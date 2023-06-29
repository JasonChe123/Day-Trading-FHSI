import logging
import os
import datetime as dt
import pandas as pd
import threading as th
import uuid

from library.contract_info import get_contract_year_and_month
from library.programme import is_running

import futu as ft

os.environ['KIVY_LOG_MODE'] = 'MIXED'
from kivy.app import App
from kivy.clock import Clock


class SysNotificationHandler(ft.SysNotifyHandlerBase):
    def on_recv_rsp(self, rsp_str):
        ret_code, data = super(SysNotificationHandler, self).on_recv_rsp(rsp_str)


class TradeOrderHandler(ft.TradeOrderHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, ret_data = super(TradeOrderHandler, self).on_recv_rsp(rsp_pb)


class TradeDealHandler(ft.TradeDealHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, ret_data = super(TradeDealHandler, self).on_recv_rsp(rsp_pb)


class FutuApi:
    def __init__(self):
        self.main_app = App.get_running_app()
        self.algo_main_page = self.main_app.algo_main_page
        self.algo = self.algo_main_page.algo_trade
        self.project_directory = self.main_app.proj_dir
        mode = 'demo' if self.main_app.is_demo else 'real'
        self.trade_journal_file_path = os.path.join(
            self.project_directory, 'database', 'trade_journal', f'trade_journal_{mode}.csv'
        )
        self.order_journal = pd.DataFrame()  # used for 'trade history' page, assign 'remark' to trade_journal
        self.demo_order_id = ''
        self.qot_ctx = None
        self.trd_ctx = None
        self.contract_detail = {}  # to be set later
        self.timer = th.Timer(0, lambda: 0)

    # ------------------------------------------------------------------------------------------- #
    """ broker connection """
    # ------------------------------------------------------------------------------------------- #
    def connect(self, unlock_trade_password: int) -> bool:
        if is_running('FutuOpenD.exe'):
            # connect futu-api
            if not self.qot_ctx or not self.trd_ctx:
                self.qot_ctx = ft.OpenQuoteContext()
                self.trd_ctx = ft.OpenFutureTradeContext()
            if self.qot_ctx.status == self.trd_ctx.status == 'READY':
                logging.debug("Quote context and trade context are ready.")
                self.init_params(unlock_trade_password)
            else:
                self.timer = th.Timer(10.0, lambda: self.connect(unlock_trade_password))
                self.timer.start()
        else:
            self.timer = th.Timer(10.0, lambda: self.connect(unlock_trade_password))
            self.timer.start()

    def close_all_connection(self):
        self.timer.cancel()
        if self.qot_ctx is not None and self.trd_ctx is not None:
            self.qot_ctx.close()
            self.trd_ctx.close()

    def init_params(self, unlock_trade_password):
        result = self.set_contract_info()
        if not result:  # sometime "此数据暂时还未准备好"
            self.timer = th.Timer(10.0, self.init_params)
            self.timer.start()
            return

        # subscribe orderbook data, used for demo trade
        ret_code, err_msg = self.qot_ctx.subscribe(self.contract_detail.get('full_code'),
                                                   ft.SubType.ORDER_BOOK,
                                                   is_first_push=False,
                                                   subscribe_push=False)
        if ret_code != ft.RET_OK:
            logging.error(err_msg)

        # unlock trade
        ret_code, ret_data = self.trd_ctx.unlock_trade(password=unlock_trade_password)
        if ret_code != ft.RET_OK:
            logging.error(ret_data)

        # set handlers
        notification_handler = SysNotificationHandler()
        trade_order_handler = TradeOrderHandler()
        trade_deal_handler = TradeDealHandler()
        self.qot_ctx.set_handler(notification_handler)
        self.trd_ctx.set_handler(trade_order_handler)
        self.trd_ctx.set_handler(trade_deal_handler)

    def set_contract_info(self) -> bool:
        year, month = get_contract_year_and_month()

        # get margin requirement
        ret_code, ret_data = self.trd_ctx.acctradinginfo_query('MARKET', 'HK.MHImain', 0)
        if ret_code != ft.RET_OK:
            logging.warning(ret_data)
            return False
        margin = round(ret_data['long_required_im'][0], -3) + 1000

        # set contract detail
        self.contract_detail = {
            'full_code': ''.join(['HK.MHI', year, month]),
            'pt_val': 10,
            'margin': margin
        }
        return True

    # ------------------------------------------------------------------------------------------- #
    """ database operation """
    # ------------------------------------------------------------------------------------------- #
    def get_trade_journal(self) -> pd.DataFrame:
        if self.main_app.is_demo:
            if os.path.isfile(self.trade_journal_file_path):
                logging.debug(f"read {self.trade_journal_file_path}")
                return pd.read_csv(self.trade_journal_file_path)
            else:
                return pd.DataFrame()
        else:
            pass

    def refresh_trade_journal(self, start_date: dt.date, end_date: dt.date, trade_journal: pd.DataFrame = pd.DataFrame()):
        """
        Callback from trade_journal 'refresh' button
        """
        if trade_journal.empty:
            trade_journal = self.filter_trade_journal(self.get_trade_journal(), start_date, end_date)

        return trade_journal

    # ------------------------------------------------------------------------------------------- #
    """ algo related """
    # ------------------------------------------------------------------------------------------- #
    def get_algo_table(self, strategies_name: list, start_date: dt.date, end_date: dt.date):
        """
        callback from algo_trade: to return a ready shown table for algo_trade
        """
        # initialize algo_table dataframe
        algo_table_cols = ['Status', 'Strategy', 'ExecSet', 'Inventory', 'P / L', 'MaxCtrt', 'AvgPrice',
                           'TradedQty', 'Fees', 'Order', 'InitMargin']
        algo_table = pd.DataFrame(columns=algo_table_cols)

        # get trade journal
        trade_journal = self.filter_trade_journal(self.get_trade_journal(), start_date, end_date)

        # return dataframe with no trading record
        if trade_journal.empty:
            for k in strategies_name:
                new_index = len(algo_table)
                algo_table.loc[new_index] = pd.Series()
                algo_table.fillna(0, inplace=True)
                algo_table.at[new_index, 'Strategy'] = k

            return algo_table

        # separate data by strategy name
        datas = {}
        for i in strategies_name:
            datas[i] = trade_journal[(trade_journal['remark'].str[:3] == i)]

        # calculate trading values
        for strategy_name, trade_data in datas.items():
            new_index = len(algo_table)
            algo_table.loc[new_index] = pd.Series()
            algo_table.fillna(0, inplace=True)
            position, avg_price, trade_vol, fees, pnl_value = self.calculate_trading_data(trade_data)
            algo_table.at[new_index, 'Strategy'] = strategy_name
            algo_table.at[new_index, 'Inventory'] = position
            algo_table.at[new_index, 'AvgPrice'] = avg_price
            algo_table.at[new_index, 'TradedQty'] = trade_vol
            algo_table.at[new_index, 'Fees'] = fees
            algo_table.at[new_index, 'P / L'] = pnl_value

        return algo_table

    def calculate_trading_data(self, trade_journal: pd.DataFrame):
        position = buy_avg_price = sell_avg_price = avg_price = trade_vol = pnl_price = 0
        symbol = 'MHI'
        for i, row in trade_journal[::-1].iterrows():
            side, price, qty = row['trd_side'], row['price'], row['qty']

            # calculate buy/sell average price
            if 'BUY' in side:
                position += qty
                buy_avg_price += price * qty
            elif 'SELL' in side:
                position -= qty
                sell_avg_price += price * qty
            trade_vol += qty

            # calculate average price
            if position == 0:
                pnl_price += sell_avg_price - buy_avg_price
                buy_avg_price = sell_avg_price = 0
            else:
                avg_price = buy_avg_price - sell_avg_price

        # calculate fees, average_price and pnl
        point_value = 10
        fees = self.fees_count(symbol, trade_vol)
        avg_price = avg_price / position if position else 0
        pnl_value = pnl_price * point_value - fees

        return int(position), abs(int(avg_price)), trade_vol, int(fees), int(pnl_value)

    # ------------------------------------------------------------------------------------------- #
    """ update gui """
    # ------------------------------------------------------------------------------------------- #
    def init_gui(self, start_date: dt.date, end_date: dt.date):
        pass

    def refresh_algo_trade(self, trade_journal):
        pass

    # ------------------------------------------------------------------------------------------- #
    """ helper methods """
    # ------------------------------------------------------------------------------------------- #
    def filter_trade_journal(self, df: pd.DataFrame, start_date: dt.date, end_date: dt.date) -> pd.DataFrame:
        """
        to filter the date between start_date and end_date
        """
        start = dt.datetime.strftime(start_date, '%Y-%m-%d') + ' 09:16:00'
        end = end_date + dt.timedelta(days=1)
        end = dt.datetime.strftime(end, '%Y-%m-%d') + ' 03:00:00'
        return df[(df['create_time'] >= start) & (df['create_time'] <= end)].reset_index(drop=True)

    def cal_algo_data(self, trade_journal: pd.DataFrame, strategy_name: str) -> (int, int, int, int, int):
        pass

    def fees_count(self, symbol: str, trd_vol: int):
        comm = plt_fees = exch_fees = sfc_fees = 0
        if symbol == 'HSI':
            comm = 8
            plt_fees = 5
            exch_fees = 10
            sfc_fees = 0.54
        elif symbol == 'MHI':
            comm = 2
            plt_fees = 5
            exch_fees = 3.5
            sfc_fees = 0.1

        return (comm + plt_fees + exch_fees + sfc_fees) * trd_vol
