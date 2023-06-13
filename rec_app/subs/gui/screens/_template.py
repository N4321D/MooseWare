"""
Screen Template

NB: Kv String cannot contain \n -> must be \\n

"""


from kivy.lang.builder import Builder
from subs.gui.screens.scr import Scr
from subs.gui.vars import *
from kivy.clock import Clock

kv_str = """
#:kivy 1.10.1

<xScreen>:
    on_enter: print("hello")

"""

class xScreen(Scr):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(kv_str)