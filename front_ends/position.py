import os
# os.environ['KIVY_LOG_MODE'] = 'MIXED'
from kivy.app import App
from kivy.uix.widget import Widget


class Position(Widget):
    id = 'position'

    def __init__(self):
        super().__init__()
        self.main_app = App.get_running_app()
        self.project_directory = self.main_app.proj_dir

    def update_data(self):
        pass

    def update_table(self, df):
        pass
