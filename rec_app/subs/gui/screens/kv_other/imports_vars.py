from kivy.lang import Builder

Builder.load_string(
"""
#:kivy 1.10.1
# filename main.py

#: import NoTransition kivy.uix.screenmanager.NoTransition
#: import Color kivy.graphics.Color

#: import Clock kivy.clock.Clock

#: import VKeyboard kivy.uix.vkeyboard.VKeyboard

#: import partial functools.partial

# Colors
#: import WHITE subs.gui.vars.WHITE
#: import MO subs.gui.vars.MO
#: import BUT_BGR subs.gui.vars.BUT_BGR
#: import SLIDER_ORANGE subs.gui.vars.SLIDER_ORANGE
#: import GRAPH_BACKGROUND subs.gui.vars.GRAPH_BACKGROUND
#: import MO_BGR subs.gui.vars.MO_BGR
#: import PLUS_GREEN subs.gui.vars.PLUS_GREEN
#: import MINUS_RED subs.gui.vars.MINUS_RED
#: import BACKBLACK subs.gui.vars.BACKBLACK
#: import BLUE subs.gui.vars.BLUE
#: import GREY subs.gui.vars.GREY
#: import YELLOW subs.gui.vars.YELLOW
#: import GREEN_BRIGHT subs.gui.vars.GREEN_BRIGHT
#: import GREEN_OK subs.gui.vars.GREEN_OK

# OTHER
#: import STIM_PAR_HEIGHT subs.gui.vars.STIM_PAR_HEIGHT
"""
)