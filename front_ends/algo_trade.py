import datetime as dt
import pandas as pd

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
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
        self.main_app = App.get_running_app()
        self.color_map = {
            'green': (0.3, 1.0, 0.3, 1.0),
            'red': (1.0, 0.2, 0.2, 1.0),
            'grey': (0.3, 0.3, 0.3, 1)
        }
        self.auto_shutdown = self.ids['checkbox_auto_shutdown'].active  # get checkbox by 'id' in kv file
        self.strategies = {}
        self.calendar = Calendar(self)

        # initialize start and end date
        now = dt.datetime.now()
        if now.hour < 3:
            now = now - dt.timedelta(days=1)
        self.today = dt.datetime.date(now)
        self.start_date = self.today
        self.end_date = self.today
        self.ids['label_date_from'].text = dt.datetime.strftime(self.start_date, '%d-%b-%y')
        self.ids['label_date_to'].text = dt.datetime.strftime(self.end_date, '%d-%b-%y')

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
        """
        update algo table while
            1. app launch
            2. futu-api TradeDealHandler callback
        :param df: dataframe format:
                Status  Strategy    ExecSet Inventory   P / L   MaxCtrt AvgPrice    TradeQty    Fees    Order   InitMargin
            0   MAL                                                                                     PlsSelect
            1   SWL                                                                                     PlsSelect

        :return: None
        """
        self.main_app.popup.dismiss()

        if not self.strategies:
            return

        self.table = df.copy()

        # initialize table
        self.ids['data_table'].clear_widgets()
        col_width, row_height = 80, 30
        self.ids['data_table'].cols = len(self.table.columns) + 1  # include column for 'on/off' checkbutton
        self.ids['data_table'].add_widget(Widget(size=(22, row_height), size_hint=(None, None)))

        # add headers
        for header in self.table.columns:
            self.ids['data_table'].add_widget(
                Button(text=header,
                       size=(col_width, row_height),
                       size_hint=(None, None),
                       background_normal='',
                       background_down='',
                       background_color=self.color_map.get('grey')
                       )
            )

        # add rows
        max_contract_total = initial_margin_total = 0
        for index, row in self.table.iterrows():
            # add 'on/off' checkbutton
            checkbox = CheckBox(active=True, size=(20, row_height), size_hint=(None, None))
            checkbox.bind(on_press=lambda cb: self.set_on_off_algo(cb))
            self.ids['data_table'].ids[row['Strategy'] + '_OnOff'] = checkbox  # set id to checkbox, e.g. MAL_OnOff
            self.ids['data_table'].add_widget(checkbox)

            # add other widgets inside the table
            strategy = self.strategies.get(row['Strategy'])
            for col in self.table.columns:
                if col == 'Order':
                    order = OrderSpinner()
                    order.ids['Strategy'] = row['Strategy']
                    self.ids['table_table'].add_widget(order)

                label = Label(markup=True, font_size=18)
                """
                Just leave it, will continue later
                """

    # buttons' callback ---------------------------------------------------------------------------
    def start_all(self, instance):
        print("start all")

    def stop_all(self, instance):
        print("stop all")

    def cover_all(self, instance):
        print("cover all")

    def refresh(self, instance):
        print("refresh", self.start_date, self.end_date)

    def update_auto_shutdown(self, instance):
        print("update auto shutdown", instance.active)

    def set_on_off_algo(self):
        print("set on/off algo")

    def manual_order(self, instance, strategy_name: str, operation: str):
        print("manual order")

    # helper methods ------------------------------------------------------------------------------
    def load_strategies(self):
        """
        to be loaded after all gui has been built (the 'on_start' method from the 'App')
        :return:
        """
        pass
