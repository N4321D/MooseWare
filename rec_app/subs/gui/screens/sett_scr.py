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
    cls_name = "SETTINGS SCREEN"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here


kv_str = """
#:kivy 1.10.1

# SET SCREEN & BUTTONS
<Graph3@Graph>:

<Set@Widget>:

<STT@FloatLayout>:  # Subpages for settings screen
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.1, 0.7
        Rectangle:
            pos: self.pos
            size: self.size

# OTHER
<but2x1>:
    # buttons on bottom of set screen
    # toggle button has group and only one button can be down (=pressed)
    color: WHITE if self.state == 'down' else MO
    background_color: MO_BGR if self.state == 'down' else BUT_BGR
    background_down: 'atlas://data/images/defaulttheme/button' # default background
    font_size: '20sp'
    size_hint: 0.2, 0.1
    halign: 'center'
    group: 'menu'

<SetScreen>:
    on_enter: 
        self.selectscreen(self.last_screen)
    
    on_leave:
        fm.main_loop_event.cancel() # stop refreshing file manager

    StdButton:
        id: appsettings_button
        size_hint: 0.2, 0.1
        font_size: "20sp"
        pos_hint: {'x': 0.0, 'top': 0.1} #relative sizes 0-1
        text: 'App Settings'
        on_release: app.open_settings()

    but2x1:
        id: filebutt
        pos_hint: {'x': 0.2, 'top': 0.1} #relative sizes 0-1
        text: 'File'
        state: 'down'
        on_release: root.selectscreen('filesettings')

    but2x1:
        id: miscbutt
        pos_hint: {'x': 0.4, 'top': 0.1} #relative sizes 0-1
        text: ''
        # on_release: root.selectscreen('miscsettings')

    but2x1:
        id: emptybut
        pos_hint: {'x': 0.6, 'top': 0.1} #relative sizes 0-1
        text: ''
        # on_release: root.selectscreen('filesettings')

    but2x1:
        id: secretbutt
        pos_hint: {'x': 0.8, 'top': 0.1} #relative sizes 0-1
        text: 'ADMIN' if app.ADMIN else ''
        on_release: 
            root.selectscreen('secretsettings') if app.ADMIN else 1 # root.selectscreen('sensorsettings')
        # disabled: not app.ADMIN
    


    # FILE SETTINGS FOR SAVING ETC
    Set:
        STT:
            id: filesettings
            size: root.size[0], 0.9 * root.size[1]
            pos: root.pos[0],  root.pos[1] + 1.1 * root.size[1]

            Label:
                id: fc_label
                pos_hint: {'right': 1, 'top': 1}
                text: ''
                color: WHITE

            FileManager:
                id: fm
                pos_hint: {'right': 1, 'top': 1}

    # MISC SETTINGS
    Set:
        STT:
            id: miscsettings
            size: root.size[0], 0.9 * root.size[1]
            pos: root.pos[0],  root.pos[1] + 1.1 * root.size[1]


    # Secret Settings    
    Set:
        STT:
            # SECRET SETTINGS (SET ADMIN TO TRUE IN MAIN.PY to enable)
            # used to directly access sensors etc
            id: secretsettings
            size: root.size[0], 0.9 * root.size[1]
            pos: root.pos[0],  root.pos[1] + 1.1 * root.size[1]

            TIn:
                id: testin
                pos_hint: {'right': 0.5, 'top': 0.5} #relative sizes 0-1
                text: str(0)
                #input_filter: 'float'
                on_focus:
                    # self.focusaction(setattr, root, 'testvar', float(self.text))

            StdButton:
                pos_hint: {'right': 0.8, 'top': 0.2}
                text: 'TEST '
                on_release:
                    root.manager.get_screen("scrsav").dim_screen(0, 255, 4)

              # READ WRITE BYTES
            DROPB:
                id: sensselect
                pos_hint: {'right': 0.2, 'top': 0.5} #relative sizes 0-1
                size_hint: (.2, .1)
                text: 'Sensor'
                types: list(app.IO.sensors.keys())
                on_text:
                    address.text = str(hex(app.IO.sensors[self.text].address))
                    root.add = str(hex(app.IO.sensors[self.text].address))
                    reset.text = 'Reset\\n' + 'Chip'
                    reset.color = WHITE
                    reset.background_color = MO_BGR

            StdButton:
                id: read_start
                pos_hint: {'right': 0.1, 'top': 0.4}
                text: 'Read'
                on_release:
                    root.rwbyte('read', root.add, root.rg)

            StdButton:
                id: write_start
                pos_hint: {'right': 0.2, 'top': 0.4}
                text: 'Write'
                on_release:
                    root.rwbyte('write', root.add, root.rg, root.bt)

            StdButton:
                id: reset
                pos_hint: {'right': 0.1, 'top': 0.3}
                text: 'Force\\nReset'
                color: GREY
                on_release:
                    key = self.text[self.text.index('\\n') + 1:]
                    if key in app.IO.sensors: app.IO.sensors[key].reset()

            TIn:
                id: address
                pos_hint: {'right': 0.1, 'top': 0.8} #relative sizes 0-1
                hint_text: 'ADDRESS'
                # input_filter: 'int'
                on_focus:
                    self.focusaction(exec, 'self.parent.add = self.text')

            TIn:
                id: register
                pos_hint: {'right': 0.1, 'top': 0.7} #relative sizes 0-1
                hint_text: 'REG'
                on_focus:
                    self.focusaction(exec, 'self.parent.rg = self.text')

            TIn:
                id: byte
                size_hint: (.1, .07)
                pos_hint: {'right': 0.1, 'top': 0.6} #relative sizes 0-1
                hint_text: 'BYTE'
                on_focus:
                    self.focusaction(exec, 'self.parent.bt = self.text')

"""

