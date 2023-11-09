"""
Screen Saver

NB: Kv String cannot contain \n -> must be \\n

"""


from kivy.lang.builder import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, ConfigParserProperty
from kivy.app import App

from subs.gui.vars import *
from subs.driver.rpi_touch_screen import RpiTouchScreen

from functools import partial
import numpy as np

# create logger
try:
    from subs.log import create_logger
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None: 
                f = lambda *x: print("FILEMANAGER: ", *x)  # change messenger in whatever script you are importing
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()

def log(message, level="info"):
    getattr(logger, level)("FILEMANAGER: {}".format(message))  # change RECORDER SAVER IN CLASS NAME


kv_str = """
#:kivy 1.10.1

<ScreenSaver>:
    on_touch_down: self.last_screen() # go back to last screen
    on_enter: 
        self.main()
        self.dim_screen(self.max_brightness, self.min_brightness, 1.5)
    on_leave: 
        self.event.cancel()
        self.dim_screen(self.min_brightness, self.max_brightness, 1.5)

    # create new layout specfically for screensaver
    FloatLayout:
        Label:
            id: scrsavtxt
            pos_hint: {'x': root.coord[0], 'top': root.coord[1]}
            size_hint: 0.2, 0.2
            text: ''
            font_size: '30sp'

"""

class ScreenSaver(Screen):
    coord = ListProperty([0.5, 0.5])

    max_brightness = ConfigParserProperty(60, "main", "max_brightness", "app_config", val_type=int,
                                          verify = lambda x: True if 30 <= x <= 100 else False)
    min_brightness = ConfigParserProperty(8, "main", "min_brightness", "app_config", val_type=int, 
                                          verify = lambda x: True if 0 <= x <= 100 else False)


    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(kv_str)
        self.app = App.get_running_app()
        self.event = Clock.schedule_once(self.main, 1)
        self.touch_screen = RpiTouchScreen()
        self.screen_brightness(self.max_brightness)
        self.bind(max_brightness=lambda *_: self.screen_brightness(self.max_brightness))
        self.bind(min_brightness=lambda *_: None)    # binding automatically creates items in settings.ini

    def main(self, *args):
        self.coord = (np.random.random(2) * 0.6 + 0.2).tolist()

        if self.app.IO.running:
            txt = f"{self.app.setupname}\nRecording: {self.app.IO.recording_name}"
        else:
            txt = f"{self.app.setupname}\nSCREEN SAVER"

        self.ids['scrsavtxt'].text = txt
        self.ids['scrsavtxt'].color = RED
        return self.event()

    def last_screen(self):
        self.app.root.ids.menubar.size_hint = (1, 0.1)
        self.manager.current = self.app.prev_screen
    
    def screen_brightness(self, brightness, *args):
        brightness = (brightness / 100) * 0xff
        self.touch_screen.brightness = brightness
    
    def dim_screen(self, start_br, end_br, duration, *args, t=0):
        dt = duration / abs(start_br - end_br)
        step = -10 if start_br > end_br else 10
        for br in range(start_br, end_br, step):
            Clock.schedule_once(partial(self.screen_brightness, br), t)
            t += dt
