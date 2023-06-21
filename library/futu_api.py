import logging
import os
os.environ['KIVY_LOG_MODE'] = 'MIXED'  # ['KIVY', 'PYTHON', 'MIXED']

import datetime as dt
import pandas as pd
import threading as th
import uuid

from kivy.app import App
from kivy.clock import Clock


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

        # initialize gui: algo_trade, history (for today)
        start_date = end_date = dt.date.today() - dt.timedelta(days=1) if dt.datetime.now().hour < 3 else dt.date.today()
        Clock.schedule_once(lambda t: self.init_gui(start_date, end_date), 1)

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
        trade_journal = self.get_trade_journal()
        if trade_journal.empty:
            return

        trade_jounal = self.filter_trade_journal(trade_journal, start_date, end_date)
        algo_table = self.get_algo_table(trade_journal)

    def refresh_algo_trade(self, trade_journal):
        algo_table = self.get_algo_table(trade_journal)

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
        cols = ['Status', 'Strategy', 'ExecSet', 'Inventory', 'P / L', 'MaxCtrt', 'AvgPrice', 'TradedQty',
                'Fees', 'Order', 'InitMargin']
        logging.info(self.algo.strategies)
        for i, strategy_name in enumerate(self.algo.strategies.keys()):
            logging.info(strategy_name)
            position, average_price, traded_qty, fees, pnl_value = self.cal_algo_data(trade_journal, strategy_name)

    def cal_algo_data(self, trade_journal: pd.DataFrame, strategy_name: str) -> (int, int, int, int, int):
        pass
