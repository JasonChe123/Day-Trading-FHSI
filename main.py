# SYSTEM MODULES ----------------------------------------------------------------------------------
from collections import defaultdict
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
        self.algo_main_page.algo_trade.load_strategies()
        self.algo_main_page.algo_trade.update_table()
        self.algo_main_page.trade_journal.init_filter()
        self.algo_main_page.trade_journal.refresh()

    def on_stop(self):
        self.futu.close_all_connection()
        self.ibapi.disconnect()

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
        self.ibapi.init_connection()


def get_system_arguments():
    # get system arguments
    sys_params = dict()
    for key, value in ((key.lstrip('-'), value) for key, value, in (a.split('=') for a in sys.argv[1:])):
        sys_params[key] = value

    # update required arguments
    required_params = {
        'futu_pwd': '0',
        'ib_username': '',
        'ib_pwd': '',
        'demo': 'true',
        'strategy': '',
    }
    required_params.update(sys_params)

    # check validity
    if required_params['futu_pwd'] == 0:
        raise Exception("Please input 'futu_pwd'=******.")

    if not required_params['futu_pwd'].isnumeric():
        raise Exception("futu_pwd should be numeric.")

    if not required_params['ib_username']:
        raise Exception("Please input 'ib_username=******.")

    if not required_params['ib_pwd']:
        raise Exception("Please input 'ib_pwd=******")

    if required_params['demo'].lower() not in ['true', 'false']:
        raise Exception("Please input true/false for 'demo' parameter.")

    return required_params


if __name__ == '__main__':
    PROJECT_DIR = os.getcwd()
    sys_params = get_system_arguments()

    # set system params
    FUTU_UNLOCK_TRADE_PASSWORD = int(sys_params['futu_pwd'])
    IB_TWS_USER_NAME = sys_params['ib_username']
    IB_TWS_LOGIN_PWD = sys_params['ib_pwd']
    IS_DEMO = True if sys_params['demo'].lower() == 'true' else False
    RUNNING_STRATEGIES = sys_params['strategy'].split(',')

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

    # todo: kill futu_open_d
