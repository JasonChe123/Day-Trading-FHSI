# SYSTEM MODULES ----------------------------------------------------------------------------------
import logging
import os
import sys
import threading as th

# PROJECT MODULES ---------------------------------------------------------------------------------
from library.futu_api import FutuApi
from library.ibapi import IBApi
from library import programme
from library.logging_ import config_logging
from front_ends.algo_trade_main_page import AlgoTradeMainPage

# GUI MODULES -------------------------------------------------------------------------------------
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.carousel import Carousel
from kivy.uix.popup import Popup


class AlgoTradeForFHSI(App):
    proj_dir = ''  # for the initialization of its children

    def __init__(self):
        super().__init__()
        self.proj_dir = PROJECT_DIR  # for kv files loading images at the very beginning
        self.engine = 'live'  # live/ backtest: control behaviour like 'update_kline' and 'fire_trade'
        self.is_demo = IS_DEMO  # live/ demo: control behaviour like 'place_order' and accessing account info
        self.running_strategies = RUNNING_STRATEGIES

    # kivy's predefined methods -------------------------------------------------------------------
    def build(self):
        self.popup = Popup(title='Information', size_hint=(0.8, 0.3), auto_dismiss=True)
        self.carousel = Carousel(direction='right', scroll_timeout=0)
        self.algo_main_page = AlgoTradeMainPage()
        self.algo_main_page.create_pages()
        self.carousel.add_widget(self.algo_main_page)
        return self.carousel

    def on_start(self):
        self.connect_brokers()

    def on_stop(self):
        pass

    # strategy's callback -------------------------------------------------------------------------
    def callback(self):
        pass

    # helper methods ------------------------------------------------------------------------------
    def connect_brokers(self):
        self.futu = FutuApi()


if __name__ == '__main__':
    # os.environ['KIVY_LOG_MODE'] = 'MIXED'  # [KIVY, PYTHON, MIXED]
    PROJECT_DIR = os.getcwd()
    IS_DEMO = True
    IS_PRINT_TO_FILE = False
    RUNNING_STRATEGIES = []
    IB_TWS_USER_NAME = ''
    IB_TWS_LOGIN_PWD = ''

    # check system arguments
    arguments = sys.argv[1:]  # the first argument is file name
    for argv in arguments:
        argv = argv.lower()
        if 'demo=' in argv and argv.lstrip('demo=') == 'false':
            IS_DEMO = False
        if 'print_to_file=' in argv and argv.lower().lstrip('print_to_file=') == 'true':
            IS_PRINT_TO_FILE = True
        if 'strategy=' in argv:
            RUNNING_STRATEGIES = argv.lstrip('strategy=').upper().split(',')

    # configure logging
    config_logging(IS_DEMO, PROJECT_DIR)

    # launch futu-openD and tws
    th.Thread(target=programme.launch_futu_opend, args=[PROJECT_DIR], daemon=True).start()
    programme.launch_tws(PROJECT_DIR, IB_TWS_USER_NAME, IB_TWS_LOGIN_PWD)  # todo: should send alert if searching for too long e.g. 10mins

    # load kv files
    kv_dir = os.path.join(PROJECT_DIR, 'front_ends', 'kv_files')
    kv_files = [kv_file for kv_file in os.listdir(kv_dir) if os.path.splitext(kv_file)[1] == '.kv']
    kv_files.sort()
    [Builder.load_file(os.path.join(kv_dir, kv_file)) for kv_file in kv_files]

    # build gui
    Window.size = (450, 800)
    app = AlgoTradeForFHSI()
    app.run()
