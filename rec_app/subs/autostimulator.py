# -*- coding: utf-8 -*-
"""
Created on Fri Feb 7 16:22:46 2020

@author: Dmitri Yousef Yengej

Autostimulator class checks incoming data for certain patterns and returns

a true or false to determine if stimulation should be triggered

pattern can be loaded from csv file

"""

import json
import time
from datetime import timedelta, datetime, time as dt_time

from kivy.app import App
from kivy.clock import Clock
from kivy.config import ConfigParser
from kivy.event import EventDispatcher
from kivy.graphics import Color, Rectangle
from kivy.lang.builder import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget, WidgetException

from subs.gui.widgets.custom_settings import SettingsWithSidebar as Settings, timestr_2_timedelta, timestr_2_time

from subs.gui.vars import BACKBLACK, BUT_BGR, MO, MO_BGR, WHITE, LIGHTER_BLUE
from subs.pattern.success import Success
from subs.pattern.tracker import Tracker
from subs.pattern.trigger import Trigger

kv_str = (
"""
<AutostimToggle>:
    background_color: MO_BGR if self.state == 'down' else BUT_BGR
    background_down: 'atlas://data/images/defaulttheme/button' # default background
    color: WHITE if self.state == 'down' else MO

<StartStop>:
    text_choices: ("", "")
    text: self.text_choices[0] if self.state == "normal" else self.text_choices[1]
    background_color: MO_BGR if self.state == 'down' else BUT_BGR
    background_down: 'atlas://data/images/defaulttheme/button' # default background
    color: WHITE if self.state == 'down' else MO


<TrackerLabel>:
    text_size: self.size
    markup: True
    halign: "left"
    valign: "top"
    background_color: 0, 0.5, 0.3, 1
    padding_y: "10sp"
    padding_x: "10sp"

<AutoStimPanel>:
    cols: 1
    orientation: 'bt-lr'
    canvas.before:
        Color:
            rgba: (0, 0, 0, 0.6)
        Rectangle:
            pos: self.pos
            size: self.size

    # BUTTONS           
    GridLayout:
        id: button_panel
        rows: 1
        size_hint: 1, 0.1

        canvas.before:
            Color:
                rgba: BACKBLACK
            Rectangle:
                pos: self.pos
                size: self.size

        # Start Tracking
        StartStop:
            id: start_tracking
            group: 'autostim_track'
            text_choices: ("Start\\nTracking", "Stop\\nTracking")
            on_release: root.tracking_on(self.state == 'down')
            disabled: (app.IO.running is False)

        # Start Autostim
        StartStop:
            id: start_autostim
            group: 'autostim_do'
            text_choices: ("Start\\nAutoStim", "Stop\\nAutoStim")
            on_release: root.autostim_on(self.state == 'down')
            disabled: start_tracking.state == 'normal'
        
        # Treshold now
        StartStop:
            id: threshold_now
            text_choices: ("Threshold\\nNow", "Thresholding...")
            group: "threshold"
            disabled: (root.autostim.do_autostim is False)
            on_release: root.threshold_now()
        
        # Tracked Data
        AutostimToggle:
            id: tracked_data
            text: "Tracked Data"
            group: 'autostim_pars'
            state: 'down'
            on_release: root.toggle_tr_data()
        
        # Parameters
        AutostimToggle:
            id: parameters
            text: "Parameters"
            group: 'autostim_pars'
            state: 'normal'
            on_release: root.toggle_par_data()
        
        # Close Button:
        AutostimBut:
            id: close_panel
            text: "Close\\nPanel"
            on_release: root.parent.remove_widget(root)
    
    # READOUTS
    # text labels are added in python script below
    ReadOutPanel:
        id: readouts_panel
        cols: 4

                
"""
)

def log(message, level="info"):
    getattr(App.get_running_app().logger, level)(f"AUTOSTIMULATOR: {message}")


def kivy_rgba_to_rgba(inp):
    inp = [int(i*0xff) for i in inp]
    out = hex(inp[0] << 24 | inp[1] << 16 | inp[2] << 8 | inp[3])[2:]
    return out


HIGHLIGHT_TXT_COL = kivy_rgba_to_rgba(MO)
PAR_TXT_COL = kivy_rgba_to_rgba(LIGHTER_BLUE)


