"""
Splash screen
"""


from kivy.lang.builder import Builder
from subs.gui.screens.scr import Scr
from subs.gui.vars import *
from kivy.clock import Clock

kv_str = """
#:kivy 1.10.1
<SplashScreen>:
    canvas.before:
        Rectangle:
            pos: self.pos
            size: self.size
            source: 'Icons/MooseBackgr.png'
"""


class SplashScreen(Scr):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(kv_str)

    def skip(self, dt):
        self.manager.current = 'Record'

    def on_enter(self, *args):
        Clock.schedule_once(self.skip, SPLASH_SCREEN_TIMEOUT)

        # TODO: easteregg: if datetime.now().strftime("%m %d") == '04 01':
        # self.manager.current == 'about'
        # in about activate moose automatically on apr 01