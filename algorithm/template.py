import datetime as dt
import logging
import pandas as pd
import threading as th


class AlgoTemplate:
    version = None
    launch_date = None
    name = None

    # ------------------------------------------------------------------------------------------- #
    """ initialization """
    # ------------------------------------------------------------------------------------------- #
    def __init__(self, main_app: type, symbol: str, start: dt.time, open_order_start: dt.time,
                 open_order_end: dt.time, timeout: dt.time):
        """
        basic setting for algo trade strategy
        :param main_app: driven by apps like backtest , real-trading
        :param symbol:
        :param start:
        :param open_order_start:
        :param open_order_end:
        :param timeout:
        """
        self.main_app = main_app
        self.kline = pd.DataFrame()
        self.kline_daily = pd.DataFrame()

        # algo params
        self.max_contract = 3
        self.exec_set = 1
        self.first_entry_price = None
        self.latest_entry_time = None

        # operating params
        self.is_turn_on = True
        self.status = 'ready'  # ready/ running/ stop/ timeout/ ...
        self.symbol = symbol
        self.mode = 'normal'
        self._order_num = 1
        self._can_trade = True  # temporary for placing order
        self.can_open_order = True
        self.is_timeout = False
        self.is_stop_trade = False
        self.algo_start_time = start
        self.open_order_start_time = open_order_start
        self.open_order_end_time = open_order_end
        self.algo_timeout_time = timeout
        self.is_summer = True if 3 <= dt.datetime.now().month <= 10 else False  # define summer/ winter

        # account values
        self.inv_real = 0
        self.inv_algo = 0
        self.avg_price = 0
        self.trd_vol = 0
        self.pnl_value = 0

    def init_tp_sl(self, close):
        """initialize take profit point and stoploss point if necessary"""
        pass

    # ------------------------------------------------------------------------------------------- #
    """ operation """
    # ------------------------------------------------------------------------------------------- #
    def place_order(self, side: str, qty: int, remark: str, order_type: str = 'MARKET', index: int = 0):
        """
        final check and send the order to broker
        :param side: buy or sell order
        :param qty: execute qty
        :param remark: identification text
        :param last_bar: latest bar data
        :param order_type: LIMIT, MARKET, AUCTION
        :param index: dataframe index used for backtesting
        :return: None
        """
        if self.main_app.engine == 'backtest':
            if self.mode == 'reverse':
                side = 'SELL' if side == 'BUY' else 'BUY'
                remark += '(reverse)'
            self.main_app.fire_trade(side, qty, f'{self.name}-{remark}', order_type, index=index)
            return
        else:
            # to avoid place_order repeatedly
            if self._can_trade:
                self._can_trade = False

                if self.mode == 'reverse':
                    # flip the buy/sell order
                    side = 'SELL' if side == 'BUY' else 'BUY'
                    remark += '(reverse)'

                self.main_app.fire_trade(side, qty, f'{self.name}-{remark}', order_type)
                th.Timer(1, self._reset_can_trade).start()

    def _reset_can_trade(self):
        self._can_trade = True

    def update_status(self, status: str):
        self.status = status
        self.main_app.algo_main_page.algo_trade.update_status(self.name, status)

    # ------------------------------------------------------------------------------------------- #
    """ helper methods """
    # ------------------------------------------------------------------------------------------- #
    def _get_order_id(self):
        """
        return available identification number
        :return: string e.g. #001
        """
        order_id = '#' + str(self._order_num).zfill(3)
        self._order_num += 1
        return order_id

    def update_params(self, side: str, qty: int, price: int):
        # update self.first_entry_price
        if self.inv_algo == 0:
            self.first_entry_price = price

        # update inventory
        if side == 'BUY':
            self.inv_real += qty
        elif side == 'SELL':
            self.inv_real -= qty
        self.inv_algo = self.inv_real if self.mode == 'normal' else -self.inv_real

        # update average price
        if self.inv_algo == 0:
            self.avg_price = 0
        else:
            self.avg_price = (self.avg_price * self.inv_algo + price * qty) / (self.inv_algo + qty)

    @staticmethod
    def cross_over(value1: pd.Series, value2: pd.Series | float):
        """
        return True while value1 cross over value2
        :param value1: pd.Series
        :param value2: pd.Series/ float
        :return: bool
        """
        try:
            if value1.iloc[-2] < value2.iloc[-2] and value1.iloc[-1] > value2.iloc[-1]:
                return True
        except Exception:
            if value1.iloc[-2] < value2 < value1.iloc[-1]:
                return True

        return False

    @staticmethod
    def cross_under(value1: pd.Series, value2: pd.Series | float):
        """
        return True while value1 cross under value2
        :param value1: pd.Series
        :param value2: pd.Series/ float
        :return: bool
        """
        # assign variables
        v1_curr = value1.iloc[-1]
        v1_prev = value1.iloc[-2]
        if isinstance(value2, pd.Series):
            v2_curr = value2.iloc[-1]
            v2_prev = value2.iloc[-2]
        else:
            v2_curr = v2_prev = value2

        # crossing logic
        if v1_prev > v2_prev and v1_curr < v2_curr:
            return True
        else:
            return False

    # ------------------------------------------------------------------------------------------- #
    """ algorithm """
    # ------------------------------------------------------------------------------------------- #
    def apply_indicators(self, kline):
        """applying indicators to the kline if the engine is backtest"""
        pass

    def apply_daily_indicators(self):
        pass

    def update_kline(self, kline: pd.DataFrame, index: int = 0):
        """
        in live trading: the latest kline would be used, get last index from kline
        in backtesting: the whole kline data and index are received and would study the specific index in the kline
        """
        # for backtest engine
        if self.main_app.engine == 'backtest':
            self.backtest_in_out_logic(kline, index)
            return

        # for live engine (demo/ real), check on/off algo
        if self.main_app.engine == 'live':
            if not self.is_turn_on:
                logging.debug(f"{self.name} is turned off")
                return
            else:
                logging.debug(f"{self.name} is turned on")
                self.kline = kline

        # if stop_trade (by any reason), do nothing
        if self.is_stop_trade:
            logging.debug(f"strategy {self.name} stop")
            return
        # if timeout, close all positions
        elif self.check_is_timeout(kline):
            logging.debug(f"strategy {self.name} timeout")
            if self.inv_algo > 0:
                side = 'SELL'
                remark = 'LX TIMEOUT'
            else:
                side = 'BUY'
                remark = 'SX TIMEOUT'
            self.place_order(side=side, qty=self.inv_algo, remark=remark, index=index)
            return
        else:
            # run indicators
            self.update_indicator(kline)

            # check exit logic first
            if self.inv_algo:
                self.check_exit_conditions(kline)

            # check entry logic if self.can_open_order
            if self._check_can_open_order(kline):
                self.check_entry_conditions(kline)

    def backtest_in_out_logic(self, kline: pd.DataFrame, index: int):
        if self.inv_algo == 0:
            # todo: check can_open_order
            self.check_entry_conditions(kline=kline, index=index)
        else:
            self.check_is_timeout(kline, index)
            self.check_exit_conditions(kline, index=index)
            self.check_add_order_conditions(kline, index=index)
        # else:
        #     self.check_entry_conditions(kline, index=index)

    def check_is_timeout(self, kline: pd.DataFrame, index: int = 0):
        """return True if algo timeout"""
        def set_timeout(flag: bool):
            self.is_timeout = True if flag else False
            return flag

        if self.main_app.engine == 'live':
            index = self.kline.index[-1]  # get index

        time_key = self.kline['time_key'].iloc[index]
        if self.algo_timeout_time.hour > 3:
            if self.algo_timeout_time <= time_key.time() or time_key.hour <= 3:
                return set_timeout(True)

        elif self.algo_timeout_time <= time_key.time() and time_key.hour <= 3:
            return set_timeout(True)

        elif time_key.hour == 12 and time_key.minute == 28:
            return set_timeout(True)

        time_str = dt.datetime.strftime(time_key, '%Y-%m-%d %H:%M:%S')

        # special timeout
        if time_str in ('2022-11-02 13:54:00', '2023-04-12 16:14:00'):
            return set_timeout(True)

        return set_timeout(False)

    def _check_can_open_order(self, kline: pd.DataFrame):
        """`
        check for open order time
        return True if time_key within open order period
        """
        def set_can_open_order(flag: bool):
            self.can_open_order = flag
            status = 'timeout' if not flag and not self.inv_algo else 'running'
            self.update_status(status)

            return flag

        time_key = kline['time_key'].iloc[-1].time()
        if self.open_order_end_time.hour > 3:
            if self.open_order_start_time < time_key < self.open_order_end_time:
                return set_can_open_order(True)
            else:
                return set_can_open_order(False)
        else:
            if self.open_order_start_time < time_key or time_key < self.open_order_end_time:
                return set_can_open_order(True)
            else:
                return set_can_open_order(False)

    def update_indicator(self, kline: pd.DataFrame):
        pass

    def check_entry_conditions(self, kline: pd.DataFrame, index: int=0):
        pass

    def check_add_order_conditions(self, kline: pd.DataFrame, index: int=0):
        pass

    def check_exit_conditions(self, kline: pd.DataFrame, index: int=0):
        pass

    def check_intrabar_tp(self, kline: pd.DataFrame):
        """return True if price reaches take-profit price"""
        pass

    def check_intrabar_sl(self, kline: pd.DataFrame):
        """return True if price reaches stoploss price"""
        pass

    def _timeout_cover_position(self, last_bar: pd.Series):
        """close all position no matter what the algo status is"""
        if self.inv_algo:
            side = 'SELL' if self.inv_algo > 0 else 'BUY'
            self.place_order(side=side, qty=self.inv_algo, remark='LX TOUT', last_bar=last_bar)
