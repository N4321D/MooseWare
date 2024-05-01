"""
Screen Template

NB: Kv String cannot contain \n -> must be \\n

"""

from datetime import timedelta
from kivy.lang.builder import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, DictProperty, ConfigParserProperty
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.boxlayout import BoxLayout

from subs.gui.screens.scr import Scr
from subs.gui.vars import *

import time

# Logger
from subs.log import create_logger
logger = create_logger()
def log(message, level="info"):
    cls_name = "LAST_VALUES SCREEN"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here


kv_str = """
#:kivy 1.10.1

<DataItem@BoxLayout>:
    Label:
        id: title
    Label:
        id: data

<LastValScreen>:
    BoxLayout:
        id: datagrid

"""
class DataItem(BoxLayout):
    pass

class LastValScreen(Scr):
    data = DictProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(kv_str)

        self.shared_buffer = self.app.IO.shared_buffer

        Clock.schedule_interval(self.get_last_value, 2)

    
    def get_last_value(self, *args, **kwargs):
        """
        collects last data points from shared buffer for each interface
        """
        self.data = {}                                          # clear dictionary
        for interface in self.shared_buffer.buffer:
            if interface == 'notes':
                continue
            last_values = self.shared_buffer.get_buf(interface, 
                                                     start=..., # has to be a value but not None
                                                     end=None,  # None indicates last added data
                                                     n_items=1, # number of items to get back from end (will overwrite start)
                                                     )[0]
            last_values = {k: v for k, v in zip(last_values.dtype.names, last_values)}
            self.data[interface.replace(" ", "\n")] = last_values
        self.create_widgets()

    def create_widgets(self, *args, **kwargs):
        """
        creates text widgets with last data
        """
        self.clear_widgets()
        for interface, data in self.data.items():
            widget = DataItem()
            widget.ids.title.text = interface
            widget.ids.data.text = '\n'.join(f"{key}: {value}" for key, value in data.items())
            self.add_widget(widget)


            