class but2x1(ToggleButton):    
    def _do_press(self):
        if self.state == "down":
            return
        else:
            return super()._do_press()


class SetScreen(Scr):
    add = StringProperty('')     # address to write bytes to
    rg = StringProperty('')      # register to write bytes to
    bt = StringProperty('')      # byte to 
    
    # parameters to create stimulation
    last_screen = "filesettings"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(kv_str)

        # Dictionary with link to sensors
        # self.rwi2c = self.app.IO.readwrite
        

    def selectscreen(self, screen):
        screens = ('filesettings',
                   'miscsettings', 'secretsettings')

        # TODO add widget as attributes and add and remove instead of moving out of screen
        for s in screens:
            if s == screen:
                # focus on screen
                self.ids[s].pos = self.pos[0], self.pos[1] + 0.1 * self.size[1]
                if screen == "filesettings":
                    # activate main loop
                    self.ids.fm.main_loop_event()
                else:
                    # stop refreshing file manager
                    self.ids.fm.main_loop_event.cancel()

            else:
                # unfocus screen
                self.ids[s].pos = self.pos[0], self.pos[1] + 1.1 * self.size[1]
                            
        self.last_screen = screen


    def rwbyte(self, mode, address, reg, *args):
        if mode == 'read':
            _go = reg != '0X' and address != '0X' and 'SENT' not in args
        else:
            _go = address != '0X' and reg != '0X'

        if _go and not self.app.IO.recording:        # dont process if no input
            try:
                address = int(address, 16)
                reg = int(reg, 16)
                if mode == 'read':
                    response = self.rwi2c.readbyte(reg, address)
                    self.ids['byte'].text = str(hex(response))

                else:
                    for byte in args:
                        byte = int(byte, 16)
                        self.rwi2c.writebyte(reg, address, byte)
                        self.ids['byte'].text = 'SENT'

            except OSError:
                self.ids['byte'].text = 'ERROR'
                log(f'Error {mode[0:4]}ing: chip or register not found', 'info')

            except ValueError:
                pass

        else:
            self.ids['byte'].text = '!REC ON!'
            log(f'Error {mode[0:4]}ing: Stop Recording first', 'info')

