import datetime as dt

from kivy.app import App
from kivy.uix.widget import Widget
from KivyCalendar import DatePicker


class Calendar(DatePicker):
    def __init__(self, trade_journal):
        super().__init__()
        self.update = ''  # update string: 'start' / 'end'
        self.trade_journal = trade_journal

    def update_value(self, inst):
        self.text = '%s.%s.%s' % tuple(self.cal.active_date)
        self.trade_journal.update_date(self.update)


class TradeJournal(Widget):
    id = 'trade_journal'

    def __init__(self):
        super().__init__()
        self.main_app = App.get_running_app()
        self.calendar = Calendar(self)
        self.algo = self.main_app.algo_main_page.algo_trade

        # initialize start and end date
        today = dt.date.today()
        self.start_date = self.end_date = today - dt.timedelta(days=1) if dt.datetime.now().hour < 3 else today

        # initialize labels
        self.ids['label_date_from'].text = dt.datetime.strftime(self.start_date, '%d-%b-%y')
        self.ids['label_date_to'].text = dt.datetime.strftime(self.end_date, '%d-%b-%y')

    # update gui ----------------------------------------------------------------------------------
    def init_filter(self):
        pass

    def update_date(self, start_or_end: str):
        pass

    def update_table(self, df):
        pass

    # buttons' callback ---------------------------------------------------------------------------
    def show_calendar(self, start_or_end: str):
        pass

    def refresh(self, instance=None):
        pass

    def update_filter(self, instance=None):
        pass