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
