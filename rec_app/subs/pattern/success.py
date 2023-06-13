# -*- coding: utf-8 -*-
"""
Created on Fri Feb 7 16:25:52 2020

@author: Dmitri Yousef Yengej

This function will be used for autostimulation
to test if stimulation was succesful

dont change the class name or return format

it should return a True or False (True if pattern is found)
and confidence level (or match percentage)

anything can be used in the check function but beware that if it becomes too
slow it will affect the whole system (gui might become unresponsive etc)

multiprocessing can be used to offload the system for complexer calculations,
however the system has few free cores available depending on the configuration

NOTE:
- data will be a dictionary with as key the parameter name, as value a numpy array with the data

- data can include nans, be sure that functions here are able to
  deal with it!

- data consists of a Dictionary with as keys the recorded parameters (as found
  in the data files) and Values are np.arrays with the data

"""
import numpy as np

from bisect import bisect

# Other imports
import time
from datetime import timedelta, datetime

class Success():
    # checks if pattern is in data
    # use threshold to set threshold for confidence to
    # that pattern is in data

    # DO NOT EDIT
    confidence = 0.0

    # USER EDITABLE 
    decimate = 50                           # decimation for data
    dt_interval = 10                        # interval between repeating protocol in sec, None means no repeats
    shared_mem = {}                         # Shared memory between watcher and succes

        # Input parameters (get buttons in autostim setup):
    pars = {"max sample window": {"val": timedelta(minutes=4),
                                  "desc": "Max time to detect success after trigger"},
            "min sample window": {"val": timedelta(seconds=30),
                                      "desc": "Min wait time after stim to detect success"},
            }
    
    # USER DEFINED:
    None
    
    # Methods:
    def __init__(self, parent, shared_mem, pars, tracked_data, **kwargs):
        shared_mem.update(self.shared_mem)
        self.shared_mem = shared_mem
        pars.update({k:v for k, v in self.pars.items() if k not in pars})        
        self.pars = pars
        self.tracked_data = tracked_data
        self.parent = parent
        for k in kwargs:
            setattr(self, k, kwargs[k])
        self._init()

    def save(self, key, val):
        """
        placeholder function for function that 
        saves data in key
        """
        return
    
    def load(self, key):
        """
        placeholder function for function that 
        loads data from key
        """
        return


    # Essential, do not change or change name:
    def detect(self,) -> bool:
        """
        return True if success

        False if not successful (window is over but no CSD)

        or None if no detection (not sure yet, within window but no CSD detected yet)
        """
        return self._calc()

    # USER FUNCTIONS
    def _init(self):
        # custom init
        pass

    def _calc(self, go=None):
        # check time
        _t_now = datetime.now()
        _t_since_stim = (_t_now 
                         - self.tracked_data
                         .get("Last Stim.", {})
                         .get("time", _t_now))

        # if too soon after stim return None
        if self.pars["min sample window"]['val'] > _t_since_stim: 
            self.tracked_data.get("Last Stim.", {})["success"] = None
            return

        # if no CSD after stim, return False
        if _t_since_stim > self.pars["max sample window"]['val']:
            # TODO: save threshold None when unsuccessful
            self.tracked_data["Last Stim."]["success"] = False
            return False

        _CSD = self.tracked_data["Blood Flow"]["last"] == "CSD"

        if _CSD:
            _state = self.tracked_data["Last Stim."]["state"]
            self.tracked_data.setdefault("Last Result", {})["state"] = _state
            self.tracked_data["Last Result"]["result"] = "success"
            self.tracked_data["Last Result"]["time"] = _t_now            
            self.tracked_data.setdefault("Stim. Treshold", {})[_state] = self.tracked_data["Last Stim."]["duration"]
            
            # stop forced thresholding
            self.shared_mem['forced_thresholding'] = False

            # reset parameters
            self.shared_mem['thresholding'] = False
            self.shared_mem['stim_announced'] = False

            # save last threshold
            self.save("Stim. Threshold", self.tracked_data["Stim. Treshold"])
            self.tracked_data["Last Stim."]["success"] = True
            go = True

        return go




# for testing:
if __name__ == '__main__':
    pass
