"""
Help Screen

NB: Kv String cannot contain \n -> must be \\n

"""


from kivy.lang.builder import Builder
from subs.gui.screens.scr import Scr
from subs.gui.vars import *
from kivy.clock import Clock

kv_str = """
#:kivy 1.10.1

<HelpScreen>:
    Label:
        id: help
        pos_hint: {'right': 0.6, 'top': 0.6} #relative sizes 0-1
        size_hint: 0.2, 0.1
        text: "Under Construction"
        font_size: '15sp'
        color: WHITE
        text_size: self.size
        halign: "center"

"""

class HelpScreen(Scr):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(kv_str)