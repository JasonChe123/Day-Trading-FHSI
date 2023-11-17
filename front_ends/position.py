import logging
import os
import pandas as pd

os.environ['KIVY_LOG_MODE'] = 'MIXED'
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class Position(Widget):
    id = 'position'

    def __init__(self):
        super().__init__()
        self.main_app = App.get_running_app()
        self.project_directory = self.main_app.proj_dir

    def update_data(self):
        self.main_app.popup.dismiss()
        self.main_app.popup.content = Label(text="Loading data...")
        self.main_app.popup.open()

        # get real account info no matter it is demo or not
        error_code, ret_data = self.main_app.futu.trd_ctx.position_list_query()  # error_code: 0/ 1
        if error_code:
            self.main_app.popup.dismiss()
            self.main_app.popup.content = Label(text=ret_data)
            self.main_app.popup.open()
            Clock.schedule_once(lambda time: self.main_app.popup.dismiss, 10)
            return

        self.update_table(ret_data)
        self.main_app.popup.dismiss()

    def update_table(self, data: pd.DataFrame):
        self.ids['position_table'].clear_widgets()

        # set params
        row_height = 30
        self.ids['position_table'].cols = 2

        # extract and sum data for MHI
        if not data.empty:
            data = pd.concat(
                # convert series to dataframe and swap row and column
                [data, data.loc[data['code'].str[3:6] == 'MHI'].sum(numeric_only=True).to_frame().T],
                ignore_index=True
            )
            # set code and stock_name
            data.loc[data.index[-1], 'code'] = data.at[0, 'code']
            data.loc[data.index[-1], 'stock_name'] = data.at[0, 'stock_name']

            # get the last row (the grouped and sum row)
            data = data.tail(1).reset_index(drop=True)

        # add widgets
        for header in data.columns:
            # add header
            button = Button(text=header.replace('_', ' ').title(), halign='left', valign='center',
                            size=(250, row_height), size_hint=(None, None),
                            background_normal='', background_down='', background_color=(0.7, 0.7, 0.7, 1.0))
            button.text_size = button.size
            self.ids['position_table'].add_widget(button)

            # add value
            if data.empty:
                self.ids['position_table'].add_widget(Widget())
                continue

            # set color
            value = data.at[0, header]
            color = (0, 0, 0, 1)
            if isinstance(value, int | float):
                if value < 0:
                    color = (1.0, 0.0, 0.0, 1.0)

            button = Button(text=str(value), halign='left', valign='center',
                            size=(100, row_height), size_hint=(None, None),
                            color=color, background_normal='', background_down='', background_color=(0, 0, 0, 0))
            button.text_size = button.size

            # set chinese font
            if header == 'stock_name':
                button.font_name = os.path.join(self.project_directory, 'library', 'fonts', 'Source Han Sans CN Light.otf')

            self.ids['position_table'].add_widget(button)
