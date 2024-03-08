"""
This class takes stim parameters and creates the stimulation protocol

Stimulation.chirp creates the stimulation protocol and saves
a series with the stims defined as [(on, off, amp), (on, off, amp), ..]
in self.protocol
also returns x and y to plot the stimulus and the number of pulses

"""
import numpy as np
import math
import random
import time

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, DictProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button

# used in kv builder, do not remove!
from subs.gui.widgets.graph import Graph
from subs.gui.buttons.TextIn import TIn

from kivy.app import App




kv_str = r"""
<Graph3@Graph>:

<SetTimeIn@TIn>:
    input_filter: lambda *x: x[0] if x[0] in "1234567890:." else ""
    par: ""

<SetIntMethod@DROPB>:
    size_hint: (.1, .07)
    text: 'method'
    par: ""

<StimPanel@FloatLayout>:
    id: stimpanel           
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.1, 0.8
        Rectangle:
            pos: self.pos
            size: self.size

    Graph3:
        id: stim_graph
        size_hint: 0.7, 0.42
        pos_hint: {'x': 0.07, 'top': 0.5}          # relative sizes 0-1

    StdButton:
        id: createstim
        size_hint: 0.2, 0.1
        pos_hint: {'x': 0.8, 'top': 0.25}
        text: 'Create Stimulus'
        on_release:
            root.create_stim()

    StdButton:
        id: closepanel
        size_hint: 0.2, 0.1
        pos_hint: {'x': 0.8, 'top': 0.15}
        text: 'Close Panel'
        on_release:
            root.close_panel()

    setLab:
        pos_hint: {'right': 0.25, 'top': STIM_PAR_HEIGHT-0.05}
        text: 'Start:'

    setLab:
        pos_hint: {'right': 0.35, 'top': STIM_PAR_HEIGHT-0.05}
        text: 'End:'

    setLab:
        pos_hint: {'right': 0.15, 'top': STIM_PAR_HEIGHT - 0.1}
        text: 'Pulse:'

    SetTimeIn:
        id: startStim
        pos_hint: {'right': 0.25, 'top': STIM_PAR_HEIGHT - 0.1} #relative sizes 0-1
        par: 'stim_Strt_T'
        text: self.time_IO(root.stim_control.stim_pars[self.par])
        on_focus:
            self.focusaction(root.setstimpar, self.par, self.time_IO(self.text))

    SetTimeIn:
        id: endStim
        pos_hint: {'right': 0.35, 'top': STIM_PAR_HEIGHT - 0.1} #relative sizes 0-1
        par: 'stim_End_T'
        text: self.time_IO(root.stim_control.stim_pars[self.par])
        on_focus:
            self.focusaction(root.setstimpar, self.par, self.time_IO(self.text))

    SetIntMethod:
        id: linlog_on
        pos_hint: {'right': 0.45, 'top': STIM_PAR_HEIGHT - 0.1}
        par: 'stim_method'
        text: root.stim_control.stim_pars[self.par]#
        types: root.stim_control.int_methods
        on_text:
            root.stim_control.stim_pars[self.par] = self.text


    setLab:
        pos_hint: {'right': 0.15, 'top': STIM_PAR_HEIGHT - 0.2}
        text: 'Interval:'

    SetTimeIn:
        id: startInt
        pos_hint: {'right': 0.25, 'top': STIM_PAR_HEIGHT-0.2} #relative sizes 0-1
        par: 'int_Strt_T'
        text: self.time_IO(root.stim_control.stim_pars[self.par])
        on_focus:
            self.focusaction(root.setstimpar, self.par, self.time_IO(self.text))

    SetTimeIn:
        id: endInt
        pos_hint: {'right': 0.35, 'top': STIM_PAR_HEIGHT-0.2} #relative sizes 0-1
        par: 'int_End_T'
        text: self.time_IO(root.stim_control.stim_pars[self.par])
        on_focus:
            self.focusaction(root.setstimpar, self.par, self.time_IO(self.text))


    SetIntMethod:
        id: linlog_off
        pos_hint: {'right': 0.45, 'top': STIM_PAR_HEIGHT - 0.2}
        par: 'int_method'
        text: root.stim_control.stim_pars[self.par]
        types: root.stim_control.int_methods
        on_text:
            root.stim_control.stim_pars[self.par] = self.text


    setLab:
        pos_hint: {'right': 0.15, 'top': STIM_PAR_HEIGHT - 0.3}
        text: 'Power:'

    SetTimeIn:
        id: startamp
        pos_hint: {'right': 0.25, 'top': STIM_PAR_HEIGHT - 0.3} #relative sizes 0-1
        text: "{}%".format(abs(root.stim_control.stim_pars["amp_Strt"]))
        input_filter: 'int'
        on_focus:
            self.focusaction(root.setstimpar, 'amp_Strt', self.text.replace("%", ""))

    SetTimeIn:
        id: endamp
        pos_hint: {'right': 0.35, 'top': STIM_PAR_HEIGHT - 0.3} #relative['lin', 'log']
        text: "{}%".format(abs(root.stim_control.stim_pars["amp_End"]))
        input_filter: 'int'
        on_focus:
            self.focusaction(root.setstimpar, 'amp_End', self.text.replace("%", ""))
    
    SetIntMethod:
        id: linlog_amp
        pos_hint: {'right': 0.45, 'top': STIM_PAR_HEIGHT - 0.3}
        types: root.stim_control.int_methods
        par: 'amp_method'
        text: root.stim_control.stim_pars[self.par]
        on_text:
            root.stim_control.stim_pars[self.par] = self.text
    
    setLab:
        pos_hint: {'right': 0.6, 'top': STIM_PAR_HEIGHT - 0.2}
        text: 'Duration:'

    TIn:
        id: durationbox
        pos_hint: {'right': 0.7, 'top': STIM_PAR_HEIGHT - 0.2} #relative sizes 0-1
        text: self.time_IO(root.stim_control.stim_pars['duration'])
        input_filter: lambda *x: x[0] if x[0] in "1234567890:." else ""
        readonly: True
        on_focus: setattr(self, 'focus', False)
        background_color: self.background_color[:3] + [0.1]

    setLab:
        pos_hint: {'right': 0.6, 'top': STIM_PAR_HEIGHT - 0.3}
        text: 'Pulses:'

    TIn:
        id: n_pulsebox
        pos_hint: {'right': 0.7, 'top': STIM_PAR_HEIGHT-0.3} #relative sizes 0-1
        text: str(root.stim_control.stim_pars['n_pulse'])
        input_filter: 'int'
        on_focus:
            self.focusaction(root.setstimpar, 'n_pulse', min(abs(int(self.text)), 0xFFFF))

<StimWidget>:
    rows: 1
    size: root.size
    id: stimwidget
"""

