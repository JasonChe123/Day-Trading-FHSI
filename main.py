# SYSTEM MODULES ----------------------------------------------------------------------------------
import logging
from pathlib import Path
import re
import os
import sys
import threading as th

# PROJECT MODULES ---------------------------------------------------------------------------------
# from library.futu_api import FutuApi
# from library.ibapi import IBApi
# from library.printing import LogPrint
from library import programme
from front_ends.algo_trade_main_page import AlgoTradeMainPage

# GUI MODULES -------------------------------------------------------------------------------------
os.environ['KIVY_LOG_MODE'] = 'MIXED'  # separate logging between python and kivy
import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.carousel import Carousel
from kivy.uix.label import Label
from kivy.uix.popup import Popup


class CustomFormatter(logging.Formatter):

    grey = "\x1b[37m"
    yellow = "\x1b[33m"
    white = "\x1b[m"
    red = "\x1b[31m"
    black_yellow_bg = "\x1b[30;43m"
    black_red_bg = "\x1b[30;41m"
    formatter = lambda colour: f'%(asctime)s <%(name)s> {colour} [ %(levelname)-8s ] %(message)s \x1b[0m ("%(filename)s:%(lineno)s)"'

    FORMATS = {
        logging.DEBUG: formatter(grey),
        logging.INFO: formatter(white),
        logging.WARNING: formatter(red),
        logging.ERROR: formatter(black_yellow_bg),
        logging.CRITICAL: formatter(black_red_bg),
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


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
        pass

    def on_stop(self):
        pass

    # strategy's callback -------------------------------------------------------------------------
    def callback(self):
        pass

    # helper methods ------------------------------------------------------------------------------
    def helper(self):
        pass


def config_logging():
    # set kivy loglevel
    Logger.setLevel(logging.WARNING)

    # set system loglevel
    mylogger = logging.getLogger('root')
    mylogger.setLevel(logging.DEBUG)  # todo: turn it to INFO while finish testing

    # define log file path
    file_name = 'demo.log' if IS_DEMO else 'live.log'
    file_path = os.path.join(PROJECT_DIR, 'database', 'log', file_name)

    # set handlers
    file_handler = logging.FileHandler(file_path, encoding='utf-8')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)  # todo: should be set to INFO, DEBUG is just for developing stage

    # set formatter
    file_formatter = logging.Formatter(
        '%(asctime)s <%(name)s> [ %(levelname)-8s ] %(message)s "(%(filename)s:%(lineno)s)"',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    stream_handler.setFormatter(CustomFormatter())
    file_handler.setFormatter(file_formatter)

    # add handler
    mylogger.addHandler(file_handler)
    mylogger.addHandler(stream_handler)


if __name__ == '__main__':
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
    config_logging()

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
