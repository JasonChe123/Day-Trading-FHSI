import logging
import os
import random
import socket
import threading as th

from library.contract_info import get_contract_year_and_month

from ibapi.client import EClient
from ibapi.wrapper import EWrapper, BarData, TickerId, TickType, TickAttrib
from ibapi.contract import Contract

os.environ['KIVY_LOG_MODE'] = 'MIXED'
from kivy.app import App


class IBApi(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        self.main_app = App.get_running_app()
        self.algo = self.main_app.algo_main_page.algo_trade
        self.client_id = random.choice(range(1000, 9999, 1))
        self.request_id = {'FHSI_1M': 10000,
                           'FHSI_1D': 100001}
        self.lock = th.Lock()

        # setup contract
        self.contract = Contract()
        contract_year, contract_month = get_contract_year_and_month()
        month_key = {
            1: 'F',
            2: 'G',
            3: 'H',
            4: 'J',
            5: 'K',
            6: 'M',
            7: 'N',
            8: 'Q',
            9: 'U',
            10: 'V',
            11: 'X',
            12: 'Z'
        }
        self.contract.secType = 'FUT'
        self.contract.exchange = 'HKFE'
        self.contract.currency = 'HKD'
        self.contract.localSymbol = ''.join(['HSI', month_key[int(contract_month)], contract_year[-1]])  # e.g. HSIH3: FHSI April 2023

    def init_connection(self):
        server_address = '192.168.1.101' if socket.gethostbyname(socket.gethostname()) != '192.168.1.101' else '127.0.0.1'
        self.connect(server_address, 7497, self.client_id)
        th.Thread(target=self.run, args=[]).start()

    def request_market_data(self):
        def request_kline(request_id: int, duration: str, bar_size: str):
            self.reqHistoricalData(reqId=request_id,
                                   contract=self.contract,
                                   endDateTime='',
                                   durationStr=duration,
                                   barSizeSetting=bar_size,
                                   whatToShow='TRADES',
                                   useRTH=False,
                                   formatDate=True,
                                   keepUpToDate=True,
                                   chartOptions=[]
                                   )

        # todo: to be applied later
        # request_kline(request_id=self.request_id.get('FHSI_1M'), duration='3 D', bar_size='1 min')
        # request_kline(request_id=self.request_id.get('FHSI_1D'), duration='5 D', bar_size='1 day')

        # request tick price
        self.reqMktData(reqId=self.request_id.get('FHSI_1M'), contract=self.contract, genericTickList='',
                        snapshot=False, regulatorySnapshot=False, mktDataOptions=[])

    # ------------------------------------------------------------------------------------------- #
    """ system callbacks """
    # ------------------------------------------------------------------------------------------- #
    def historicalData(self, reqId: int, bar: BarData):
        logging.critical('historicalData')

    def historicalDataUpdate(self, reqId: int, bar: BarData):
        if reqId == self.request_id.get('FHSI_1M'):
            self.update_kline(bar)

    def tickPrice(self, reqId: TickerId , tickType: TickType, price: float, attrib: TickAttrib):
        if reqId == self.request_id.get('FHSI_1M') and tickType == 4:  # last price at which the contract traded
            self.algo.update_realtime_pnl(price)

    # ------------------------------------------------------------------------------------------- #
    """ algo methods """
    # ------------------------------------------------------------------------------------------- #
    def update_kline(self, bar: BarData):
        with self.lock:
            pass