# LEGACY

# class Stimulation():
#     protocol = []

#     def __init__(self):
#         # create standard stim
#         self.chirp(duration=10)

#     def chirp(self,
#               stim_Strt_T=1,
#               stim_End_T=0.5,
#               stim_method='lin',
#               int_Strt_T=0.5,
#               int_End_T=0.5,
#               int_method='lin',
#               amp_Strt=1,
#               amp_End=2,
#               amp_method='lin',
#               duration=-1,
#               n_pulse=5,
#               offset=0,
#               **kwargs):

#         def create_series(start, stop, steps, method):
#             # creaetes lin or log range for stims
#             # method can be lin or log
#             create_series = np.geomspace if method == 'log' else np.linspace
#             series = create_series(start, stop, int(steps))
#             return series

#         temp_list = [stim_Strt_T, stim_End_T,
#                      int_Strt_T, int_End_T, amp_Strt, amp_End]
#         for i in range(len(temp_list)):
#             if temp_list[i] <= 0:
#                 temp_list[i] = 0.001

#         # calculate n_pulses to get stim of duration time
#         if duration > 0:
#             # formula: n_pulses = duration / (mean_stim_time + mean_int_time)
#             if 'log' not in [stim_method, int_method]:
#                 stim_meanT = (stim_Strt_T + stim_End_T) / 2
#                 int_meanT = (int_Strt_T + int_End_T) / 2
#                 n_pulse = duration / (stim_meanT + int_meanT)
#                 n_pulse = int(n_pulse)
#                 if n_pulse <= 1:
#                     n_pulse = 1

