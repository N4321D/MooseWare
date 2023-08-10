"""
Recording screen


NB: Kv String cannot contain \n -> must be \\n

"""


from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import BooleanProperty, ConfigParserProperty

from subs.gui.vars import *
from subs.gui.screens.scr import Scr

from subs.autostimulator import AutoStimPanel

# used in kv lang, do not remove
from subs.gui.widgets.chips_widget import ChipWidget
from subs.gui.widgets.Graph import Graph

from functools import partial

import re

# Logger
from subs.log import create_logger
logger = create_logger()
def log(message, level="info"):
    cls_name = "REC SCREEN"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here


kv_str = """
<Graph1@Graph>:
<Graph2@Graph>:

<RecScreen>:
    on_enter:
        self.main()      # launch sensor test when starting every second
        if not app.IO.plotting: root.plotonoff()

    on_leave:
        self.main(stop=True)
        if app.IO.plotting: root.plotonoff()

    on_touch_down:
        if app.IO.plotting and app.IO.running: self.plotonoff(auto=True)
    
    ChipWidget:
        id: chip_widget
        size_hint: 0.9, 0.1
        pos_hint: {'x': 0, 'top': 1}
        orientation: "horizontal"

    StdButton:
        id: startbutt
        font_size: '20sp'
        pos_hint: {'x': 0.9, 'top': 0.1} #relative sizes 0-1
        background_color: MO_BGR if app.IO.running else BUT_BGR
        color: WHITE if app.IO.running else MO
        text: 'STOP' if app.IO.running else 'START'
        on_release:
            root.start_stop()
    
    DROPB:
        id: microbutt
        drop_but_font_size: '15sp'          # must be before types and text
        drop_but_size: '48sp'         # size of drop down buttons 
        font_size: '15sp'
        pos_hint: {'x': 0.7, 'top': 0.1}
        size_hint: (.2, .1)
        text: app.IO.plot_micro
        types: ['Internal', *app.IO.micro_controllers]
        text_size: self.size
        color: WHITE # if app.IO.plot_micro != "Internal" else MO
        background_color: MO_BGR # if app.IO.plot_micro != "Internal" else BUT_BGR
        halign: "center"
        valign: "center"
        on_text:
            root.toggle_micro(self.text)
        on_types:
            root.micro_disconnect(self.text)


    Label:
        id: recf
        pos_hint: {'right': 0.99, 'top': 1}
        size_hint: 0.08, 0.05
        text: '{} ({:.0f}) Hz.'.format(app.IO.rec_pars['samplerate'], app.IO.rec_pars['emarate'])
        font_size: '10sp'
        color: 0.5, 0.5, 0.5, 0.9
        halign: 'right'
        size: self.texture_size  # prevents label from turning black if too much text


    Label:
        id: plotting
        pos_hint: {'right': 0.99, 'top': 0.97}
        size_hint: 0.05, 0.05
        text: "Live" if app.IO.running else "Stopped"
        font_size: '10sp'
        color: WHITE if app.IO.plotting and app.IO.running else GREY
        halign: 'right'
        text_size: self.size

    # STIMBUTTONS
    StdButton:
        id: autostim
        pos_hint: {'right': 1, 'top': 0.5}
        text: 'Autostim:\\n{}'.format(root.autostim.status if app.IO.running else "Options")
        # disabled: not app.IO.running
        on_release:
            root.open_autostim()

    Label:
        id: stimstat_text
        size_hint: 0.1, 0.1
        pos_hint: {'right': 1, 'top': 0.63}
        font_size: '16sp' if self.text == '[i]last\\nstim[/i]' else '14sp'
        text: '[i]last\\nstim[/i]'
        color: WHITE if app.IO.sensor_status.get("OIS:status", (0, ))[0] > 1 else GREY
        halign: 'center' if self.text == '[i]last\\nstim[/i]' else 'right'
        markup: True
    
    StdButton:
        id: bluebutt
        font_size: '16sp'
        pos_hint: {'right': 1, 'top': 0.8}
        size_hint: 0.2, 0.1
        text: "STOP\\nSTIMS"
        color: WHITE
        background_color: MO_BGR
        on_release:
            app.IO.stop_all_stims()


    # TIME RANGE
    PlusButton:
        id: plottimeup
        pos_hint: {'right': 0.8, 'top': 0.5} #relative sizes 0-1
        on_release: root.plusminbut('time', 'up')
        send_nw: False


    MinusButton:
        id: plottimedown
        pos_hint: {'right': 0.8, 'top': 0.4} #relative sizes 0-1
        on_release: root.plusminbut('time', 'down')
        send_nw: False

    Label:
        id: plttimelabel
        pos_hint: {'right': 0.8, 'top': 0.65} #relative sizes 0-1
        size_hint: 0.1, 0.05
        text: 'Time'
        font_size: '15sp'
        color: WHITE

    TIn:
        id: plottimein
        pos_hint: {'right': 0.8, 'top': 0.6} #relative sizes 0-1
        size_hint: 0.1, 0.07
        font_size: '18sp'
        hint_text: self.time_IO(app.IO.secondsback)
        text: self.time_IO(app.IO.secondsback)
        input_filter: lambda *x: x[0] if x[0] in "1234567890:" else ""
        send_nw: False
        on_focus:
            self.focusaction(root.plusminbut,'time', self.time_IO(self.text))


    # ZOOM
    PlusButton:
        id: zoomup
        pos_hint: {'right': 0.9, 'top': 0.5} #relative sizes 0-1
        on_release: root.plusminbut('zoom', 'up')
        send_nw: False

    MinusButton:
        id: zoomdown
        pos_hint: {'right': 0.9, 'top': 0.4} #relative sizes 0-1
        on_release: root.plusminbut('zoom', 'down')
        send_nw: False

    Label:
        id: yzoombox
        pos_hint: {'right': 0.9, 'top': 0.65} #relative sizes 0-1
        size_hint: 0.1, 0.05
        text: 'Zoom'
        font_size: '15sp'
        color: WHITE

    TIn:
        id: yzoomin
        pos_hint: {'right': 0.9, 'top': 0.6} #relative sizes 0-1
        size_hint: 0.1, 0.07
        hint_text: 'auto'
        text: 'auto'
        input_filter: 'int'
        font_size: '18sp'
        suffix: '%'
        send_nw: False
        on_focus:
            self.focusaction(root.plusminbut, 'zoom', self.text)

    Graph1:
        id: graf1
        size_hint: 0.6,0.38
        pos_hint: {'x': 0.07, 'top': 0.88}
        skipnan: False

    Graph2:
        id: graf2
        size_hint: 0.6,0.38
        pos_hint: {'x': 0.07, 'top': 0.43}
        skipnan: False

    SPLOT:
        id: splot1
        pos_hint: {'x': 0.07, 'top': 0.88}
        types: app.IO.choices
        text: self.types[0] if len(self.types) > 1 else 'Not Connected'

    SPLOT:
        id: splot2
        pos_hint: {'x': 0.07, 'top': 0.428}
        types: app.IO.choices
        text: self.types[1] if len(self.types) > 2 else 'Not Connected'

"""

