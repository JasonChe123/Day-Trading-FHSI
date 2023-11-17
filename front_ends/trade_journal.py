import datetime as dt
import os
import threading as th

import pandas as pd

os.environ['KIVY_LOG_MODE'] = 'MIXED'
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
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

    # ------------------------------------------------------------------------------------------- #
    """ update gui """
    # ------------------------------------------------------------------------------------------- #
    def init_filter(self):
        self.ids['filter'].values = ['ALL'] + list(self.algo.strategies.keys())

    def update_date(self, start_or_end: str):
        """
        update labels of date
        """
        if start_or_end == 'start':
            self.start_date = dt.datetime.strptime(self.calendar.text, '%d.%m.%Y')
            self.ids.label_date_from.text = dt.datetime.strftime(self.start_date, '%d-%b-%y')
        else:
            self.end_date = dt.datetime.strptime(self.calendar.text, '%d.%m.%Y')
            self.ids.label_date_to.text = dt.datetime.strftime(self.end_date, '%d-%b-%y')

    def update_table(self, trade_journal: pd.DataFrame):
        self.ids['data_table'].clear_widgets()
        if trade_journal.empty:
            return

        # filter strategy
        strategy = self.ids['filter'].text
        if strategy != 'ALL':
            trade_journal = trade_journal[
                (trade_journal['remark'].str[:3] == strategy)
            ].reset_index(drop=True)
        if trade_journal.empty:
            return

        # set number of column in data_table
        self.ids['data_table'].cols = len(trade_journal.columns)

        row_height = 30
        col_width_dict = {'create_time': 100,
                          'code': 100,
                          'remark': 250,
                          'others': 80}
        col_index = {}
        for i, col in enumerate(list(trade_journal.columns)):
            col_index[i] = col

        # add header
        for header in trade_journal.columns:
            # set column width
            col_width = col_width_dict['others'] if not col_width_dict.get(header) else col_width_dict[header]

            # add widget
            self.ids['data_table'].add_widget(
                Button(text=header, size=(col_width, row_height), size_hint=(None, None),
                       background_normal='', background_down='', background_color=(0.7, 0.7, 0.7, 1))
            )

        # add rows
        date = ''
        for index, row in trade_journal.iterrows():
            # add row data
            for i, value in enumerate(row):
                # set column width
                col = col_index.get(i)
                col_width = col_width_dict[col] if col_width_dict.get(col) else col_width_dict['others']

                # set color
                bg = (0, 0, 0, 0)
                if col == 'trd_side':
                    bg = (0.6, 0.8, 1.0, 1.0) if value == 'BUY' else (1.0, 0.8, 0.6, 1)

                # check for new day
                blank_row = False
                fg = (0, 0, 0, 1)
                if col == 'create_time':
                    # new day
                    if value[:value.index(' ')] != date:
                        # get the date string 'yyyy-mm-dd'
                        text = value[:value.index(' ')]
                        blank_row = True
                        date = text
                        fg = (0.2, 0.1, 0.3, 1.0)
                    # same day
                    else:
                        text = value[value.index(' ') + 1:]
                else:
                    text = str(value)

                # add widget
                h_align = 'left' if col == 'remark' else 'center'
                button = Button(text=text, color=fg, halign=h_align, valign='center',
                                size=(col_width, row_height), size_hint=(None, None),
                                background_normal='', background_down='', background_color=bg)
                button.text_size = button.size
                self.ids['data_table'].add_widget(button)

                # add blank row for new day
                if blank_row:
                    # add blank widget
                    for j in range(trade_journal.shape[1] - 1):
                        self.ids['data_table'].add_widget(Widget())

                    # add time again
                    button = Button(text=value[value.index(' ')+1:], halign=h_align, valign='center',
                                    size=(col_width, row_height), size_hint=(None, None),
                                    background_normal='', background_down='', background_color=bg)
                    button.text_size = button.size
                    self.ids['data_table'].add_widget(button)

        # fill up the space
        self.ids['data_table'].add_widget(Widget())

    # ------------------------------------------------------------------------------------------- #
    """ button's callback """
    # ------------------------------------------------------------------------------------------- #
    def show_calendar(self, start_or_end: str):
        self.calendar.show_popup(1, 0.5)
        self.calendar.update = start_or_end

    def refresh(self, instance=None):
        self.main_app.popup.dismiss()
        self.main_app.popup.content = Label(text="Loading data...")
        self.main_app.popup.open()
        trade_journal = self.main_app.futu.refresh_trade_journal(self.start_date, self.end_date)
        self.update_table(trade_journal)
        self.main_app.popup.dismiss()

    def update_filter(self, instance=None):
        self.refresh()
