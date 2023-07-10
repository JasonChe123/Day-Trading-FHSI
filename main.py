# SYSTEM MODULES ----------------------------------------------------------------------------------
import datetime as dt
import logging
import os
import threading as th
import yaml

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
        self.update_strategy_params()
        self.algo_main_page.trade_journal.init_filter()
        self.algo_main_page.trade_journal.refresh()

    def on_stop(self):
        self.futu.close_all_connection()
        self.ibapi.disconnect()

    # ------------------------------------------------------------------------------------------- #
    """ strategy callback """
    # ------------------------------------------------------------------------------------------- #
    def fire_trade(self, side: str, qty: int, remark: str, order_type: str):
        self.futu.fire_trade(side, qty, remark, order_type)
        self.update_gui()
        self.update_strategy_params()

    def update_strategy_params(self):

        def get_last_open_position_price_and_time(strategy):
            trade_journal = self.futu.filter_trade_journal(
                self.futu.get_trade_journal(),
                self.algo_main_page.algo_trade.start_date,
                self.algo_main_page.algo_trade.end_date
            )

            for i in trade_journal.index:
                # todo: review logic: the last trade can be a partial closing trade, not the latest open trade
                if trade_journal['remark'][i][:3] == strategy.name:
                    return trade_journal['price'][i], trade_journal['create_time'][i]

        algo_table = self.algo_main_page.algo_trade.algo_table
        if not algo_table.empty:
            for i in algo_table.index:
                strategy = self.algo_main_page.algo_trade.strategies[algo_table['Strategy'][i]]
                inventory = algo_table['Inventory'][i]
                realized_pnl = algo_table['P / L'][i]  # todo
                average_price = algo_table['AvgPrice'][i]
                traded_vol = algo_table['TradedQty'][i]
                if not inventory:
                    last_entry_price = int
                    last_entry_time = dt.datetime
                else:
                    last_entry_price, last_entry_time = get_last_open_position_price_and_time(strategy)

                strategy.update_params(inventory, realized_pnl, average_price, traded_vol, last_entry_price, last_entry_time)

    def update_gui(self):
        self.algo_main_page.algo_trade.update_table()
        self.algo_main_page.trade_journal.refresh()
        # Clock.schedule_once(lambda time_: self.algo_main_page.algo_trade.update_table(), 0)
        # Clock.schedule_once(lambda time_: self.algo_main_page.trade_journal.refresh(), 0)

    # ------------------------------------------------------------------------------------------- #
    """ helper methods """
    # ------------------------------------------------------------------------------------------- #
    def connect_brokers(self):
        self.futu = FutuApi()
        self.ibapi = IBApi()
        self.futu.connect(unlock_trade_password=FUTU_UNLOCK_TRADE_PASSWORD)
        self.ibapi.init_connection(IB_TWS_ADDRESS)
        self.ibapi.request_market_data()


def get_system_params():
    # check if file valid
    if os.path.isfile('start_up_params.yaml'):
        with open('start_up_params.yaml', 'r') as file_:
            params = yaml.safe_load(file_)

            # check if all required params is in the file
            required_params = {'futu_unlock_trade_pwd', 'ib_username', 'ib_login_pwd', 'demo', 'strategy', 'ib_tws_address'}
            if required_params.difference(params):
                raise KeyError(f"Please add {list(required_params.difference(params))} in 'start_up_params.yaml'.")

            # check value validity
            if not isinstance(params.get('futu_unlock_trade_pwd'), int):
                raise ValueError("futu_pwd should be numeric.")

            if not isinstance(params.get('demo'), bool):
                raise ValueError("demo should be 'True/False'.")
    else:
        raise FileNotFoundError("Please add 'start_up_params.yaml' in the main project directory.")

    return params


if __name__ == '__main__':
    PROJECT_DIR = os.getcwd()
    sys_params = get_system_params()

    # get system params
    FUTU_UNLOCK_TRADE_PASSWORD = int(sys_params['futu_unlock_trade_pwd'])
    IB_TWS_ADDRESS = sys_params['ib_tws_address']
    IB_TWS_USER_NAME = sys_params['ib_username']
    IB_TWS_LOGIN_PWD = sys_params['ib_login_pwd']
    IS_DEMO = sys_params['demo']
    RUNNING_STRATEGIES = sys_params['strategy']

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

    # launch app
    Window.size = (450, 800)
    app = AlgoTradeForFHSI()

    # run application
    app.run()

    # todo: kill futu_open_d
