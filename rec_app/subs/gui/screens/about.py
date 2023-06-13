"""
About screen

NB: Kv String cannot contain \n -> must be \\n

"""


from kivy.lang.builder import Builder
from subs.gui.screens.scr import Scr
from kivy.core.audio import SoundLoader

from subs.gui.vars import *

kv_str = """
#:kivy 1.10.1
<AboutScreen>:
    Label:
        id: help
        pos_hint: {'right': 0.5, 'top': 0.5} #relative sizes 0-1
        size_hint: 0.1, 0.1
        text: root.text
        markup: True
        halign: 'center'
        valign: 'center'
        font_size: '15sp'
        color: WHITE
        on_ref_press:
            secretmoose.size_hint = (0.8, 0.8)
            root.sound.play()

    STT:
        id: secretmoose
        pos_hint: {'right': 0.9, 'top': 0.85} #relative sizes 0-1
        size_hint: 0, 0
        halign:'right'
        valign:'center'
        on_touch_down:
            self.size_hint = (0, 0)
            root.sound.stop()
        Image:
            source: './Icons/moose_secret.jpg'
            size: root.size
            pos_hint: {'right': 1, 'top': 1}

"""


class AboutScreen(Scr):
    text = """
    by [b]MOOSEWARE[/b] [i]2019[/i]\n
    [ref=moose]
                    VVVVV\\         /VVVVV
                    =|@@|=
                         --      [/ref]

                Andrew Charles
                Guido Faas
                Dmitri Yousef Yengej    
            """

    # Easter egg
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(kv_str)
        try:
            self.sound = SoundLoader.load('./Icons/moose.mp3')
            self.sound.volume = 1
            self.sound.loop = True
        except AttributeError:
            pass
