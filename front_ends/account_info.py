import logging
import os
import pandas as pd

os.environ['KIVY_LOG_MODE'] = 'MIXED'
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class AccountInfo(Widget):
    id = 'account_info'

    def __init__(self):
        super().__init__()
        self.main_app = App.get_running_app()

    def update_data(self):
        self.main_app.popup.dismiss()
        self.main_app.popup.content = Label(text="Loading data...")
        self.main_app.popup.open()

        # get real account info no matter it is demo or not
        error_code, ret_data = self.main_app.futu.trd_ctx.accinfo_query()  # error_code: 0/ 1
        if error_code:
            self.main_app.popup.dismiss()
            self.main_app.popup.content = Label(text=ret_data)
            self.main_app.popup.open()
            Clock.schedule_once(lambda time: self.main_app.popup.dismiss, 10)
            return

        self.update_table(ret_data)
        self.main_app.popup.dismiss()

    def update_table(self, data: pd.DataFrame):
        self.ids['funds_table'].clear_widgets()

        # set params
        row_height = 30
        self.ids['funds_table'].row = len(data.columns)
        self.ids['funds_table'].cols = data.shape[0] + 1  # including header

        for header in data.columns:
            # add header
            h = header.replace('_', ' ').title()
            button = Button(text=h, halign='left', valign='center',
                            size=(250, row_height), size_hint=(None, None),
                            background_normal='', background_down='', background_color=(0.7, 0.7, 0.7, 1))
            button.text_size = button.size
            self.ids['funds_table'].add_widget(button)

            # add value
            value = data.at[0, header]
            color = (0, 0, 0, 1)
            if isinstance(value, int | float):
                color = (1.0, 0.0, 0.0, 1.0) if value < 0 else color
                value = '{:,.0f}'.format(value)
            button = Button(text=value, halign='left', valign='center',
                            size=(100, row_height), size_hint=(None, None),
                            color=color, background_normal='', background_down='', background_color=(0, 0, 0, 0))
            button.text_size = button.size
            self.ids['funds_table'].add_widget(button)
