import logging
import os
import sys
from kivy.logger import Logger


class CustomFormatter(logging.Formatter):

    grey = "\x1b[37m"
    yellow = "\x1b[33m"
    white = "\x1b[m"
    red = "\x1b[31m"
    black_yellow_bg = "\x1b[30;43m"
    black_red_bg = "\x1b[30;41m"
    formatter = lambda colour: f'%(asctime)s <%(name)-20s> {colour} [ %(levelname)-8s ] %(message)s \x1b[0m ("%(filename)s:%(lineno)s")'

    FORMATS = {
        logging.DEBUG: formatter(grey),
        logging.INFO: formatter(white),
        logging.WARNING: formatter(red),
        logging.ERROR: formatter(black_yellow_bg),
        logging.CRITICAL: formatter(black_red_bg),
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


def config_logging(is_demo: bool, proj_dir: os.path):
    os.environ['KIVY_LOG_MODE'] = 'MIXED'  # [KIVY, PYTHON, MIXED]

    # set kivy loglevel
    Logger.setLevel(logging.WARNING)

    # set system loglevel
    mylogger = logging.getLogger('root')
    mylogger.setLevel(logging.INFO)  # todo: turn it to INFO while finish testing

    # define log file path
    file_name = 'demo.log' if is_demo else 'live.log'
    file_path = os.path.join(proj_dir, 'database', 'log', file_name)

    # set handlers
    file_handler = logging.FileHandler(file_path, encoding='utf-8')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)  # todo: should be set to INFO, DEBUG is just for developing stage

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