class AutostimToggle(ToggleButton):
    def _do_press(self):
        if self.state == "down":
            return
        else:
            return super()._do_press()

class StartStop(ToggleButton):
    pass

class TrackerLabel(Label):
    pass

class AutostimBut(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = MO
        self.background_color = BUT_BGR

class ReadOutPanel(GridLayout):
    widget_dict = {}                # dictionary with all the widget labels

class AutoStimulator(EventDispatcher):
    last_stim = 0       # time of last stimulation
    last_success = 0    # time of last successful stim
    
    stimulating = False           # indicates if stimulating or not
    successful = False      # indicates if last stim was succesful
    
    # Subclasses
    tracker = None          # placeholder for tracker class
    trigger = None          # placeholder for trigger class
    success = None          # placeholder for 

    # status: stopped, scanning, checking, triggered
    status = StringProperty("stopped")

    shared_mem = {"rec_name": None,             # name of the recording
                  }         # dict with shared memory for watcher and success checker

    parameters = {"main":    {"interval": {"val": timedelta(seconds=1), "desc": "interval between calculating values"},
                              "notify": {"val": False, "desc": "send sms notifications"},  # dt between checking of data in sec
                              'test mode': {'val': True, 
                                            'desc': "Do not do OIS stim when conditions are met: to test autostim"},
                              },                  
                  "tracker": {},
                  "trigger": {},
                  "success": {},
                  }         # dict with setup parameters

    # Dictionary with tracked data (such as last movement etc)
    tracked_data = {"dt":{"all": None, "tracker": None, "trigger": None, "success": None}}

    do_autostim = BooleanProperty(False)             # set to on to stimulate (not only track)
    thresholding = BooleanProperty(False)            # indicates if tresholding

    wake_protocol = []      # placeholder for list with nudge protocol
    wake_up_event = None    # placeholder for kivy clock schedule for wake up protocol

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = App.get_running_app()
        self._reset()
        self.watch_event = Clock.schedule_interval(
            self._watch_stim_loop, 
            self.parameters["main"]["interval"]['val'].total_seconds())
        self.watch_event.cancel()

        # placeholder for watch event scheduling
        self.next_watch_event = Clock.schedule_once(lambda *x: x, 0)
        
        self.shared_mem['interval'] = self.parameters['main']['interval']    # share interval with all classes
    
    def get_data(self, seconds_back, par=...):
        """
        get last recorded data upto x seconds back
        - seconds_back: time from last recorded data back to retrieve
        - par: specific parameter to retrieve, if not defined all 
               pars are returned
        """
        return self.app.IO.get_time_back_data(seconds_back=seconds_back,
                                              par=par)

    def start_autostim(self, *args):
        """
        starts checking data and stimulation if conditions are met
        """
        self._reset()
        self._watch_stim_loop()
        self.watch_event()
        self.status = "scanning"
        self.app.IO.add_note("Autostimulation Started")

    def stop_autostim(self, *args):
        """
        starts checking data and stimulation if conditions are met
        """
        self.watch_event.cancel()
        self.do_autostim = False
        self.stop_wakeup_prot()
        self.status = "stopped"
        self.app.IO.add_note("Autostimulation Stopped")

    def manual_check(self):
        """
        can be used to manually trigger check
        """
        self._watch_stim_loop()

    def start_stim(self, *args, **kwargs):
        """
        placeholder for function to launch when conditions are met
        to (re-) start whole stim protocol
        """
        return

    def continue_stim(self, *args, **kwargs):
        """
        placeholder for function to launch on success
        """
        return

    def stop_stim(self, *args, **kwargs):
        """
        placeholder for function to launch on success
        """
        return

    def _custom_protocol(self, prot, *args, **kwargs):
        """
        calls self.custom_protocol (which should be replaced with method
        that thriggers stim) and reports autostim 
        """
        self.app.IO.add_note(f"Autostimulation Triggered: {','.join([str(i) for i in prot])}")
        return self.custom_protocol(prot, *args, **kwargs)

    def custom_protocol(self, prot, *args, **kwargs):
        """
        triggers custom stim protocol
        protocol must be list with tuples containing start (sec.), stop (sec.) and intesity
        [(start, stop, instensity), (start, stop, instensity), ....]

        start is relative to sending the protocol to the sensor.

        override this method when initiating autostim class with the 
        method that trigger stim
        """
        return

    def change_timeout(self, timeout):
        """
        change interval of checking for stim conditions/ stim success
        """
        self.parameters["main"]["interval"]["val"] = timedelta(seconds=timeout)
        self.watch_event.timeout = timeout

    def wake_up_out(self, state):
        """
        placeholder for function that is activated when subject is sleeping
        to wake it up

        overwrite when after initiating autostim class
        with a function that uses state to activate something
        state will be True for on and False for off

        you can cancel the protocol at any time by calling:
        stop_wakeup_prot
        """
        return

    def stop_wakeup_prot(self, *args):
        if self.wake_up_event is not None:
            self.wake_up_event.cancel()
            self.wake_up_event = None
            self.wake_up_out(False)

    def wake_up(self, *args):
        if not self.wake_protocol:
            self.stop_wakeup_prot()
        else:
            self.wake_up_out(self.wake_protocol.pop(0))

    def _start_wakeup_prot(self, prot, *args):
        """
        this method will be triggered if the subject is sleeping
        prot will be the protocol to wake it up.
        protocol has this format:
        [dt, [sequence of on/ off (as True/ False)]]
        dt indicates the length of each on or off block
        and on or off indicates if the output pin should be on or off
        e.g. [0.1 [True, True, False True, False]] is:
        on for 0.2 sec (2x0.1), then off for 0.1 sec, then on for 0.1 sec,
        then off 
        """
        dt, self.wake_protocol = prot     
        self.wake_protocol.append(None)    # set None at end to indicate end
        self.wake_up_event = Clock.schedule_interval(self.wake_up, dt)

    def _watch_stim_loop(self, *args):
        """
        function which is repeatedly called (interval self.dt)
        this function launches watcher to search for conditions
        and if conditions are found, it launches success to check if
        stim was successful
        """
        _t_start, _t_track, _t_trigger, _t_success = datetime.now(), None, None, None

        self.watch_event.timeout = (self.parameters["main"]["interval"]["val"]
                                    .total_seconds())
        
        if not self.app.IO.running:
            return

        _status = "tracking"

        # calculate conditions
        self.tracker.process()
        _t_track = datetime.now() - _t_start

        protocol = {'ois': None,
                    'wake': None,}

        if self.do_autostim:            
            # check if condition meet stim criteria
            
            go, protocol = self.trigger.detect()
            if not self.stimulating:
                self.stimulating = go['ois']
            else:
                protocol['ois'] = None
                _status = "triggered"
            
            # wake up if required (only when not already in a protocol)
            if self.wake_up_event is None and go['keep awake']:
                self._start_wakeup_prot(protocol['keep awake'])
                _status = 'nudging'

            _t_trigger = (datetime.now() - _t_start) - _t_track

            # stim if required
            _prot = protocol.get('ois', None)
            if _prot:
                _status = "triggered"
                if not self.parameters['main']['test mode']['val']:
                    self._custom_protocol(_prot)

            # check if stim successful
            if self.stimulating:
                _t_success = datetime.now()
                success = self.success.detect()
                _t_success = datetime.now() - _t_success
                if success is not None:
                    # reset
                    self.stimulating = False
                    
                    if success is True:
                        _status = "success"
                    else:
                        _status = 'failed'

            # update thresholding status
            self.thresholding = self.shared_mem['thresholding']

        # update status
        if self.status != _status:
            self.status = _status

        # call update from parent
        Clock.schedule_once(self._update_parent, 0.05)

        self.tracked_data.setdefault("dt", {}).update(
            {"all": datetime.now() - _t_start,
             "tracker": _t_track,
             "trigger": _t_trigger,
             "success": _t_success})

    def _reset(self):
        """
        resets watcher and success
        """
        self.shared_mem = {"rec_name": self.app.IO.recording_name}

        self.tracker = Tracker(self, self.shared_mem, self.parameters["tracker"], self.tracked_data,
                               save=self.save, load=self.load, get_data=self.get_data)
        self.trigger = Trigger(self, self.shared_mem, self.parameters["trigger"], self.tracked_data,
                               save=self.save, load=self.load, get_data=self.get_data)
        self.success = Success(self, self.shared_mem, self.parameters["success"], self.tracked_data,
                               save=self.save, load=self.load, get_data=self.get_data)
        self.found = False
        self.successful = False
        self.do_autostim = False
        self.stimulating = False

    def save(self, key, val):
        """
        save val in key
        """
        return

    def load(self, key):
        """
        load val from key
        """
        return

    def _update_parent(self, *args):
        """
        place holder function for update method
        (called after each loop when autostim is running)
        """
        return

    def autostim_on(self, on, *args):
        """
        Turns autostim on or off, 

        Args:
            on (bool): True to turn on, False to turn off
        """
        self.do_autostim = on
    
    def send_alert(self, message):
        """
        send sms notification
        """
        if self.parameters['main']['notify']['val'] is True:
            self.app.msg.send_alert(f"AUTOSTIMULATOR:\n" + 
                                     message, 
                                    immediately=True)


class AutoStimPanel(GridLayout):
    """
    Panel Widget for autostim.
    Contain read parameters and enables setting variables
    """
    button_dict = {}

    def __init__(self, setup_autostim=None, **kwargs):
        if setup_autostim:
            self.setup_autostim = setup_autostim

        self.autostim = AutoStimulator()

        Builder.load_string(kv_str)
        super().__init__(**kwargs)

        self.autostim._update_parent = self.update
        self.app = App.get_running_app()

        self._create_pars_widget()

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
    
    def _create_pars_widget(self, *args):
        self.parameters = Settings()
        self.config = ConfigParser()
        self.config.read("autostim.ini")

        # load config in vars:
        for cls in self.config.sections():
            for opt in self.config.options(cls):
                val = self.config.get(cls, opt)
                self._on_par_change(self.config, cls, opt, val)
          
        # create settings json
        for cls, _dict in self.autostim.parameters.items():
            _sett = []

            self.config.adddefaultsection(cls)
            for k, v in _dict.items():

                _type = [] if "options" in v else v['val']
                _type = self.parameters.convert_type(_type)

                d = {"type": _type,
                     "title": k,
                     "desc": '',
                     "section": cls,
                     "key": k, 
                     }
                d.update(v)       # add options and description if in par

                # save config and remove val
                self.config.setdefault(cls, k, d.pop('val'))

                _sett.append(d)

            self.parameters.add_json_panel(
                f"Auto Stim. {cls}", self.config, data=json.dumps(_sett))


        # remove close button
        _button = self.parameters.children[0].ids.menu.ids.button
        self.parameters.children[0].ids.menu.remove_widget(_button)

        # assign function on changeing pars
        self.parameters.on_config_change = self._on_par_change

    def update(self, *args):
        """
        this method is called when autostim has new data
        """
        self._update_readouts_panel()


    def _update_readouts_panel(self, *args):
        """
        Updates the readouts panel with the tracked data.

        This function updates the `readouts_panel` widget with the tracked data
        stored in the `tracked_data` dictionary of `self.autostim`. 
        
        The existing widgets in the `readouts_panel` are cleared and new widgets
        are added for each item in the `tracked_data` dictionary. The widget for
        each item displays the main key and its values as text, with each sub-item
        key and value formatted in a readable manner.

        The formatting of the values depends on the data type:
        - If a value is a float, it is formatted to show three decimal places.
        - If a value is a `datetime` object, it is converted to a string and the
            microseconds part is truncated.
        - If a value is a `timedelta` object, it is converted to a string in the
            format `d. HH:MM:SS` or `S.ms` if the total time is less than one minute.

        :param *args: Optional arguments passed to the function.
        """
        # Iterate over each item in the `tracked_data` dictionary:
        for main_key, val in self.autostim.tracked_data.items():
            # Process only the items with a value of type `dict`:
            if isinstance(val, dict):
                # Create and parse the tracked data text:
                _txt = f"[b][u][color=#{HIGHLIGHT_TXT_COL}]{main_key}:[/color][/b][/u]  "
                for key, val in val.items():
                    # Format the value depending on its data type:
                    if isinstance(val, float):
                        val = f"{val:.3f}"
                    elif isinstance(val, datetime):
                        val = val.strftime("%x %X")

                    elif isinstance(val, timedelta):        
                        days, _sec = val.days, (val.seconds + val.microseconds/1e6)
                        hours, _rem = divmod(_sec, 3600)
                        minutes, seconds = divmod(_rem, 60)
                        if (days + hours + minutes) == 0:
                            val = f"{seconds:.3f} s."
                        else:
                            val = ((str(days) + "d. " if days > 0 else "") + 
                                    f"{hours:>02}:{minutes:>02}:{seconds:>02.0f}")
                            
                    # Add the formatted key and value to the text:
                    if key == "val":
                        _txt += f"\n{val}"
                    else:
                        _txt += f"\n[i][color=#{PAR_TXT_COL}]{key}:[/i][/color] {val}"

                # Determine whether the widget for the item already exists:
                _add = key not in self.ids.readouts_panel.widget_dict                   
                w = (self.ids.readouts_panel
                     .widget_dict.setdefault(key, TrackerLabel(text=_txt)))
                if _add:
                    # add widget if not existing:
                    self.ids['readouts_panel'].add_widget(w)
                else:
                    # update text
                    w.text = _txt

    def toggle_tr_data(self, *args):
        self.remove_widget(self.parameters)
        try:
            self.add_widget(self.ids['readouts_panel'])
        except WidgetException:
            pass

    def toggle_par_data(self, *args):
        self.remove_widget(self.ids['readouts_panel'])
        try:
            self.add_widget(self.parameters)
            self.parameters.pos = self.pos
            self.parameters.size = self.size
        except WidgetException:
            pass

    def _on_par_change(self, *args):
        """
        This method is launched when a parameter is changed
        and sends the changed par back to the autostim scripts
        """
        _conf_parser, cls, key, val = args
        _target = self.autostim.parameters[cls][key]["val"]

        # convert to target type
        if isinstance(_target, timedelta):
            val = timestr_2_timedelta(val)
        elif isinstance(_target, dt_time):
            val = timestr_2_time(val)
        elif isinstance(_target, bool):
            if val == 'True':
                val = 1
            elif val == 'False':
                val = 0
            val = type(_target)(int(val))
        else:
            val = type(_target)(val)
        
        # set parameters:
        self.autostim.parameters[cls][key]["val"] = val
        try:
            # set var in running class for 'live' change
            setattr(getattr(self.autostim, cls), 'pars', self.autostim.parameters[cls])
        except AttributeError:
            # skip if autostim is not running (classes are not there yet)
            pass

    def tracking_on(self, on, *args):
        if on is True:
            self.setup_autostim()                                               # setup autostim
            self.autostim.start_autostim()                                      # start autostim
        else:
            self.autostim.stop_autostim()                                       # stop autostim
            self.autostim.thresholding = False                                  # stop thresholding
    
    def autostim_on(self, on, *args):
        """Turn autostim on or off

        Args:
            on (bool): True turns on, False turns it off
        """
        self.autostim.autostim_on(on)
    
    def threshold_now(self, *args):
        forced_thres= not self.autostim.trigger.shared_mem['forced_thresholding']
        self.autostim.trigger.shared_mem['forced_thresholding'] = forced_thres
        if forced_thres:
            self.ids['threshold_now'].state = 'down'
        else:
            self.ids['threshold_now'].state = 'normal'

    def setup_autostim(self, *args):
        """
        placeholder for parent setup function, called on start
        """
    
    def on_motion(self, etype, me):
        super().on_motion(etype, me)
        return True



# Testing
if __name__ == "__main__":
    import numpy as np

    def make_data():
        span = 3600
        f = 64
        t = time.time()
        data = {"time": np.linspace(t - span, t, span * f),
                "OIS Signal": np.random.random(span * f),
                "Motion Ang. X": np.random.random(span * f) * 16 - 8,
                }
        return data

    class SIO():
        recording_name = "test"
        add_note = lambda *x: print(*x)
        pass

    class MyApp(App):
        IO = SIO()

        def build(self):
            self.panel = AutoStimPanel()
            self.panel.autostim.data = make_data()
            Clock.schedule_interval(self.make_data, 1)
            return self.panel

        def make_data(self, *args):
            self.panel.autostim.data = make_data()

    app = MyApp()
    app.run()

