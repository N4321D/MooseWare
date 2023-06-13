# -*- coding: utf-8 -*-
"""
Created on Fri Feb 7 16:25:52 2020

@author: Dmitri Yousef Yengej

This function will be used for autostimulation
it triggers stimulation if conditions are right
(conditions are tracked by tracker)

dont change the class name or return format

it should return a True or False (True if pattern is found)
and confidence level (or match percentage)

anything can be used in the check function but beware that 
if it becomes too slow it will affect the whole system 
(gui might become unresponsive etc)

multiprocessing can be used to offload the system for
complexer calculations however the system has few free 
cores available depending on the configuration


NOTE:
- data can include nans, be sure that functions here are able to
  deal with it!

- data consists of a Dictionary with as keys the recorded parameters
  (as found in the data files) and Values are np.arrays with the data


SHARED VARS, written or changed here:
tracked_data: {"Activity": {"Last Stim.": "val": (start, stop, mA),
                                          "time": time_stamp},

                }

"""

from datetime import date, timedelta, datetime, date, time
import random

class Trigger():
    """
    checks if pattern is in data
    use threshold to set threshold for confidence to
    that pattern is in data
    triggers stim if patter is in data
    """
    # DO NOT EDIT:

    # USER EDITABLE:
    shared_mem = {'max_idle_time': None,               # max time that the subject can be napping before nudge
                  'acute_time_asleep': timedelta(0),   # current measured time that the subject is napping
                  'next_reduction': None,              # next time that max idle time should be reduced
                  'forced_thresholding': False,        # bypasses time checks to force start thresholding protocol
                  'csd_with_deprivation': False,       # indicates if CSD was triggered after deprivation 
                  'thresholding': False,               # indicates if currently running a thresholding protocol
                  'stim_announced': False              # indicates that stimulation heads up was sent
                  }                         # Shared memory between tracker, trigger and success

    #       Input parameters (get buttons in autostim setup):
    # NOTE: DO NOT USE CAPITALS IN KEYS!!!
    pars = {"find csd threshold": {"val": True,
                                   "desc": "enable OIS stimulation to find CSD threshold"},  
            "time asleep": {"val": timedelta(minutes=30),
                            "desc": "minimum time asleep to count as sleeping"},                    # time that the animal has to be asleep for stim 
            "time awake": {"val": timedelta(minutes=30),
                            "desc": "minimum time awake to count as sleeping"},                     # time that the animal has to be awake for stim
            "stim asleep": {"val": True,
                            "desc": "stimulate when asleep"},
            "stim awake": {"val": True,
                           "desc": "stimulate when awake"},

            "heads up time": {"val": timedelta(minutes=2),
                              "desc": "time before stim. to send alert (if notifications enabled)"},

            "stim interval": {"val": timedelta(minutes=15),
                               "desc": "interval between stimulation pulses"},                  # time in seconds between stims in sec
            "event interval": {"val": timedelta(hours=12),
                                "desc": "interval between successful stimulations"},                     # min time between successfully triggered events in sec
            "stim intensity": {"val": 30,
                              "desc": "stimulation Intensity in mA"},
            "stim start duration": {"val": timedelta(seconds=5),
                                    "desc": "start duration of pulse"},
            "stim max duration": {"val": timedelta(seconds=60),
                        "desc": "maximal pulse duration"},
            
            "steps back on new threshold": {"val": 2,
                                            "desc": ("amount of steps to start below last"
                                                     "threshold when starting a new thresholding protocol")},
            
           # pars for keep awake            
            "keep awake":               {'val': False,
                                         'desc': "keep subject awake"},

            "bedtime":                  {'val': time(hour=7,),
                                         'desc': "the time the subject is expected to go to sleep (24h format)"},

            "keep awake time":          {'val': timedelta(hours=4),
                                         'desc': "target time to keep the subject awake since bedtime"},

            "max idle time start":      {'val': timedelta(seconds=5),
                                         'desc': 'the maximal time the subject can be idle\nminimally the refhresh interval (in Auto Stim. main)'},

            "reduce idle time every":   {'val': timedelta(hours=3),
                                         'desc': 'interval to reduce the idle time with reduction step'},
            "idle time reduction step": {'val': timedelta(seconds=1),
                                         'desc': 'interval to reduce the idle time with reduction step'},
            "max idle time end":        {'val': timedelta(seconds=1),
                                         'desc': 'limit the reduction to this value'},
            "trigger csd when kept awake": {'val': False,
                                            'desc': 'start csd thresholding this time after bedtime'},
            "csd after keeping awake":   {'val': timedelta(hours=2),
                                         'desc': 'start csd thresholding this time after bedtime'},
            'nudge block duration':           {'val': timedelta(seconds=5),
                                         'desc': 'total duration of the nudge'},

            'use random nudge pattern': {'val': True,
                                         'desc': 'use Random on/off nudge instead of continuously on'},
            
            'minimal nudge time':       {'val': timedelta(microseconds=2e4),
                                         'desc': 'minimal on or off time during random pattern'},
            
            'on/off ratio':             {'val': 2,
                                         'desc': 'ratio on to off during random pattern, e.g'},
                    
            }       

    # USER DEFINED:
    PARS_FROM_DATA = ['time', 'OIS Signal', 'Motion Ang. X']  # parameters to read from data


    def __init__(self, parent, shared_mem, pars, tracked_data, **kwargs):
        shared_mem.update(self.shared_mem)
        self.shared_mem = shared_mem
        pars.update({k:v for k, v in self.pars.items() 
                     if k not in pars})
        self.pars = pars
        self.tracked_data = tracked_data
        self.parent = parent
        for k in kwargs: 
            setattr(self, k, kwargs[k])
        self.shared_mem['stim_announced'] = False
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

    def detect(self) -> tuple:
        # ESSENTIAL METHOD, DO NOT CHANGE NAME OR OUTPUT TYPE
        # TODO: make sure triggered CSD does not stop looking for awake or not

        max_time = max([p['val'] for p in self.pars.values()
                        if isinstance(p['val'], timedelta)]).total_seconds()
        
        data = self.get_data(max_time, self.PARS_FROM_DATA)

        go, prot = {}, {}
        if self.pars['find csd threshold'] or self.shared_mem['force_thresholding']:
            go['ois'], prot['ois'] = self._calc_ois(data)
        if self.pars['keep awake']:
            go['keep awake'], prot['keep awake'] = self._calc_awake(data)
        return go, prot
    
    # USER FUNCTIONS
    def _init(self):
        # custom init
        pass

    # OIS TRIGGER FUNCS
    def _calc_ois(self, data, go=False,):
        """
        conditions are check here and if met -> 
        stim is triggered
        """
        prot = []

        # check time
        _t = datetime.now()
        _last_stim_time = (self.tracked_data
                           .get("Last Stim.", {})
                           .get("time") 
                           or datetime.fromtimestamp(0))
        _last_result_time = (self.tracked_data
                              .get("Last Result", {})
                              .get("time",
                                   datetime.fromtimestamp(0)))

        _last_result = (self.tracked_data
                              .get("Last Result", {})
                              .get("result"))
        
        # time between stims shorter than interval:
        if ((_t - _last_stim_time) < self.pars["stim interval"]["val"]):
            return False, []

        # time between events to short
        if (_t - _last_result_time) < self.pars['event interval']["val"]:
            if not self.shared_mem['forced_thresholding']:
                return False, []

        # check if animal is awake / asleep
        _state = (self.tracked_data
                  .get("Activity", {})
                  .get("last"))
        _duration = (self.tracked_data
                     .get("Activity", {})
                     .get("duration"))
        _last_state = (self.tracked_data
                       .get("Last Success", {})
                       .get("state")
                       )
        

        if _state is None or _duration is None:
            # "no state or duration"
            return go, prot

        _notify = False
        # awake
        if (_state == "Awake" and self.pars['stim awake']['val']
            and (_last_state in {"Sleeping", None}                  # only check if last state was sleeping if sleep stims
                 if self.pars["stim asleep"]['val'] else True)):


                if _duration >= self.pars["time awake"]['val']:
                    go = True
                elif _duration >= (self.pars["time awake"]['val']
                                   - self.pars['heads up time']['val']):
                    _notify = True
        
        # sleeping
        if (_state == "Sleeping" and self.pars["stim asleep"]['val']
            and (_last_state in {"Awake", None}
                 if self.pars["stim awake"]["val"] else True)):
            if _duration >= self.pars["time asleep"]['val']:
                go = True
            elif _duration >= (self.pars["time asleep"]['val']
                                   - self.pars['heads up time']['val']):
                _notify = True
        
        # forced thresholding
        if self.shared_mem['forced_thresholding']:
            go = True
        
        if _notify:
            self.notify_stim(_state)                    

        if go:
            prot.append(self._find_threshold(_state))
            self.shared_mem['thresholding'] = True    # should come after calling self._find_threshold

            if not prot[-1]:
                # success was none, checker not ready
                return False, []

            # stop if max pulse length is reached and and/ or last stim has failed
            if (((prot[0][1] - prot[0][0]) 
                 > self.pars["stim max duration"]['val'].total_seconds())
                and (self.tracked_data.get("Last Stim.", {})
                     .get("success") is False)): 

                # stop forced thresholding
                self.shared_mem['forced_thresholding'] = False

                # reset parameters
                self.shared_mem['thresholding'] = False
                self.shared_mem['stim_announced'] = False

                # limit to max stim
                prot[0][1] = self.pars["stim max duration"]['val'].total_seconds() + prot[0][0]
                
                # 
                self.tracked_data.setdefault("Last Result", {})["state"] = _state
                self.tracked_data["Last Result"]["result"] = "failed"
                self.tracked_data["Last Result"]["time"] = _t
                
                go, prot = False, []
            
            else:
                # set protocol as last stim
                self.tracked_data["Last Stim."] = {"duration": prot[0][1] - prot[0][0],
                                               'mA': prot[0][2],
                                               "state": _state,
                                               "success": None,
                                               "time": datetime.now(),
                                               }

        return go, prot

    def _find_threshold(self, state):
        """
        finds stim threshold to trigger CSD
        
        state: tracks for which state a threshold was found
        
        next_stim:  can be used to set a start value 
                    (start, stop, intensity)
        """
        next_stim = [0, self.pars["stim start duration"]['val'].total_seconds(), 
                     self.pars['stim intensity']['val']]

        threshold_stim = (self.tracked_data.get("Stim. Threshold", {})
                          .get("state"))

        # get last stim parameters
        last_stim = self.tracked_data.get('Last Stim.', {})
        _last_stim_state = last_stim.get("state")
        _last_stim_duration = last_stim.get('duration')
        _last_stim_intensity = last_stim.get('mA')
        _last_stim_success = last_stim.get('success')

        last_stim = None
        if (None not in {_last_stim_state, _last_stim_duration, _last_stim_intensity}):
            if state == _last_stim_state:
                if _last_stim_success is False:
                    if ((_last_stim_duration 
                        >= self.pars['stim max duration']['val'].total_seconds())
                        and self.shared_mem['thresholding'] is False):
                        # stimulation went through all steps and was unsuccessfull
                        # restart protocol
                        last_stim = None

                    else:
                        # if last stim was not a success or failure (success == False)
                        # success is None means it is not checked yet
                        last_stim = (0, _last_stim_duration, _last_stim_intensity)
                else:
                    # results not checked yet or was successful, do not create new stim
                    return []
 
        if last_stim is None:
            # start new stim run
            if threshold_stim is None:
                last_threshold = self.load("Last Threshold")
                if (last_threshold is not None 
                    and self.shared_mem.get("rec_name") == last_threshold["name"]):
                    # use saved last threshold
                    self.tracked_data["Stim. Threshold"][state] = last_threshold

                    next_stim = self._calc_next_stim(last_threshold["val"], 
                                                     op="-", 
                                                     step=self.pars["steps back on new threshold"]['val'])
                else:
                    # start from beginning (next stim as is)
                    pass 

            else:
                # start a little lower than last successful stim
                next_stim = self._calc_next_stim(threshold_stim,
                                                 op="-",
                                                 steps=self.pars["steps back on new threshold"]['val'])
        else:
            # TODO: FIGURE out a way to detect if max stim length is reached but no CSD:
            #       the system will use the max stim length then and not stim at all (because it
            #       is longer than max).
            # increase stim based on last stim
            next_stim = self._calc_next_stim(last_stim)
        
        return next_stim
    
    @staticmethod
    def _calc_next_stim(last_stim, op="+", steps=1, delay=0.1):
        """
        calculates duration of next stim based on last stim

        op: can be + or -: increase or decrease next stim

        steps: how many steps to increase or decrease

        delay: delays start (in sec)
        """
        start, stop, intesity = last_stim
        duration = stop - start

        if op == "+": 
            _mult = 1
        else:
            _mult = -1

        for i in range(steps):
            duration += (((duration + 10) // 10) * _mult)

        last_stim = [delay, delay + max(0, duration), intesity]

        return last_stim


    def notify_stim(self, state):
        if self.shared_mem['stim_announced'] is True:
            return
        self.parent.send_alert(f'Ready to start {state} protocol '
                                f"in {self.pars['heads up time']['val']}")
        self.shared_mem['stim_announced'] = True

    # KEEP AWAKE TRIGGER
    def _calc_awake(self, data, go=False):
        """
        calculate if nudge should be activated
        returns True if needed and nudging protocol

        """
        prot = []
        t_now = datetime.now()    #  current time
        t_bedtime = datetime.combine(date.today(),
                                   self.pars['bedtime']['val'])
        if t_bedtime > t_now:
            t_bedtime -= timedelta(days=1)
        

        t_since_bedtime = t_now - t_bedtime

        # trigger thresholding if turned on
        if self.pars['trigger csd when kept awake']['val']:
            if t_since_bedtime > self.pars['csd after keeping awake']['val']:
                if not self.shared_mem['csd_with_deprivation']:
                    self.shared_mem['csd_with_deprivation'] = True
                    self.shared_mem['forced_thresholding'] = True

        # detect if current time is within keep awake window, else return
        if t_since_bedtime > self.pars['keep awake time']['val']:
            # reset max idle time to start value
            self.shared_mem['max_idle_time'] = self.pars['max idle time end']['val']
            self.shared_mem['next_reduction'] = None
            
            self.shared_mem['csd_with_deprivation'] = False       # reset csd thresholding for next window

            return False, []
        
        # calculate if idle 
        if not self._check_if_sleeping(t_now):
            # subject awake
            return False, []

        # create nudge_protocol because subject is sleeping
        prot = self._create_nudge_protocol()
        return True, prot
        
    def _create_nudge_protocol(self):
        """
        creates nudge protocol
        protocol has the form of:
        [True, False, ...]
        duration is minimal nudge time
        """
        min_nudge_len = self.pars['minimal nudge time']['val'].total_seconds()
        block_len = self.pars['nudge block duration']['val'].total_seconds() - min_nudge_len   # substract 1 nudge becuase we always start with an on
        prot = []
        steps = int(block_len/min_nudge_len)
        ratio = self.pars['on/off ratio']['val']

        if self.pars['use random nudge pattern']['val']:
            on_count = int((steps / (ratio + 1)) * ratio)  # number of on events determined by ratio
            off_count = int((steps / (ratio + 1)) * 1)     # number of off events
            prot += ([True for i in range(on_count)] + 
                     [False for i in range(off_count)])
            random.shuffle(prot)                           # randomize on and off
        
        else:
            prot += [True for i in range(steps)]
            

        prot = [True] + prot + [False]   # start with on and stop at the end
        return [min_nudge_len, prot]
        
    def _check_if_sleeping(self, t_now):
        """
        checks if subject is sleeping and returns True if sleeping
        else False
        """
        dt_nap = self.parent.parameters['main']['interval']['val']

        if self.shared_mem.get('max_idle_time') is None:
            # reset max idle time to start value if not set
            self.shared_mem['max_idle_time'] = self.pars['max idle time end']['val']

        if self.tracked_data.get('Activity', {}).get('now') == 'Sleeping':
            # add current nap time to time asleep
            self.shared_mem['acute_time_asleep'] += dt_nap
        else:
            # reset time asleep if animal is awake
            self.shared_mem['acute_time_asleep'] = timedelta(seconds=0)
            
        
        if self.shared_mem.get('next_reduction') is None:
            self.shared_mem['next_reduction'] = (t_now
                                                 + self.pars['reduce idle time every']['val'])
        # decrease max idle time every x time
        if t_now > self.shared_mem['next_reduction']:
            # calc timepoint for next reduction:
            self.shared_mem['next_reduction'] = (self.shared_mem['next_reduction']
                                                 + self.pars['reduce idle time every']['val'])
            # reduce idle time:
            self.shared_mem['max_idle_time'] -= self.pars['idle time reduction step']['val']

            if self.shared_mem['max_idle_time'] < self.pars['max idle time end']['val']:
                # limit to max idle time end
                self.shared_mem['max_idle_time'] = self.pars['max idle time end']['val']
            
        if self.shared_mem['acute_time_asleep'] > self.shared_mem['max_idle_time']:
            # Subject is sleeping
            self.shared_mem['acute_time_asleep'] = timedelta(seconds=0)          # reset idle time
            return True
        
        else: 
            # Subject is awake
            return False