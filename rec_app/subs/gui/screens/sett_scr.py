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
from subs.gui.widgets.Graph import Graph

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
        self.main_loop_event()
    
    on_leave:
        self.main_loop_event.cancel()
    
    on_leave:
        fm.main_loop_event.cancel() # stop refreshing file manager

    Label:     # crashes if not here

    StdButton:
        id: appsettings_button
        size_hint: 0.2, 0.1
        font_size: "20sp"
        pos_hint: {'x': 0.0, 'top': 0.1} #relative sizes 0-1
        text: 'App Settings'
        on_release: app.open_settings()  # root.selectscreen('senssettings')

    but2x1:
        id: stimbutt
        pos_hint: {'x': 0.2, 'top': 0.1} #relative sizes 0-1
        text: 'Stimulation'
        on_release: root.selectscreen('stimsettings')
        state: 'down'

    but2x1:
        id: filebutt
        pos_hint: {'x': 0.4, 'top': 0.1} #relative sizes 0-1
        text: 'File'
        on_release: root.selectscreen('filesettings')

    but2x1:
        id: miscbutt
        pos_hint: {'x': 0.6, 'top': 0.1} #relative sizes 0-1
        text: ''
        # on_release: root.selectscreen('miscsettings')

    but2x1:
        id: secretbutt
        pos_hint: {'x': 0.8, 'top': 0.1} #relative sizes 0-1
        text: 'ADMIN' if app.ADMIN else ''
        on_release: 
            root.selectscreen('secretsettings') if app.ADMIN else 1 # root.selectscreen('sensorsettings')
        # disabled: not app.ADMIN

    
    # STIMSETTINGS
    Set:
        STT:
            id: stimsettings
            size: root.size[0], 0.9 * root.size[1]
            pos: (root.pos[0],  root.pos[1] + 0.1 * root.size[1])

            Graph3:
                id: graf3
                size_hint: 0.7, 0.42
                pos_hint: {'x': 0.07, 'top': 0.5}          # relative sizes 0-1

            StdButton:
                id: createstim
                size_hint: 0.2, 0.1
                pos_hint: {'x': 0.8, 'top': 0.15}
                text: 'Create Stimulus'
                on_release:
                    root.createstim(True)

            #
            #   SET BUTTONS AND INPUTS TO CREATE STIMULUS
            #

            setLab:
                pos_hint: {'right': 0.25, 'top': STIM_PAR_HEIGHT-0.05}
                text: 'Start:'

            setLab:
                pos_hint: {'right': 0.35, 'top': STIM_PAR_HEIGHT-0.05}
                text: 'End:'

            setLab:
                pos_hint: {'right': 0.15, 'top': STIM_PAR_HEIGHT - 0.1}
                text: 'Pulse:'

            TIn:
                id: startStim
                pos_hint: {'right': 0.25, 'top': STIM_PAR_HEIGHT - 0.1} #relative sizes 0-1
                text: self.time_IO(root.stimpars['stim_Strt_T'])
                input_filter: 'float'
                input_filter: lambda *x: x[0] if x[0] in "1234567890:." else ""
                on_focus:
                    self.focusaction(root.setstimpar, 'stim_Strt_T', self.time_IO(self.text))

            TIn:
                id: endStim
                pos_hint: {'right': 0.35, 'top': STIM_PAR_HEIGHT - 0.1} #relative sizes 0-1
                text: self.time_IO(root.stimpars['stim_End_T'])
                input_filter: lambda *x: x[0] if x[0] in "1234567890:." else ""
                on_focus:
                    self.focusaction(root.setstimpar, 'stim_End_T', self.time_IO(self.text))

            DROPB:
                id: linlog_on
                pos_hint: {'right': 0.45, 'top': STIM_PAR_HEIGHT - 0.1}
                size_hint: (.1, .07)
                text: 'method'
                types: ['lin', 'log']
                on_text:
                    root.stimpars['stim_method'] = self.text

            setLab:
                pos_hint: {'right': 0.15, 'top': STIM_PAR_HEIGHT - 0.2}
                text: 'Interval:'

            TIn:
                id: startInt
                pos_hint: {'right': 0.25, 'top': STIM_PAR_HEIGHT-0.2} #relative sizes 0-1
                text: self.time_IO(root.stimpars['int_Strt_T'])
                input_filter: lambda *x: x[0] if x[0] in "1234567890:." else ""
                on_focus:
                    self.focusaction(root.setstimpar, 'int_Strt_T', self.time_IO(self.text))

            TIn:
                id: endInt
                pos_hint: {'right': 0.35, 'top': STIM_PAR_HEIGHT-0.2} #relative sizes 0-1
                text: self.time_IO(root.stimpars['int_End_T'])
                input_filter: lambda *x: x[0] if x[0] in "1234567890:." else ""
                on_focus:
                    self.focusaction(root.setstimpar, 'int_End_T', self.time_IO(self.text))

            DROPB:
                id: linlog_off
                pos_hint: {'right': 0.45, 'top': STIM_PAR_HEIGHT - 0.2}
                size_hint: (.1, .07)
                text: 'method'
                types: ['lin', 'log']
                on_text:
                    root.stimpars['int_method'] = self.text

            setLab:
                pos_hint: {'right': 0.15, 'top': STIM_PAR_HEIGHT - 0.3}
                text: 'Power:'

            TIn:
                id: startamp
                pos_hint: {'right': 0.25, 'top': STIM_PAR_HEIGHT - 0.3} #relative sizes 0-1
                text: '{:d} mA'.format(root.stimpars['amp_Strt'])
                input_filter: 'int'
                on_focus:
                    self.focusaction(root.setstimpar, 'amp_Strt', self.text)

            TIn:
                id: endamp
                pos_hint: {'right': 0.35, 'top': STIM_PAR_HEIGHT - 0.3} #relative sizes 0-1
                text: '{:d} mA'.format(root.stimpars['amp_End'])
                input_filter: 'int'
                on_focus:
                    self.focusaction(root.setstimpar, 'amp_End', self.text)

            DROPB:
                id: linlog_amp
                pos_hint: {'right': 0.45, 'top': STIM_PAR_HEIGHT - 0.3}
                size_hint: (.1, .07)
                text: 'method'
                types: ['lin', 'log']
                on_text:
                    root.stimpars['amp_method'] = self.text

            setLab:
                pos_hint: {'right': 0.6, 'top': STIM_PAR_HEIGHT - 0.2}
                text: 'Duration:'

            TIn:
                id: durationbox
                pos_hint: {'right': 0.7, 'top': STIM_PAR_HEIGHT - 0.2} #relative sizes 0-1
                text: self.time_IO(root.stimpars['duration']) if root.stimpars['duration'] > 0 else ''
                input_filter: lambda *x: x[0] if x[0] in "1234567890:." else ""
                on_focus:
                    self.focusaction(root.setstimpar, 'duration', self.time_IO(self.text))

            setLab:
                pos_hint: {'right': 0.6, 'top': STIM_PAR_HEIGHT - 0.3}
                text: 'Pulses:'

            TIn:
                id: n_pulsebox
                pos_hint: {'right': 0.7, 'top': STIM_PAR_HEIGHT-0.3} #relative sizes 0-1
                text: str(int(root.stimpars['n_pulse'])) if root.stimpars['n_pulse'] > 0 else ''
                input_filter: 'int'
                on_focus:
                    self.focusaction(root.setstimpar, 'n_pulse', self.text)

            setLab:
                pos_hint: {'right': 0.85, 'top': STIM_PAR_HEIGHT - 0.1}
                text: 'Delay:'


            TIn:
                id: delaybox
                pos_hint: {'right': 0.95, 'top': STIM_PAR_HEIGHT - 0.1} #relative sizes 0-1
                text: self.time_IO(root.stimpars['offset'])
                input_filter: lambda *x: x[0] if x[0] in "1234567890:." else ""
                on_focus:
                    self.focusaction(root.setstimpar, 'offset', self.time_IO(self.text))

            setLab:
                pos_hint: {'right': 0.85, 'top': STIM_PAR_HEIGHT - 0.2}
                text: 'Repeats:'

            TIn:
                id: repnbox
                pos_hint: {'right': 0.95, 'top': STIM_PAR_HEIGHT-0.2} #relative sizes 0-1
                text: str(root.stimpars['rep_n'])
                input_filter: 'int'
                on_focus:
                    self.focusaction(root.setstimpar, 'rep_n', self.text)

            setLab:
                pos_hint: {'right': 0.85, 'top': STIM_PAR_HEIGHT - 0.3}
                text: 'Rep. Int.:'

            TIn:
                id: repStim_box
                pos_hint: {'right': 0.95, 'top': STIM_PAR_HEIGHT - 0.3} #relative sizes 0-1
                text: (self.time_IO(root.stimpars['rep_s'])) if root.stimpars['rep_s'] > 0 else ''
                input_filter: lambda *x: x[0] if x[0] in "1234567890:." else ""
                on_focus:
                    self.focusaction(root.setstimpar, 'rep_s', self.time_IO(self.text))


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


            # # TIMEZONE
            # TzWidget:
            #     size_hint: (0.3, 0.1)
            #     pos_hint: {'x': 0.12, 'top': 0.45} #relative sizes 0-1
            #     disabled: app.SERVER
            # setLab:
            #     text: 'Change\\nTimezone:'
            #     pos_hint: {'right': 0.11, 'top': 0.45}
            #     disabled: app.SERVER
            
            # # WIFI
            # setLab:
            #     text: 'Network:'
            #     pos_hint: {'right': 0.69, 'top': 0.9}     
            #     disabled: app.SERVER
            
            # WifiWidget:
            #     id: wifi
            #     size_hint: (0.4, 0.4)
            #     pos_hint: {"x": 0.6, "y": 0.4}
            #     disabled: app.SERVER


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
                types: list(root.sensors.keys())
                on_text:
                    address.text = str(hex(root.sensors[self.text].address))
                    root.add = str(hex(root.sensors[self.text].address))
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
                    if key in root.sensors: root.sensors[key].reset()

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
    stimpars = DictProperty()   # this is the var used  _stimpars is only for saving settings
    _stimpars = ConfigParserProperty({'stim_Strt_T': 1,
                                      'stim_End_T': 10,
                                      'stim_method': 'lin',  # 'lin' or 'log'
                                      'int_Strt_T': 300,
                                      'int_End_T': 300,
                                      'int_method': 'lin',   # 'lin' or 'log'
                                      'amp_Strt': 30,
                                      'amp_End': 30,
                                      'amp_method': 'lin',   # 'lin' or 'log'
                                      'duration': -1,
                                      'n_pulse': 10,
                                      'offset': 0,
                                      'rep_s': -1,
                                      'rep_n': 1}, 
                                      "stimulation", "stimpars", "app_config",
                                      val_type=val_type_loader)  

    last_screen = "stimsettings"


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(kv_str)

        # build stimpars:
        self.stimpars.update(self._stimpars)  # load stimpars
        # save
        self.bind(stimpars=lambda *_: setattr(self, "_stimpars", 
                                               dict(self.stimpars)))

        # Dictionary with link to sensors
        self.sensors = {}
        self.rwi2c = self.app.IO.readwrite
        self.main_loop_event = Clock.schedule_interval(self.main_loop, 1)
        self.main_loop_event.cancel()

        Clock.schedule_once(self.__kv_init__, 0)
    
    def __kv_init__(self, dt):
        self.createstim(False)

    def main_loop(self, *args):
        pass

    def selectscreen(self, screen):
        screens = ('stimsettings', 'filesettings',
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

    def setstimpar(self, stimpar, value):
        try:
            value = min(0xFFFF, float(value))
            if value <= 0:
                return
        except (ValueError, TypeError):
            return

        if stimpar == 'duration' and value > 0:
            self.stimpars['n_pulse'] = -1

        elif stimpar == 'n_pulse' and value > 0:
            self.stimpars['duration'] = -1

        if 'amp' in stimpar or 'rep' in stimpar:
            value = int(value)

        self.stimpars[stimpar] = value

    def createstim(self, sending):
        self.app.stimstat = [0, 0, 0] # indicates new stim
        stim, npul = self.app.stim.chirp(**self.stimpars)
        if stim:
            self.ids['graf3'].plot_xy(stim[0] - time.localtime().tm_gmtoff,
                                      stim[1], linecolor=BLUE)

            if sending:
                # send to server/client
                self.app.IO.send(('VAR', ('settings', 'stimpars',
                                      dict(self.stimpars))))
                self.app.IO.send(('VAR', ('settings', 'createstim', False)))

            # return calculated stims / duration
            if self.stimpars['duration'] == -1:
                self.stimpars['duration'] == stim[0][-1]
                self.ids['durationbox'].text = self.ids['durationbox'].time_IO(
                                                    stim[0][-1])

            if self.stimpars['n_pulse'] == -1:
                self.stimpars['n_pulse'] == npul
                self.ids['n_pulsebox'].text = str(npul)

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

