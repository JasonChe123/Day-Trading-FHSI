import datetime as dt
import logging

import pandas as pd
from algorithm.template import AlgoTemplate
from library import ta


class MAL(AlgoTemplate):
    version = 0.0
    launch_date = '2021-07-01'
    name = 'MAL'

    def __init__(self, main_app, symbol):
        super().__init__(main_app=main_app,
                         symbol=symbol,
                         start=dt.time(9, 15),
                         open_order_start=dt.time(14, 00),
                         open_order_end=dt.time(16, 30),
                         # open_order_end=dt.time(23, 59),
                         timeout=dt.time(2, 58),
                         )
        self.max_contract = 1
        self.exec_set = 1
        self.tp = 90
        self.sl = 120
        self.ema_fast_len = 40
        self.ema_slow_len = 90
        self.adx_low = 20

        # initialize indicator
        self.adx = pd.Series()
        self.bb_top = pd.Series()
        self.bb_mid = pd.Series()
        self.bb_bot = pd.Series()
        self.ema_fast = pd.Series()
        self.ema_slow = pd.Series()
        self.ema_filter_slow = pd.Series()
        self.ema_filter_fast = pd.Series()
        self.ema_fast_daily = pd.Series()
        self.ema_slow_daily = pd.Series()

    def apply_indicators(self, kline):
        """only apply once"""
        self.kline = kline.copy()
        self.adx = ta.adx(kline, 14)
        self.ema_fast = ta.ema(kline, self.ema_fast_len)
        self.ema_slow = ta.ema(kline, self.ema_slow_len)
        self.ema_filter_slow = ta.ema(kline, 60 * 16 * 20)  # 60 minutes * 16 hours * 20 days
        self.ema_filter_fast = ta.ema(kline, 60 * 16 * 10)

        self.apply_daily_indicators()

    # daily ta
    def apply_daily_indicators(self):
        self.ema_fast_daily = pd.DataFrame(ta.ema(self.kline_daily, 10))
        self.ema_slow_daily = pd.DataFrame(ta.ema(self.kline_daily, 20))
        self.ema_fast_daily.set_index(self.kline_daily['time_key'], inplace=True)
        self.ema_slow_daily.set_index(self.kline_daily['time_key'], inplace=True)
        self.ema_fast_daily.index.names = ['index']

    def update_indicator(self, kline: pd.DataFrame):
        if self.main_app.engine == 'live':
            self.adx = ta.adx(kline, 14)
            self.ema_fast = ta.ema(kline, self.ema_fast_len)
            self.ema_slow = ta.ema(kline, self.ema_slow_len)

            # todo: not practical, not enough bars to process, only works in backtest
            self.ema_filter_slow = ta.ema(kline, 60 * 16 * 20)  # 60 minutes * 16 hours * 20 days
            self.ema_filter_fast = ta.ema(kline, 60 * 16 * 10)

    def check_entry_conditions(self, kline: pd.DataFrame, index: int = 0):
        """
        this method should be called if self.inv_algo == 0
        :param kline: dataframe included cols: time_key, open, high, low, close, volume
        :param index: index feed from backtest engine, to extract data from specific index
        :return: True if placed order, else False
        """
        if self.main_app.engine == 'live':
            index = kline.index[-1]

        # check open order time
        time_ = self.kline['time_key'].iloc[index].time()
        if time_ < self.open_order_start_time or time_ > self.open_order_end_time:
            return

        # check  filters
        yesterday = self.kline['time_key'][index] - dt.timedelta(days=1)
        yesterday = dt.datetime.strftime(yesterday, '%Y%m%d')
        return
        # if self.ema_filter_fast[index] < self.kline['close'][index] < self.ema_filter_slow[index]:
        #     return

        # condition 1 - check volume
        if self.kline['volume'].iloc[index] < 30:
            logging.debug(f"{self.name} check entry: volume failed", log_level='live')
            return

        # condition 2 - close cross over ema_fast and ema_fast > ema_slow
        if not (self.ema_fast[index] > self.ema_slow[index] and
                self.cross_over(self.kline['close'].iloc[index - 1: index + 1],
                                self.ema_slow[index - 1: index + 1])):
            logging.debug(f"{self.name} check entry: EMAs cross over failed", log_level='live')
            return

        # condition 3 - adx < adx_low for 5 bars in a row
        consec_bars = 3
        for adx in self.adx[index - consec_bars - 1: index + 1]:
            if adx > self.adx_low:
                logging.debug(f"{self.name} check entry: low adx failed", log_level='live')
                return

        # success
        logging.debug(f"{self.name} entry conditions matched", log_level='live', fg='red')
        self.place_order(side='BUY', qty=self.exec_set, remark='LE', index=index)
        return True

    def check_exit_conditions(self, kline: pd.DataFrame, index: int = 0):
        """
        this method should be called if self.inv_algo != 0
        :param kline: kline dataframe
        :param index: only used for backtesting
        :return:
        """
        # check timeout time
        if self.is_timeout:
            side = 'SELL' if self.inv_algo > 0 else 'BUY'
            remark = 'LX TOUT' if self.inv_algo > 0 else 'SX TOUT'
            self.place_order(side=side, qty=self.inv_algo, remark=remark, index=index)
            return True

        # assign variables
        close = self.kline['close'].iloc[index]
        if self.main_app.engine == 'live':
            index = kline.index[-1]

        # check stoploss: last close < sl_point
        cond1 = self.kline['close'][index-1] < self.first_entry_price - self.sl
        if cond1:
            self.place_order(side='SELL', qty=self.inv_algo, remark='LX SL', index=index)
            return True

        # take profit: ema_fast cross under ema_slow
        if self.cross_under(self.ema_fast.iloc[index - 1: index + 1],
                            self.ema_slow.iloc[index - 1: index + 1]):
            if close > self.first_entry_price + self.tp:
                self.place_order(side='SELL', qty=self.inv_algo, remark='LX TP', index=index)
                return True
