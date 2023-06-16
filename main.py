# SYSTEM MODULES ----------------------------------------------------------------------------------
import logging
from pathlib import Path
import re
import os
import sys
import threading as th

# PROJECT MODULES ---------------------------------------------------------------------------------
"""from library.futu_api import FutuApi
from library.ibapi import IBApi
from library.printing import LogPrint
import library.system_programme_running as spr
from front_ends.algo_trade_main_page import AlgoTradeMainPage"""

# GUI MODULES -------------------------------------------------------------------------------------
os.environ['KIVY_LOG_MODE'] = 'MIXED'  # separate logging between python and kivy
import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.carousel import Carousel
from kivy.uix.label import Label
from kivy.uix.popup import Popup


class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = '%(asctime)s <%(name)s> [ %(levelname)-8s ] %(message)s ("%(filename)s:%(lineno)s)"'

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


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


def config_logging():
    # set kivy loglevel
    Logger.setLevel(logging.WARNING)

    # set system loglevel
    mylogger = logging.getLogger('root')
    mylogger.setLevel(logging.INFO)

    # set handler
    file_name = 'demo.log' if IS_DEMO else 'live.log'
    file_path = os.path.join(PROJECT_DIR, 'database', 'log', file_name)
    file_handler = logging.FileHandler(file_path, encoding='utf-8')
    stream_handler = logging.StreamHandler(sys.stdout)

    # set formatter
    file_formatter = logging.Formatter(
        '%(asctime)s <%(name)s> [ %(levelname)-8s ] %(message)s "(%(filename)s:%(lineno)s)"',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    stream_handler.setFormatter(CustomFormatter())
    file_handler.setFormatter(file_formatter)

    # add handler
    mylogger.addHandler(file_handler)
    mylogger.addHandler(stream_handler)


if __name__ == '__main__':
    PROJECT_DIR = os.getcwd()
    IS_DEMO = True
    IS_PRINT_TO_FILE = False
    RUNNING_STRATEGIES = []

    # check system arguments
    arguments = sys.argv[1:]  # the first argument is file name
    for argv in arguments:
        argv = argv.lower()
        if 'demo=' in argv and argv.lstrip('demo=') == 'false':
            IS_DEMO = False
        if 'print_to_file=' in argv and argv.lower().lstrip('print_to_file=') == 'true':
            IS_PRINT_TO_FILE = True
        if 'strategy=' in argv:
            RUNNING_STRATEGIES = argv.lstrip('strategy=').upper().split(',')

    # configure logging
    config_logging()
