# SYSTEM MODULES ----------------------------------------------------------------------------------
import logging
import os
from pathlib import Path
import re
import sys
import threading as th

# PROJECT MODULES ---------------------------------------------------------------------------------
"""from library.futu_api import FutuApi
from library.ibapi import IBApi
from library.printing import LogPrint
import library.system_programme_running as spr
from front_ends.algo_trade_main_page import AlgoTradeMainPage"""

# GUI MODULES -------------------------------------------------------------------------------------
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.carousel import Carousel
from kivy.uix.label import Label
from kivy.uix.popup import Popup


class AnsiEscapeCodeRemover:
    """
    A custom file-like object that removes ANSI escape codes from text before writing to a file.
    Use for writing log/ printed text to a .txt file rather than a terminal.
    """

    def __init__(self, file):
        self.file = file

    def write(self, text):
        # Remove ANSI escape codes from the text
        text = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)
        # Write the modified text to the file
        self.file.write(text)

    def flush(self):
        self.file.flush()

