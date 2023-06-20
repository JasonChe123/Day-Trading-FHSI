import datetime as dt
import pandas as pd
from kivy.app import App
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from KivyCalendar import DatePicker


class Calendar(DatePicker):
    def __init__(self, algo_trade):
        super().__init__()
        self.update = ''
        self.algo_trade = algo_trade

    def update_value(self, inst):
        self.text = '%s.%s.%s' % tuple(self.cal.active_date)
        self.algo_trade.update_date(self.update)


class OrderSpinner(Spinner):
    """
    drop down menu for order selection (buy/ sell/ cover)
    """
    pass


class AlgoTrade(Widget):
    id = 'algo_trade'

    def __init__(self):
        super().__init__()
        self.color_map = {
            'green': (0.3, 1.0, 0.3, 1.0),
            'red': (1.0, 0.2, 0.2, 1.0)
        }
        self.auto_shutdown = self.ids['checkbox_auto_shutdown'].active  # get checkbox by 'id' in kv file
        self.strategies = {}
        self.calendar = Calendar(self)

        # initialize algo trade table
        running_strategies = App.get_running_app().running_strategies
        empty_list = ['' for i in range(len(running_strategies))]
        order_list = ['PlsSelect' for i in range(len(running_strategies))]
        self.table = pd.DataFrame(
            {'Status': empty_list,
             'Strategy': running_strategies,
             'ExecSet': empty_list,
             'Inventory': empty_list,
             'P / L': empty_list,
             'MaxCtrt': empty_list,
             'AvgPrice': empty_list,
             'TradeQty': empty_list,
             'Fees': empty_list,
             'Order': order_list,
             'InitMargin': empty_list,
             }
        )

        # initialize start and end date
        now = dt.datetime.now()
        if now.hour < 3:
            now = now - dt.timedelta(days=1)
        # now -= dt.timedelta(days=1) if now.hour < 3 else now
        print(now, type(now))
        self.today = dt.datetime.date(now)
        self.start_date = self.today
        self.end_date = self.today
        self.ids['label_date_from'].text = dt.datetime.strftime(self.start_date, '%d-%b-%y')
        self.ids['label_date_to'].text = dt.datetime.strftime(self.end_date, '%d-%b-%y')

        # update datatable
        self.update_table(self.table.copy())

    # update gui ----------------------------------------------------------------------------------
    def show_calendar(self, start_or_end: str):
        self.calendar.show_popup(1, 0.5)
        self.calendar.update = start_or_end

    def update_date(self, start_or_end: str):
        if start_or_end == 'start':
            self.start_date = dt.datetime.strptime(self.calendar.text, '%d.%m.%Y')
            self.ids['label_date_from'].text = dt.datetime.strftime(self.start_date, '%d-%b-%y')
        else:
            self.end_date = dt.datetime.strptime(self.calendar.text, '%d.%m.%Y')
            self.ids['label_date_to'].text = dt.datetime.strftime(self.end_date, '%d-%b-%y')

    def update_table(self, df):
        pass
