import datetime as dt
import os

from front_ends.algo_trade import AlgoTrade
from front_ends.trade_journal import TradeJournal
from front_ends.account_info import AccountInfo
from front_ends.position import Position

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget


os.environ['KIVY_LOG_MODE'] = 'MIXED'  # [KIVY, PYTHON, MIXED]


class AlgoTradeMainPage(Widget):
    id = 'main_page'

    def __init__(self):
        super().__init__()
        self.carousel = self.ids['content']  # get carousel from 'id' in kv file
        self.slides = self.carousel.slides  # empty

        # setup headline text
        headline_text = 'Algo Trading for HK.MHI'
        headline_text = ' '.join([letter for letter in headline_text])  # add spacing
        mode = 'D E M O' if App.get_running_app().is_demo else 'R E A L'
        lbl_headline = self.ids['headline']  # get label from 'id' in kv file
        lbl_headline.text = f'{headline_text}  (  {mode}  )'

    def create_pages(self):
        # create pages
        self.algo_trade = AlgoTrade()
        self.trade_journal = TradeJournal()
        self.account_info = AccountInfo()
        self.position = Position()

        # add pages
        for page in (self.algo_trade, self.trade_journal, self.account_info, self.position):
            self.carousel.add_widget(page)

        # run clock
        Clock.schedule_interval(lambda t: self.update_clock(), 1)

    def show_slide(self, slide):
        for page in self.slides:
            self.carousel.load_slide(page) if page.id == slide else None
            if slide == 'account_info':
                # update data
                pass
            elif slide == 'position':
                # update data
                pass

    def update_clock(self):
        # get label by 'id' in kv file
        self.ids['label_time'].text = dt.datetime.strftime(dt.datetime.now(), '%d-%b-%Y ( %a )  %H:%M:%S')
