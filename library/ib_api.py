import logging
import os

from ibapi.client import EClient
from ibapi.wrapper import EWrapper

os.environ['KIVY_LOG_MODE'] = 'MIXED'
from kivy.app import App


class IBApi(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        self.main_app = App.get_running_app()
        self.algo = self.main_app.algo_main_page.algo_trade

    def init_connection(self):
        pass
