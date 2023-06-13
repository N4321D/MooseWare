"""
This class takes stim parameters and creates the stimulation protocol

Stimulation.chirp creates the stimulation protocol and saves
a series with the stims defined as [(on, off, amp), (on, off, amp), ..]
in self.protocol
also returns x and y to plot the stimulus and the number of pulses

"""
import numpy as np


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

s = Stimulation()
s.protocol