#             # if log 'Brute force' calc duration
#             else:
#                 n_pulse = 0
#                 on, off = [], []
#                 while sum(off) + sum(on) < duration:
#                     n_pulse += 1
#                     int_range = (int_Strt_T, int_End_T, n_pulse, int_method)
#                     stm_range = (stim_Strt_T, stim_End_T,
#                                  n_pulse + 1, stim_method)
#                     on, off = map(lambda x: create_series(*x),
#                                   [int_range, stm_range])

#         # - 1 n_pulse for amp and interal for first pulse (at on 0 added later)
#         int_range = (int_Strt_T, int_End_T, n_pulse - 1, int_method)
#         stm_range = (stim_Strt_T, stim_End_T, n_pulse, stim_method)
#         amp_range = (amp_Strt, amp_End, n_pulse, amp_method)
#         on, off, amp = map(lambda x: create_series(*x),
#                            [int_range, stm_range, amp_range])

#         # let stim start at offset
#         on = np.append([offset], on)

#         # create wave for plotting and correct times
#         wave = np.empty(on.size + off.size)
#         wave[0::2] = on
#         wave[1::2] = off
#         for i in range(1, len(wave)):
#             wave[i] += wave[i - 1]
#         on, off = wave[0::2], wave[1::2]
#         self.protocol = list(zip(on, off, amp))

#         wave = [item for item in wave for i in range(2)]
#         wave_amp = []
#         [wave_amp.extend([0, i, i, 0]) for i in amp]

#         return (np.array(wave), np.array(wave_amp)), n_pulse


# NEW

