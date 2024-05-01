"""
Screen Template

NB: Kv String cannot contain \n -> must be \\n

"""

from datetime import timedelta
from kivy.lang.builder import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, DictProperty, ConfigParserProperty
from kivy.uix.togglebutton import ToggleButton
from subs.gui.widgets.custom_settings import timestr_2_timedelta, val_type_loader

from subs.gui.screens.scr import Scr
from subs.gui.vars import *

# used in kv builder, do not remove!
from subs.gui.widgets.graph import Graph

import time

# Logger
from subs.log import create_logger
logger = create_logger()
def log(message, level="info"):
    cls_name = "LAST_VALUES SCREEN"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here


kv_str = """
#:kivy 1.10.1

<LastValScreen>:

"""

class LastValScreen(Scr):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(kv_str)

        self.shared_buffer = self.app.IO.shared_buffer

        Clock.schedule_interval(self.get_last_value, 2)

        # Dictionary with link to sensors
        # self.rwi2c = self.app.IO.readwrite
    
    def get_last_value(self, *args, **kwargs):
        for interface, data in self.shared_buffer.buffer.items():
            if interface == 'notes':
                continue
            last_values = self.shared_buffer.get_buf(interface, 
                                                     start=..., # has to be a value but not None
                                                     end=None,  # None indicates last added data
                                                     n_items=1, # number of items to get back from end (will overwrite start)
                                                     )
            print(last_values)
            