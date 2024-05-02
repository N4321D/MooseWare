"""
Screen Template

NB: Kv String cannot contain \n -> must be \\n

"""

from datetime import timedelta
from kivy.lang.builder import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, DictProperty, ConfigParserProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import App

from subs.gui.vars import MO, MO_BGR, LIGHTER_BLUE

import time

# Logger
from subs.log import create_logger
logger = create_logger()
def log(message, level="info"):
    cls_name = "LAST_VALUES SCREEN"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here


def kivy_rgba_to_rgba(inp):
    inp = [int(i*0xff) for i in inp]
    out = hex(inp[0] << 24 | inp[1] << 16 | inp[2] << 8 | inp[3])[2:]
    return out

HIGHLIGHT_TXT_COL = kivy_rgba_to_rgba(MO)
PAR_TXT_COL = kivy_rgba_to_rgba(LIGHTER_BLUE)

kv_str = """
#:kivy 2.1.0

<LabLastData@Label>:
    text_size: self.size
    markup: True
    background_color: 0, 0.5, 0.3, 1
    height: self.texture_size[1]
    halign: "left"
    valign: "top"

<LabLastDataTitle@Label>:
    text_size: self.size
    markup: True
    background_color: 0, 0.5, 0.3, 1
    height: self.texture_size[1]
    halign: "left"
    valign: "top"

<DataItem@BoxLayout>:
    orientation: "vertical"

<LastValWidget>:
    size_hint: 1, 0.9
    pos_hint: {"top": 1, "right": 1}
    canvas.before:
        Color:
            rgba: (0, 0, 0, 0.6)
        Rectangle:
            pos: self.pos
            size: self.size
    orientation: "vertical"

    BoxLayout:
        id: datagrid
        orientation: "horizontal"
        size_hint_y: 0.9

    # Button Panel
    BoxLayout:
        size_hint_y: 0.1
        orientation: "horizontal"

        # filler button
        Button:
            background_color: BUT_BGR
            disabled: True
            size_hint_x: 0.8

        # Close Button:        
        Button:
            color: MO
            background_color: BUT_BGR
            id: close_panel
            text: "Close\\nPanel"
            on_release: root.parent.remove_widget(root)
            size_hint_x: 0.2

"""
class DataItem(BoxLayout):
    pass

class LastLabData(Label):
    pass

class LastLabDataTitle(LastLabData):
    pass

class LastValWidget(BoxLayout):
    data = DictProperty({})

    def __init__(self, **kwargs):
        Builder.load_string(kv_str)
        super().__init__(**kwargs)
        
        
        self.app = App.get_running_app()
        self.shared_buffer = self.app.IO.shared_buffer

        Clock.schedule_interval(self.get_last_value, 2)
    
    def on_touch_down(self, touch):
            """
            Handle touch down events. Defined here to blcok touches to underlying
            widgets (see kivy ModalView as example)
            
            Parameters
            ----------
            touch : kivy.input.Touche
                Touch event instance.
            
            Returns
            -------
            bool
                Returns True if the touch was within the widget, to prevent further processing
                of touch events and activate the widget.
                Returns False if the touch was outside of the widget, to allow interaction with
                other widgets that are not below the panel.
            
            """
            if self.collide_point(*touch.pos):
                super().on_touch_down(touch)
            else:
                return False
            return True

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
        self.ids.datagrid.clear_widgets()
        for interface, data in self.data.items():
            widget = DataItem()
            widget.add_widget(LastLabDataTitle(
                text=f"[b][u][color=#{PAR_TXT_COL}]{interface}[/color][/b][/u]",     
                markup=True,
                ))
            widget.add_widget(LastLabData(
                text='\n'.join(f"{key}: {value:.3f}" for key, value in data.items()),
                markup=True,
                ))
            self.ids.datagrid.add_widget(widget)


if __name__ == "__main__":
    """
    test code

    """
    import numpy as np

    class TestSharedBuffer:
        def __init__(self):
            self.buffer = {
        }


        def get_buf(self, interface, start, end, n_items):
            if interface in self.buffer:
                return self.buffer[interface]
            else:
                return []

    class TestIO:
        def __init__(self):
            self.shared_buffer = TestSharedBuffer()

    class TestApp(App):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.IO = TestIO()
            self.last_val_wid = LastValWidget()
            Clock.schedule_interval(self.make_data, 1)

        def build(self):
            return self.last_val_wid
        
        def make_data(self, *args):
            data = {'interface1': np.array(np.random.randint(0, 10, (3)),
                dtype=[('par1', 'i2'), ('par2', 'f4'), ('par3', 'bool')]),
            'interface2':  np.array(np.random.random(3),
                dtype=[('par1', 'i2'), ('par2', 'f4'), ('par3', 'f4')])}
            self.IO.shared_buffer.buffer = data

    app = TestApp()
    app.run()