class StimGenerator():
    def __init__(self) -> None:
        self.int_methods = {
            'lin': self.linear_interpolate,
            'exp': self.exponential_interpolate,
            'log': self.logarithmic_interpolate,
            'random': self.random_interpolate,
        }  # avaiable interpolation methods

    def _create_stim(self,
                     stim_Strt_T=1,
                     stim_End_T=10,
                     stim_method='lin',
                     int_Strt_T=10,
                     int_End_T=1,
                     int_method='lin',
                     amp_Strt=0,
                     amp_End=100,
                     amp_method='lin',
                     n_pulse=10,
                     **kwargs) -> tuple:
        """
        Creates a callable that yields the next stimulation step.

        Args:
            stim_Strt_T (float): Start time of the stimulation (in seconds).
            stim_End_T (float): End time of the stimulation (in seconds).
            stim_method (str): Method for generating the stimulation time steps 
                               ('lin', 'exp', 'log', or 'random').
            int_Strt_T (float): Start time of the inter-stimulus interval (in seconds).
            int_End_T (float): End time of the inter-stimulus interval (in seconds).
            int_method (str): Method for generating the inter-stimulus interval 
                              time steps ('lin', 'exp', 'log', or 'random').
            amp_Strt (float): Start amplitude of the stimulation (between 0 and 1).
            amp_End (float): End amplitude of the stimulation (between 0 and 1).
            amp_method (str): Method for generating the amplitude steps 
                              ('lin', 'exp', 'log', or 'random').
            n_pulse (int): Number of pulses in the stimulation sequence.

        Returns:
            tuple: (on time, off time, amplitude).

        """

        if (err := {stim_method, int_method, amp_method}.difference(self.int_methods)):
            raise ValueError(
                f"Invalid method(s): {', '.join(err)}. "
                "Available methods are 'lin', 'exp', 'log', and 'random'.")

        if n_pulse <= 2:
            # do not interpolate if 1 or 2 pulses -> no way steps inbetween
            n_pulse = max(1, n_pulse)
            on_time = (i for i in (stim_Strt_T, stim_End_T))
            off_time = (i for i in (int_Strt_T, int_End_T))
            amp = (i for i in (amp_Strt, amp_End))

        else:
            # create interpolated generators from start to end
            on_time = self.int_methods[stim_method](
                stim_Strt_T, stim_End_T, n_pulse)
            off_time = self.int_methods[int_method](int_Strt_T, int_End_T, n_pulse - 1)
            amp = self.int_methods[amp_method](amp_Strt, amp_End, n_pulse)

        # Combine into generator that generates pulse
        for i in range(n_pulse):               
            yield (next(on_time), (next(off_time) if i < n_pulse - 1 else 0), next(amp))

    def linear_interpolate(self, start_value, end_value, num_steps):
        step_size = (end_value - start_value) / (num_steps - 1)
        for i in range(num_steps):
            yield start_value + (step_size * i)

    def exponential_interpolate(self, start_value, end_value, num_steps):
        ratio = end_value / start_value
        exponent = math.pow(ratio, 1 / (num_steps - 1))
        for i in range(num_steps):
            yield start_value * math.pow(exponent, i)

    def logarithmic_interpolate(self, start_value, end_value, num_steps):
        ratio = math.log(end_value / start_value)
        increment = ratio / (num_steps - 1)
        for i in range(num_steps):
            yield start_value * math.exp(increment * i)

    def random_interpolate(self, start_value, end_value, num_steps):
        for _ in range(num_steps):
            yield random.uniform(start_value, end_value)

    def calc_duration(self, 
                      stim_Strt_T=1,
                      stim_End_T=10,
                      stim_method='lin',
                      int_Strt_T=10,
                      int_End_T=1,
                      int_method='lin', 
                      n_pulse=0, 
                      **kwargs) -> float:
        if n_pulse <= 2:
            # do not interpolate if 1 or 2 pulses -> no way steps inbetween
            n_pulse = max(1, n_pulse)
            on_time = sum(i for i in (stim_Strt_T, stim_End_T))
            off_time = sum(i for i in (int_Strt_T, int_End_T))
        else:
            on_time = sum(self.int_methods[stim_method](stim_Strt_T, stim_End_T, n_pulse))
            off_time = sum(self.int_methods[int_method](int_Strt_T, int_End_T, n_pulse - 1))
        return on_time + off_time
    
    def create_wave(self, 
                    **stim_pars):
        """
        Generates a waveform as a numpy array with x and y values for plotting block pulses.

        Args:
            wave_generator (generator): A generator that yields tuples representing stimulation steps,
                                    with each tuple containing (on time, off time, amplitude).

        Returns:
            numpy.ndarray: A numpy array with x and y values representing the waveform.

        """
        wave_generator = self._create_stim(**stim_pars)
        pulse = np.fromiter(wave_generator, dtype=[('on', '<f4'), ('off', '<f4'), ('amp', '<f4')])

        num_steps = pulse.shape[0]
        wave_out = np.zeros(num_steps * 4, dtype=[('x', 'f'), ('y', 'f')])

        t = np.zeros((num_steps * 2) + 1)  # + 1 because start at 0
        t[1::2] = pulse['on']
        t[2::2] = pulse['off']
        wave_out['x'] = np.repeat(np.cumsum(t), 2)[:-2]  # skip last part to not plot last off time
        wave_out['y'][1::4] = pulse['amp'] # pulse goes to amp at start
        wave_out['y'][2::4] = pulse['amp'] # pulse stays at amp to finish
        
        wave_out['x'] -= time.localtime().tm_gmtoff  # start plot on 00:00

        return wave_out