class RecScreen(Scr):
    plotting = BooleanProperty(True)  # data being plotted or not
    Button = None                     # placeholder for hardware led button

    # range and steps
    # each key is min and max of the range and the value is the steps
    steps = {'time': {(0, 15): 5, (15, 60): 30,
                      (60, 300): 60, 
                      (300, 900): 300, 
                      (900, 3600): 900,
                      (3600, float('inf')): 3600},
             'zoom': {(0, 100): 25, (100, 500): 50, (500, 2000): 250, (2000, 10000): 1000},
             'ledma': {(0, 10): 1, (10, 20): 2, (20, 100): 10},
             }
    
    nudging = False                 # indicates if wake up stim is running
    autostim = None                 # placeholder for autostim
    autostim_pan = None             # placeholder for autostim panel

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        Builder.load_string(kv_str)

        self.autostim_pan = AutoStimPanel(setup_autostim=self.setup_autostim)
        self.autostim = self.autostim_pan.autostim
        self.autostim.wake_up_out = self.wake_up

        self.graph1 = []            # list with [par, graph, kwargs]
        self.graph2 = []             # list with [par, graph, kwargs]
      
        self.event = Clock.schedule_once(self.main, 0.5)
        self.plotonoff_event = Clock.schedule_once(self.plotonoff, 0)
        
        # hardware button
        self.Button = self.app.Button
        self.Button.on_press = self.button_press
        self.Button.on_release = self.button_release
    
        self.app.IO.bind(sensor_status=self.ois_updates)
        self.app.IO.bind(plot_micro=lambda *x: setattr(self.ids['microbutt'], 'text', 
                                                       self.app.IO.plot_micro))

        Clock.schedule_once(self.__kv_init__, 0)
    
    def __kv_init__(self, *_):
        """
        init to run when kivy app is built
        """
        self.app.root.bind(UTC=lambda *_: self.toggle_utc(self.app.root.UTC))
        self.Button.start_detection()
        return

    def main(self, *args, stop=False):
        if stop:
            return self.event.cancel()

        if not self.graph1:
            self.graph1 = [self.ids['splot1'].text, self.ids['graf1'],
                           {'zoom': True}]
            self.app.IO.graphs = (self.graph1, self.graph2)

        if not self.graph2:
            self.graph2 = [self.ids['splot2'].text, self.ids['graf2'],
                           {'showoff': False}]
            self.app.IO.graphs = (self.graph1, self.graph2)

        if self.graph1[0] != self.ids['splot1'].text:
            self.graph1[0] = self.ids['splot1'].text
            self.app.IO.graphs = (self.graph1, self.graph2)

        if self.graph2[0] != self.ids['splot2'].text:
            self.graph2[0] = self.ids['splot2'].text
            self.app.IO.graphs = (self.graph1, self.graph2)
                
        return self.event()

    def plusminbut(self, func, inp):
        """
        this function controls +/- button behaviour

        if input is "up" or "down" the step size is extracted
        from the self.steps dict.
        else the value of the input is set to the variable
        """
        step = 0            # step size of the increase/decrease

        # if button up or down pressed:        
        if inp == "up" or inp == "down":
            # get value
            out = {'time': self.app.IO.secondsback,
                   'zoom': self.app.IO.yzoom,
                   'ledma': self.app.rec_vars.ois_ma
                   }[func]

            # find step size
            for key in self.steps[func]:
                if ((key[0] <= out < key[1] and inp == 'up') or
                        (key[0] < out <= key[1] and inp == 'down')):
                    step = self.steps[func][key]
                    break

            # stop if no value found
            if step == 0:
                return
            
            # out = out + step if inp == 'up' else out - step
            if inp == "up":
                out = (out + step) - (out%step) # round to nearst multiple of step
            else:
                out = out - (out%step or step) # round to nearst multiple of step
        
        
        # if value is entered
        else:
            try:
                out = round(float(inp))

            except (ValueError, TypeError):
                return

        if func == 'time':
            self.app.IO.secondsback = out

        if func == 'zoom':
            self.app.IO.yzoom = out
            if out == 0:
                self.ids['yzoomin'].text = 'auto'
            else:
                self.ids['yzoomin'].text = f'{self.app.IO.yzoom:.0f} %'

        if func == 'ledma':
            # limit mA within range:
            if out < 0:
                out = 0
            if out > 60:
                out = 60

            self.app.rec_vars.ois_ma = out
            if self.app.IO.running:
                self.app.IO.add_note(f'Green LED power (mA): {out}')
            self.app.IO.chip_command('OIS', 'ledcontrol', 'pulse', (out, out))

    def change_rec_name(self, name, *args):
        if (self.app.IO.running or not name
            or not isinstance(name, str)):
            return
        
        # filter characters which produce error in filename
        name = re.sub(r"\s", "_", name)     # replace spaces with underscore
        name = re.sub(r"\W", "", name)      # remove non-file safe characters
        self.app.IO.recording_name = name

    def start_stop(self):
        if not self.app.IO.running:
            self.app.IO.start_recording()
        else:
            self.app.IO.stop_recording()

    def plotonoff(self, *args, auto=False):
        # switch to turn plotting on or off
        self.app.IO.plotting = not self.app.IO.plotting

        # automatically turn on plotting if auto plot on off
        # (when touching screen)
        if auto:
            return self.plotonoff_event()

    def button_press(self, lastpresstime):
        if not self.nudging:
            self.app.IO.sensors['GPIO Interface'].set_gpio_pin(6, True)
        else:
            # stop wakeup protocol when pressing button
            self.autostim.stop_wakeup_prot()
            self.nudging = False

    def button_release(self, touch_duration, *args):
        if not self.nudging:
            self.app.IO.sensors['GPIO Interface'].set_gpio_pin(6, False)
            if self.app.IO.running:
                self.app.IO.add_note(f'Button Pressed for {touch_duration:.2f} seconds')

    def ois_updates(self, *args):
        _i = self.app.IO.sensor_status["OIS:status"][0]        
        # set stim counter
        if _i > 1:
            count = self.app.IO.sensor_status['OIS:stim_count'][0]
            if count > 0:
                ma = self.app.IO.sensor_status['OIS:last_stim_mA'][0]
                dur = round(self.app.IO.sensor_status['OIS:last_stim_dur'][0], 2)
                self.ids.stimstat_text.text = f"{count}\n{dur} s.\n{ma} mA"
            
    # Autostimulation
    def open_autostim(self,):
        # self.autostim_pan.open()
        try:
            self.add_widget(self.autostim_pan)
            
        except Exception as e:
            log(e, 'warning')



    def setup_autostim(self):
        # define what to do at stop and start
        # self.autostim.start_stim = partial(self._do_1_stim, reset=True)
        # self.autostim.stop_stim = self._stop_stim
        # self.autostim.continue_stim = self._do_1_stim
        # self.autostim.custom_protocol = self._start_stim_prot
        pass

    def wake_up(self, state):
        self.nudging = True
        if state is None:
            # indicate that nudging protocol is over
            self.nudging = False
        else:
            self.app.IO.sensors['GPIO Interface'].set_gpio_pin(6, state)
    
    def toggle_utc(self, utc, *_):
        """
        Toggles if the graf1 and graf2 widgets plot time in utc or local time.

        Parameters:
        - `utc` (BooleanProperty): The UTC value to be set for the graf1 and graf2 widgets.
        Returns:
        None
        """
        utc = bool(utc)
        self.ids['graf1'].utc = utc
        self.ids['graf2'].utc = utc

    def toggle_micro(self, micro):
        self.ids['chip_widget'].create_buttons()
        self.app.IO.toggle_micro(micro)

    def micro_disconnect(self, micro):
        if micro not in self.ids.microbutt.types: 
            self.toggle_micro(self.ids.microbutt.types[-1])