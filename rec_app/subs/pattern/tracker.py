# -*- coding: utf-8 -*-
"""
Created on Fri Feb 7 16:25:52 2020

@author: Dmitri Yousef Yengej

This function will be used for autostimulation
it tracks the conditions / calculates the parameters
for autostimulation

dont change the class name or return format

anything can be used in the calc functions but beware
that if it becomes too slow it will affect the whole
system (gui might become unresponsive etc)

multiprocessing can be used to offload the system
for complexer calculations however the system has
few free cores available depending on the configuration


NOTE:
- data can include nans, be sure that functions here are able to
  deal with it!

- data consists of a Dictionary with as keys the recorded parameters (as found
  in the data files) and Values are np.arrays with the data

"""

# IMPORTS
import numpy as np
from bisect import bisect
# import time

from datetime import datetime, timedelta

class Tracker():
    """
    checks if pattern is in data
    use threshold to set threshold for confidence to
    that pattern is in data
    triggers stim if patter is in data
    """
    # DO NOT EDIT:

    # USER EDITABLE:
    shared_mem = {'start_window': None      # start of the dection window
                  }                         # Shared memory with watcher and success classes

    #       Input parameters (get buttons in autostim setup):
    pars = {"motion detection window": {"val": timedelta(seconds=300),
                                        "desc": "Window of time to determine if asleep or awake"},
            "motion ang. x threshold": {"val": 0.5, 
                                        "desc": "Threshold in mean motion to determine if awake"},
            "motion ang. x threshold mode": {"val": "absolute value",
                                             "desc": "threshold is absolute value or proportional to baseline or self",
                                             "options": ["absolute value", "relative to baseline", "relative to self"]},
            "ois signal threshold": {"val": 1.1,
                              "desc": "Threshold of OIS to be CSD"}, # threshold for CSD
            "ois signal threshold mode": {"val": "relative to baseline",
                                   "desc": "threshold is absolute value or proportional to baseline or self",
                                   "options": ["relative to baseline", "absolute value", "relative to self"]}, 
            "csd window": {"val": timedelta(minutes=2),
                           "desc": "Window to detect decrease in bloodflow"},
            "ois signal baseline window": {"val": timedelta(minutes=10),
                                    "desc": "Window to calculat baseline value over"},
            }

    parent = None                           # placeholder for parent class (autostim.py)

    # USER DEFINED:
    PARS_FROM_DATA = ['time', 'OIS Signal', 'Motion Ang. X']  # parameters to read from data

    def __init__(self, parent, shared_mem, pars, tracked_data, **kwargs):
        self.shared_mem = shared_mem
        pars.update({k:v for k, v in self.pars.items() if k not in pars})
        self.pars = pars
        self.tracked_data = tracked_data
        for k in kwargs:
            setattr(self, k, kwargs[k])
        self.parent = parent
        self._init()
    
    def get_data(self, seconds_back, par=...):
        """
        PLACEHOLDER
        get last recorded data upto x seconds back
        - seconds_back: time from last recorded data back to retrieve
        - par: specific parameter to retrieve, if not defined all 
               pars are returned
        """
        return

    def process(self):
        """
        Calculates and updates the status of the animal based on its data.
                
        Notes:
            - This method is an essential method and its name and output type should not be changed.
            - The method first determines the maximum time of the `timedelta` values in the `self.pars` dictionary.
            - It then calls the `self.get_data` method with the maximum time and `self.PARS_FROM_DATA` as arguments
            to obtain the data.
            - Finally, it calls the `self._calc` method with the obtained data to calculate and update the status
            of the animal.
        """
        # ESSENTIAL METHOD, DO NOT CHANGE NAME OR OUTPUT TYPE
        max_time = max((p['val'] for p in self.pars.values()
                        if isinstance(p['val'], timedelta)), 
                        default=timedelta(0)).total_seconds()        
        if max_time > 0:
            self._calc(self.get_data(max_time, self.PARS_FROM_DATA))

    # USER FUNCTIONS
    def _init(self):
        # custom init
        pass

    def _slice(self, data,
               start_time=None,
               stop_time=None,
               seconds_back=None,
               dec=None) -> slice:
        """
        finds the indexes for time stamps in data
        start_time: start time for window (if not defined, set to data start)
        stop_time: end of window (if not defined set to data end)
        seconds_back: slice # seconds back from end to end
        dec: steps for decimation of data, if None, no decimation is applied
        """

        t = data["time"]
        start_idx, stop_idx = None, None

        # find start of data
        start = self.shared_mem.get("start_window")
        if start is None or start > 0:
            # if start = 0 the start of data is at index 0
            # (and remains there: data is added at the end)
            self.shared_mem["start_window"] = start = bisect(t, 0)

        if start_time:
            start_idx = bisect(t, start_time, lo=start)

        else:
            start_idx = start

        if seconds_back:
            start_idx = bisect(t, t[-1] - seconds_back, lo=start)

        if stop_time:
            stop_idx = bisect(t, stop_time, lo=start_idx)

        return slice(start_idx, stop_idx, dec)

    @staticmethod
    def _calc_mean(data, par, window) -> float:
        """
        calculates the mean of a parameter over a window
        """
        try:
            par_data = data[par]

        except ValueError:
            return      # par not found in data
        
        return float(np.nanmean(np.abs(par_data[window])))  # float is needed, otherwise np.float object is returned

    def _calc_status(self, data, threshold,
                      sample_time=300,
                      baseline_time=None,
                      par="Motion Ang. X",
                      state=("Awake", "Sleeping", "Activity")
                      ):
        """
        Checks a parameter is above or below threshold and returns a label of
        the current status

        Note: Calculated time awake/asleep and state are saved in tracked_data

        - data (np.array/ dict):            structured array / dict containing data as numpy arrays. It must contain 
                                                the key "time".
        - threshold (float):                The minimum mean data during the `sample_time` to determine 
                                                that the animal is awake. The value can be applied over itself 
                                                or over baseline values, depending on the value of the `par` key 
                                                in the `pars` attribute.
        - sample_time (int, optional):      The window of time to measure movement over (to determine if the animal is 
                                                awake, for example) in seconds. Defaults to 300.
        - baseline_time (float, optional):  The time to sample the baseline over in seconds. If None, no baseline time 
                                                is measured and the sample is tested against its last state. If a 
                                                baseline is calculated, the sample is tested against it. Defaults to None.
        - par (str, optional):              The key from `data` to use for calculations. Defaults to "Motion Ang. X".
        - state (tuple, optional):          A tuple containing the state names and the name of the category. It should 
                                                be in the form of (Above Threshold, Below Threshold, Category). 
                                                Defaults to ("Awake", "Sleeping", "Activity").
        """
        active, passive, category = state
        _baseline_data_mean = np.nan

        # calc state since last refresh
        _par_window_now = self._slice(data, 
                                      seconds_back=(self.parent
                                                        .parameters['main']['interval']['val']
                                                        .total_seconds()))           # create slice
        _par_data_mean_now = self._calc_mean(data, par, _par_window_now)

        # calc mean sample
        _par_window = self._slice(data, seconds_back=sample_time)           # create slice
        _par_data_mean = self._calc_mean(data, par, _par_window)
        self.tracked_data.setdefault(par, {}).update({"last": _par_data_mean})

        # calc mean baseline
        if baseline_time is not None:
            _baseline_window = self._slice(data,
                                           seconds_back=(sample_time
                                                         + baseline_time))   # create slice
            _baseline_data_mean = self._calc_mean(data, par, _baseline_window)
            
            (self.tracked_data.setdefault(par, {})
             .update({"baseline": _baseline_data_mean}))


        # calc threshold
        _key_mode = (self.pars.get(f"{par.lower()} threshold mode",{})
                     .get("val", "absolute value"))

        if _key_mode == "relative to baseline":
            threshold *= _baseline_data_mean
        
        elif _key_mode == "relative to self":
            threshold *= _par_data_mean
        # NOTE: else _key_mode == 'absolute value' -> threshold is an absolute value, no need to adjust it
    
        _state_now = (active if (_par_data_mean_now >= threshold) else passive)
        _state_current = (active if (_par_data_mean >= threshold) else passive)

        _t = datetime.fromtimestamp(data["time"][-1])
        
        self.tracked_data.setdefault("dt", {}).update({"refreshed": _t})

        if (category not in self.tracked_data
            or (self.tracked_data[category]["last"] != self.tracked_data[category]["current"])):
            # no tracked data yet, or change detected
            self.tracked_data[category] = {'now': _state_now,
                                           "current": _state_current,
                                           "last": _state_current,
                                           "duration": timedelta(seconds=0),
                                           "changed": _t,
                                           }
        else:
            # no change
            self.tracked_data[category]["duration"] = _t - (self
                                                            .tracked_data
                                                            [category]
                                                            ["changed"])
            self.tracked_data[category]["current"] = _state_current
            self.tracked_data[category]["now"] = _state_now


    def _calc(self, data):
        # check if animal is awake or sleeping:
        self._calc_status(data, self.pars["motion ang. x threshold"]["val"],
            sample_time=self.pars["motion detection window"]["val"].total_seconds(),
            par="Motion Ang. X",
            state=("Awake", "Sleeping", "Activity"))

        # check if changes in bloodflow:
        self._calc_status(data, self.pars["ois signal threshold"]["val"],
                sample_time=self.pars["csd window"]["val"].total_seconds(),
                baseline_time=self.pars["ois signal baseline window"]["val"].total_seconds(),
                par="OIS Signal",
                state=("CSD", "No CSD", "Blood Flow"))

        return True