class StimController(StimGenerator, EventDispatcher):
    run = BooleanProperty(False)
    stim_pars = DictProperty(dict(
            stim_Strt_T=1,
            stim_End_T=10,
            stim_method='lin',
            int_Strt_T=1,
            int_End_T=1,
            int_method='lin',
            amp_Strt=10,
            amp_End=100,
            amp_method='lin',
            n_pulse=10,
            duration=0,
        ))
    stim_finished = False
    
    def __init__(self,) -> None:
        Builder.load_string(kv_str)
        super().__init__()
        self.stim_generator = None
        self.last_stim = (None, None, None)
        self.next_stim_event = Clock.schedule_once(lambda *x: x, 0)
        self.create_stim()

    def create_stim(self, **stim_pars):
        self.stim_pars.update(stim_pars)
        self.stim_generator = self._create_stim(**self.stim_pars)
        self.last_stim = (None, None, None)
        self.stim_pars['duration'] = self.calc_duration(**self.stim_pars)
        self.wave = self.create_wave(**self.stim_pars)
        self.stim_finished = False

    def start_stim(self):
        if self.stim_generator is not None:
            self.run = True
            self.last_stim = (None, None, None)
            if self.stim_finished:
                # create new stim if stim is finished
                self.create_stim()
            self.do_next_stim()

    def do_next_stim(self, *args):
        if self.run and self.stim_generator:
            try:
                on_time, off_time, amp = self.last_stim = next(
                    self.stim_generator)
                next_stim_start = on_time + off_time
                self.next_stim_event = Clock.schedule_once(self.do_next_stim, next_stim_start)
                self.do_stim(int(1e3 * on_time), amp)

            except StopIteration:
                # end of stim protocol
                self.stop_stim()
                self.stim_finished = True
                return

    def stop_stim(self):
        self.next_stim_event.cancel()
        self.run = False
        self.do_stim(0, 0)

    def reset_stim(self):
        self.stop_stim()
        self.create_stim()

    def do_stim(self, duration, amp):
        """
        placeholder for function that is called when stim is created

        Args:
            duration (float): duration of stim in ms
            amp (float): amp of stim in %
        """
        print(f"stim for {duration} mili seconds, {amp}% amplitude")
    
    def get_panel(self, *args):
        stim_panel = StimPanel(self)
        return stim_panel

class StimPanel(FloatLayout):
    def __init__(self, stim_control, **kwargs):
        self.app = App.get_running_app()
        self.stimpars = stim_control.stim_pars
        self.stim_control = stim_control
        super().__init__(**kwargs)
        self.create_stim()
 
    def create_stim(self):
        self.stim_control.create_stim()
        print('create stim')
        self.ids['stim_graph'].plot(self.stim_control.wave)

    def setstimpar(self, key, value):
        if not value:
            return
        if isinstance(value, str):
            value = abs(float(value))
        self.stimpars[key] = value
    
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

    def close_panel(self, *args):
        self.parent.remove_widget(self)

if __name__ == "__main__":

    from kivy.app import App
    from subs.gui.buttons.Server_Button import Server_Button
    from subs.gui.buttons.DropDownB import DropDownB    
    class MyApp(App):
        def build(self):
            Builder.load_string(
r"""
#:set STIM_PAR_HEIGHT 0.9  # height of stimpar buttons
#:set MO (1,1,1,1)

<DROPB@DropDownB>: # general DropDown, set types to change (types: ['1','2'])
    id: selplot
    pos_hint: {'x': 0.2, 'top': 0.8}
    text: 'Menu'
    size_hint: 0.1, 0.05
    halign: 'center'

<StdButton@Server_Button>:                                                             # settings for all buttons
    font_size: '15sp'
    size_hint: 0.1, 0.1  # relative size
    halign: 'center'
    valign: 'center'
    markup: True
    idName: None   # save id name in here for triggering later
    send_nw: False  # can be set to false to disable sending for specific buttons

<TIn>:
    size_hint: (.1, .07)
    text_size: self.size
    multiline: False
    foreground_color: 1,1,1,1
    background_color: 0.2,0.2,0.2,0.9
    font_size: '15sp'
    base_direction: 'rtl'
    halign: 'right'
    valign: 'middle'
    use_bubble: True

<setLab@Label>:
    # labels for stimulation and settings
    pos_hint: {'right': 0.8, 'top': 0.62} #relative sizes 0-1
    halign: 'right'
    size_hint: 0.1, 0.05
    text: 'LABEL'
    font_size: '15sp'
    color: (1,1,1,1)
"""
)
            return StimWidget()

    app = MyApp()
    app.run()