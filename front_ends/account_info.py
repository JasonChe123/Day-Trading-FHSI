import logging
import os

os.environ['KIVY_LOG_MODE'] = 'MIXED'  # [KIVY, PYTHON, MIXED]
from kivy.app import App
from kivy.uix.widget import Widget


class AccountInfo(Widget):
    id = 'account_info'

    def __init__(self):
        super().__init__()
        self.main_app = App.get_running_app()

    def update_data(self):
        pass

    def update_table(self, df):
        pass
