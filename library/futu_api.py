import os
os.environ['KIVY_LOG_MODE'] = 'MIXED'  # ['KIVY', 'PYTHON', 'MIXED']

import pandas as pd
import threading as th
import uuid

from kivy.app import App


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

