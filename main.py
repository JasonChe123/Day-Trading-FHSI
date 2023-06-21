# SYSTEM MODULES ----------------------------------------------------------------------------------
import logging
import os
import sys
import threading as th

# PROJECT MODULES ---------------------------------------------------------------------------------
from library.futu_api import FutuApi
from library.ib_api import IBApi
from library import programme
from library.logging_ import config_logging
from front_ends.algo_trade_main_page import AlgoTradeMainPage

# GUI MODULES -------------------------------------------------------------------------------------
from kivy.app import App
from kivy.clock import Clock
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

    # ------------------------------------------------------------------------------------------- #
    """ kivy's pre-defined methods """
    # ------------------------------------------------------------------------------------------- #
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
        self.futu.close_all_connection()

    # ------------------------------------------------------------------------------------------- #
    """ strategy callback """
    # ------------------------------------------------------------------------------------------- #
    def callback(self):
        pass

    # ------------------------------------------------------------------------------------------- #
    """ helper methods """
    # ------------------------------------------------------------------------------------------- #
    def connect_brokers(self):
        self.futu = FutuApi()
        self.ibapi = IBApi()
        self.futu.connect(unlock_trade_password=FUTU_UNLOCK_TRADE_PASSWORD)
        Clock.schedule_once(self.ibapi.init_connection, 60)


if __name__ == '__main__':
    # os.environ['KIVY_LOG_MODE'] = 'MIXED'  # [KIVY, PYTHON, MIXED]
    PROJECT_DIR = os.getcwd()
    IS_DEMO = True
    IS_PRINT_TO_FILE = False
    RUNNING_STRATEGIES = []
    FUTU_UNLOCK_TRADE_PASSWORD = 0
    IB_TWS_USER_NAME = ''
    IB_TWS_LOGIN_PWD = ''

    # check system arguments
    arguments = sys.argv[1:]  # the first argument is file name
    for argv in arguments:
        argv = argv.lower()
        if 'futu_pwd=' in argv:
            FUTU_UNLOCK_TRADE_PASSWORD = argv.lstrip('futu_pwd=')
            if not FUTU_UNLOCK_TRADE_PASSWORD.isnumeric():
                print("Futu unlock trade password should be a number")
                sys.exit()
            FUTU_UNLOCK_TRADE_PASSWORD = int(FUTU_UNLOCK_TRADE_PASSWORD)

        if 'ib_user_name=' in argv:
            IB_TWS_USER_NAME = argv.lstrip('ib_user_name=')

        if 'ib_pwd=' in argv:
            IB_TWS_LOGIN_PWD = argv.lstrip('ib_pwd=')

        if 'demo=' in argv and argv.lstrip('demo=') == 'false':
            IS_DEMO = False

        if 'strategy=' in argv:
            RUNNING_STRATEGIES = argv.lstrip('strategy=').upper().split(',')

    # check login input
    if FUTU_UNLOCK_TRADE_PASSWORD == 0:
        print("Please input Futu Unlock Trade Password so as to function properly.")
        print("\tfutu_pwd=123456")
        sys.exit()
    if IB_TWS_USER_NAME == '' or IB_TWS_LOGIN_PWD == '':
        print("Please input TWS login name and password so as to function properly.")
        print("\tib_user_name=abcdefg")
        print("\tib_pwd=abcdefg")
        sys.exit()

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
