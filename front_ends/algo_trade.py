import datetime as dt
import importlib.util
import inspect
import logging
import os

import pandas as pd

os.environ['KIVY_LOG_MODE'] = 'MIXED'
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.widget import Widget
from KivyCalendar import DatePicker


class Calendar(DatePicker):
    def __init__(self, algo_trade):
        super().__init__()
        self.update = ''  # update string: 'start'/ 'end'
        self.algo_trade = algo_trade

    def update_value(self, inst):
        self.text = '%s.%s.%s' % tuple(self.cal.active_date)
        self.algo_trade.update_date(self.update)


class OrderSpinner(Spinner):
    """
    drop down menu for order selection (buy/ sell/ cover)
    """
    def _on_dropdown_select(self, instance, data, *largs):
        super()._on_dropdown_select(instance, data, *largs)
        App.get_running_app().algo_main_page.algo_trade.manual_order(self)


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

    # ------------------------------------------------------------------------------------------- #
    """ update gui """
    # ------------------------------------------------------------------------------------------- #
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

    def update_table(self):
        """
        update algo table while
            1. app launch
            2. futu-api TradeDealHandler callback

        :param data: dataframe format:
                Status  Strategy    ExecSet Inventory   P / L   MaxCtrt AvgPrice    TradeQty    Fees    Order   InitMargin
            0   MAL                                                                                     PlsSelect
            1   SWL                                                                                     PlsSelect

        :return: None
        """
        self.main_app.popup.dismiss()

        # do nothing if no any running strategies
        if not self.strategies.keys():
            return

        # setup self.table in DataFrame format
        self.algo_table = self.main_app.futu.get_algo_table(self.strategies.keys(), self.start_date, self.end_date)

        # initialize table (gui)
        self.ids['data_table'].clear_widgets()
        col_width, row_height = 80, 30
        self.ids['data_table'].cols = len(self.algo_table.columns) + 1  # include column for 'on/off' checkbutton

        # add headers
        self.ids['data_table'].add_widget(Widget(size=(22, row_height), size_hint=(None, None)))  # on/off column
        for header in self.algo_table.columns:
            self.ids['data_table'].add_widget(
                Button(text=header, size=(col_width, row_height), size_hint=(None, None),
                       background_normal='', background_down='', background_color=self.color_map.get('grey'))
            )

        # add rows
        def add_check_button():
            checkbox = CheckBox(active=True, size=(20, row_height), size_hint=(None, None))
            checkbox.bind(on_press=lambda cb: self.set_on_off_algo(cb))
            self.ids['data_table'].ids[row['Strategy'] + '_OnOff'] = checkbox  # set id to checkbox, e.g. MAL_OnOff
            self.ids['data_table'].add_widget(checkbox)

        def add_order_spinner(row):
            order = OrderSpinner()
            order.ids['Strategy'] = row['Strategy']
            self.ids['data_table'].add_widget(order)

        max_contract_total = initial_margin_total = 0
        for index, row in self.algo_table.iterrows():  # looping for row <----------
            # filter out the trade is not related to the algo trade strategies
            if not self.strategies.get(row['Strategy']):
                continue

            # add widgets
            add_check_button()
            strategy = self.strategies.get(row['Strategy'])
            for col in self.algo_table.columns:  # looping for column <----------
                # reset params
                color = (1.0, 1.0, 1.0, 1.0)
                halign = 'center'
                label = Label(markup=True, font_size=18, text_size=(col_width, row_height),
                              size=(col_width, row_height), size_hint=(None, None), valign='middle')
                value = row[col]

                # configure columns
                match col:
                    case 'Status':
                        value = strategy.status
                        self.ids['data_table'].ids[row['Strategy'] + '_Status'] = label  # set id
                    case 'ExecSet':
                        value = strategy.exec_set
                    case 'MaxCtrt':
                        value = strategy.max_contract
                        max_contract_total += value
                    case 'InitMargin':
                        # if futu_openD not ready
                        init_margin = 22000 if not self.main_app.futu.contract_detail else \
                            abs(strategy.max_contract) * self.main_app.futu.contract_detail.get('margin')
                    case 'Order':
                        add_order_spinner(row)
                        continue

                # apply configuration
                text, color, halign = self.format_label(col, value)
                label.text, label.color, label.halign = text, color, halign

                # assign id
                """
                access method: label = self.ids['data_table'].ids['MAL_PL']
                """
                match col:
                    case 'P / L':
                        self.ids['data_table'].ids[row['Strategy'] + '_PL'] = label
                    case 'AvgPrice':
                        self.ids['data_table'].ids[row['Strategy'] + '_AvgPrice'] = label
                    case 'Inventory':
                        self.ids['data_table'].ids[row['Strategy'] + '_Inventory'] = label

                # add widget
                self.ids['data_table'].add_widget(label)

    def update_realtime_pnl(self, price: float):
        if self.algo_table.empty:
            return

        df = self.algo_table.copy()
        pnl_total = inv_total = 0
        point_value = 10
        for index, row in df.iterrows():
            strategy_name = row['Strategy']
            if row['Inventory']:
                # calculate realtime P/L
                realize_pnl = row['P / L']
                inventory = row['Inventory']
                avg_price = row['AvgPrice']
                realtime_pnl = realize_pnl + (price - avg_price)*inventory*point_value

                # update label
                label = self.ids['data_table'].ids[f'{strategy_name}_PL']  # get label widget
                label.color = (0, 1, 0, 1) if realtime_pnl >= 0 else (1, 0, 0, 1)
                text = '{:,.0f}'.format(realtime_pnl)
                label.text = f'[b]{text}[/b]' if realtime_pnl < 0 else f'[b]{"+"+text}[/b]'

    # ------------------------------------------------------------------------------------------- #
    """ button's callback """
    # ------------------------------------------------------------------------------------------- #
    def start_all(self, instance=None):
        logging.critical("start all")

    def stop_all(self, instance=None):
        logging.critical("stop all")

    def cover_all(self, instance=None):
        logging.critical("cover all")

    def refresh(self, instance=None):
        self.update_table()

    def update_auto_shutdown(self, instance=None):
        logging.critical(f"update auto shutdown {instance.active}")

    def set_on_off_algo(self, instance=None):
        logging.critical("set on/off algo")

    def manual_order(self, instance: Spinner = None, strategy_name: str = '', operation: str = '',):
        """
        callback from order spinner in algo_trade
        """
        # check strategy
        strategy = self.strategies.get(instance.ids['Strategy']) if not strategy_name else self.strategies.get(strategy_name)
        operation = instance.text if instance else operation

        match operation:
            case 'Buy' | 'Sell':
                qty = strategy.exec_set
                side = operation.upper()
                remark = 'LE-MANUAL' if side == 'BUY' else 'SE-MANUAL'
            case 'Cover':
                qty = abs(strategy.inv_algo)
                if not qty:
                    logging.critical("Nothing to be covered.")
                    return
                side = 'SELL' if strategy.inv_algo > 0 else 'BUY'
                remark = 'COVER-MANUAL'
            case _:
                return

        self.main_app.futu.fire_trade(side=side, qty=qty, remark='-'.join([strategy.name, remark]))
        self.refresh()

    # ------------------------------------------------------------------------------------------- #
    """ helper methods """
    # ------------------------------------------------------------------------------------------- #
    def load_strategies(self):
        """
        Load strategies after all gui had been built (the 'on_start' method from the 'App').
        :return:
        """
        # get all files in algorithm
        strategy_file_names = os.listdir(os.path.join(self.main_app.proj_dir, 'algorithm'))

        # check if 'ready' in strategy_file_names
        for file_name in strategy_file_names:
            if 'ready' in file_name:
                # import module from file
                spec = importlib.util.spec_from_file_location(
                    os.path.splitext(file_name)[0],
                    os.path.join(self.main_app.proj_dir, 'algorithm', file_name)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # import all classes as strategies
                for class_ in inspect.getmembers(module, inspect.isclass):  # [(class_name, class_instance), ...]
                    if class_[0] == 'AlgoTemplate':
                        continue
                    self.__setattr__(class_[1].name.lower(),
                                     class_[1](self.main_app, 'MHI')
                                     )
                    # assign strategy to dictionary
                    self.strategies[class_[1].name] = self.__getattribute__(class_[1].name.lower())

    def format_label(self, col, value):
        color = (1, 1, 1)
        halign = 'center'
        text = value

        # format for number
        if col in ('Inventory', 'P / L', 'MaxCtrt', 'AvgPrice', 'TradedQty', 'Fees', 'InitMargin'):
            # format number
            value = value if value else 0
            text = '{:,.0f}'.format(value)
            text = '+' + text if col == 'P / L' and value > 0 else text

            # format color
            if col in ('Inventory', 'P / L', 'MaxCtrt'):
                color = self.color_map.get('green') if value >= 0 else self.color_map.get('red')

            # format alignment
            if col in ('P / L', 'AvgPrice', 'TradedQty', 'Fees', 'InitMargin'):
                halign = 'right'

        # format for string
        elif col == 'Status':
            if value in ('ready', 'running', 'waiting'):
                color = self.color_map.get('green')
            elif value in ('stop', 'timeout'):
                color = self.color_map.get('red')

        return str(text), color, halign

    def update_strategy_params(self):
        pass
