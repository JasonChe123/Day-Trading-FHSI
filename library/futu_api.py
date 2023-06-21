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
                self.timer = th.Timer(10.0, self.connect)
                self.timer.start()
        else:
            self.timer = th.Timer(10.0, self.connect)
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
        start = dt.datetime.strftime(start_date, '%Y-%m-%d') + ' 09:16:00'
        end = end_date + dt.timedelta(days=1)
        end = dt.datetime.strftime(end, '%Y-%m-%d') + ' 03:00:00'
        return df[(df['create_time'] >= start) & (df['create_time'] <= end)].reset_index(drop=True)

    def get_algo_table(self, trade_journal: pd.DataFrame) -> pd.DataFrame:
        """
        convert trade journal to algo table
        """
        pass
        # cols = ['Status', 'Strategy', 'ExecSet', 'Inventory', 'P / L', 'MaxCtrt', 'AvgPrice', 'TradedQty',
        #         'Fees', 'Order', 'InitMargin']
        # logging.error(self.algo.strategies)
        # for i, strategy_name in enumerate(self.algo.strategies.keys()):
        #     logging.info(strategy_name)
        #     position, average_price, traded_qty, fees, pnl_value = self.cal_algo_data(trade_journal, strategy_name)

    def cal_algo_data(self, trade_journal: pd.DataFrame, strategy_name: str) -> (int, int, int, int, int):
        pass
