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

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty
from kivy.uix.gridlayout import GridLayout

kv_str = r"""
<StimWidget>:
    rows: 1
    size: root.size

    Button:
        text: "Create\nStim"
        on_release: root.stim_control.create_stim()

    Button:
        text: "Stop\nStim" if root.stim_control.run else "Start\nStim"
        on_release: root.stim_control.stop_stim() if root.stim_control.run else root.stim_control.start_stim()
    
    Button:
        text: "Reset\nStim"
        on_release: root.stim_control.reset_stim()
"""

class Stimulation():
    protocol = []

    def __init__(self):
        # create standard stim
        self.chirp(duration=10)

    def chirp(self,
              stim_Strt_T=1,
              stim_End_T=0.5,
              stim_method='lin',
              int_Strt_T=0.5,
              int_End_T=0.5,
              int_method='lin',
              amp_Strt=1,
              amp_End=2,
              amp_method='lin',
              duration=-1,
              n_pulse=5,
              offset=0,
              **kwargs):

        def create_series(start, stop, steps, method):
            # creaetes lin or log range for stims
            # method can be lin or log
            create_series = np.geomspace if method == 'log' else np.linspace
            series = create_series(start, stop, int(steps))
            return series

        temp_list = [stim_Strt_T, stim_End_T,
                     int_Strt_T, int_End_T, amp_Strt, amp_End]
        for i in range(len(temp_list)):
            if temp_list[i] <= 0:
                temp_list[i] = 0.001

        # calculate n_pulses to get stim of duration time
        if duration > 0:
            # formula: n_pulses = duration / (mean_stim_time + mean_int_time)
            if 'log' not in [stim_method, int_method]:
                stim_meanT = (stim_Strt_T + stim_End_T) / 2
                int_meanT = (int_Strt_T + int_End_T) / 2
                n_pulse = duration / (stim_meanT + int_meanT)
                n_pulse = int(n_pulse)
                if n_pulse <= 1:
                    n_pulse = 1

            # if log 'Brute force' calc duration
            else:
                n_pulse = 0
                on, off = [], []
                while sum(off) + sum(on) < duration:
                    n_pulse += 1
                    int_range = (int_Strt_T, int_End_T, n_pulse, int_method)
                    stm_range = (stim_Strt_T, stim_End_T,
                                 n_pulse + 1, stim_method)
                    on, off = map(lambda x: create_series(*x),
                                  [int_range, stm_range])

        # - 1 n_pulse for amp and interal for first pulse (at on 0 added later)
        int_range = (int_Strt_T, int_End_T, n_pulse - 1, int_method)
        stm_range = (stim_Strt_T, stim_End_T, n_pulse, stim_method)
        amp_range = (amp_Strt, amp_End, n_pulse, amp_method)
        on, off, amp = map(lambda x: create_series(*x),
                           [int_range, stm_range, amp_range])

        # let stim start at offset
        on = np.append([offset], on)

        # create wave for plotting and correct times
        wave = np.empty(on.size + off.size)
        wave[0::2] = on
        wave[1::2] = off
        for i in range(1, len(wave)):
            wave[i] += wave[i - 1]
        on, off = wave[0::2], wave[1::2]
        self.protocol = list(zip(on, off, amp))

        wave = [item for item in wave for i in range(2)]
        wave_amp = []
        [wave_amp.extend([0, i, i, 0]) for i in amp]

        return (np.array(wave), np.array(wave_amp)), n_pulse


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

        on_time = self.int_methods[stim_method](
            stim_Strt_T, stim_End_T, n_pulse)
        off_time = self.int_methods[int_method](int_Strt_T, int_End_T, n_pulse)
        amp = self.int_methods[amp_method](amp_Strt, amp_End, n_pulse)

        for i in range(n_pulse):
            yield (next(on_time), next(off_time), next(amp))

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
                      n_pulses=0, 
                      **kwargs) -> float:
        on_time = self.int_methods[stim_method](stim_Strt_T, stim_End_T, n_pulses)
        off_time = self.int_methods[int_method](int_Strt_T, int_End_T, n_pulses)
        return sum(on_time) + sum(off_time)


class StimController(StimGenerator, EventDispatcher):
    run = BooleanProperty(False)
    def __init__(self,) -> None:
        super().__init__()
        self.stim_generator = None
        self.last_stim = (None, None, None)
        self.stim_pars = dict(
            stim_Strt_T=1,
            stim_End_T=6,
            stim_method='lin',
            int_Strt_T=1,
            int_End_T=0.1,
            int_method='lin',
            amp_Strt=0,
            amp_End=100,
            amp_method='lin',
            n_pulse=10,
        )
        self.next_stim_event = Clock.schedule_once(lambda *x: x, 0)

    def create_stim(self, **stim_pars):
        self.stim_pars.update(stim_pars)
        self.stim_generator = self._create_stim(**self.stim_pars)
        self.last_stim = (None, None, None)
        self.duration = self.calc_duration(**self.stim_pars)

    def start_stim(self):
        if self.stim_generator is not None:
            self.run = True
            self.last_stim = (None, None, None)
            self.do_next_stim()

    def do_next_stim(self, *args):
        if self.run and self.stim_generator:
            try:
                on_time, off_time, amp = self.last_stim = next(
                    self.stim_generator)
                next_stim_start = on_time + off_time
                self.next_stim_event = Clock.schedule_once(self.do_next_stim, next_stim_start)
                self.do_stim(on_time, amp)

            except StopIteration:
                # end of stim protocol
                self.stop_stim()
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
            duration (float): duration of stim in seconds
            amp (float): amp of stim in %
        """
        print(f"stim for {duration} seconds, {amp}% amplitude")

class StimWidget(GridLayout):
    stim_control = StimController()

    def __init__(self, **kwargs) -> None:
        Builder.load_string(kv_str)
        super().__init__(**kwargs)



if __name__ == "__main__":
    from kivy.app import App
    
    class MyApp(App):
        def build(self):
            return StimWidget()

    app = MyApp()
    app.run()