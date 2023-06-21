import logging
import os
import random
import socket
import threading as th

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
        self.client_id = random.choice(range(1000, 9999, 1))

    def init_connection(self):
        server_address = '192.168.1.101' if socket.gethostbyname(socket.gethostname()) != '192.168.1.101' else '127.0.0.1'
        self.connect(server_address, 7497, self.client_id)
        th.Thread(target=self.run, args=[]).start()
