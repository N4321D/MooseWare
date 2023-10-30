"""
Recorder for internal bus of RPi in similar styles as the driver for external recording 
on micro controlelrs
"""

from subs.log import create_logger

logger = create_logger()

from multiprocessing import Queue

import sched
from threading import Lock
import time



def log(message, level="info"):
    cls_name = "RECORDER"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here


# import sensors from driver
TODO create new drivers and chip_d based on RPI pico system
try:
    from subs.driver.sensors import (
        sensTest,
        get_pars,
        chip_d,
        chip_d_short_name,
        datatypes,
        get_connected_chips_and_pars,
        get_connected_chips,
        shared_vars,
        ReadWrite,
        TESTING,
    )

except Exception as e:
    log("Sensor import error: {}".format(e), "warning")
    from driver.sensors import (
        sensTest,
        get_pars,
        chip_d,
        datatypes,
        get_connected_chips_and_pars,
        shared_vars,
        ReadWrite,
        TESTING,
    )


class FakeSerial():
    """
    This class 'fakes' serial communication with queues to keep interface
    classes the same for internal and external devices. The queues also enable
    running the recorder on a seperate core

    """
    q_in = Queue()
    q_out = Queue()
    CLOSED = False                  # is set to True if queue is closed -> app exit

    def __init__(self) -> None:
        self.CLOSED = False
        self.readStringUntil = lambda *x: self.read()

    def available(self):
        return not self.q_in.empty()

    def read(self, *args):
        if not self.q_in._closed():
            return self.q_in.get_nowait()
        else:
            self.CLOSED = True

    def println(self, line):
        if not self.q_out._closed:
            self.q_out.put_nowait(line)
        else:
            self.CLOSED = True

class Recorder():
    # IO variables
    doc_out = {}  # outgoing data as python dict or json
    doc_in = {}  # incoming data as python dict or json

    # sensor list
    I2CSensor = chip_d  # dict with i2c sensors and interfaces to sample

    # sampling counter
    callCounter = 0  # counts the number of calls to ImterHandler by interupt clock
    loopCounter = 0  # counts the number of finished loop calls
    loopBehind = 0  # difference between callCoutner & loopCounter
    increaseCounter = 0 # count number of loops that sampling is 2x faster and sample speed can be increased

    # timers
    loopStart = 0  # timepoint of start of loop
    lastLoop = 0  # start time of last loop
    startTime = 0  # start of recording in micros

    dt = 0  # duration of loop
    sampleDT = 0  # time needed to sample sensors

    START = False

    NAME = "Internal"  # Name of interface

    Serial = None   # Placeholder for Faked Serial interface


    # settings
    settings = {
        "timer_freq_hz": 256,  # timer freq in Hz (start freq)
        "current_timer_freq_hz": 0,  # actual timer freq
        "min_freq_hz": 1.0,  # minimal sample frequency in Hz
        "idle_freq_hz": 2.0,  # frequency of idle loop (checking which sensors are connected)
        "loops_before_adjust": 0,  # number of loops too slow or fast before adjusting (is set in set freq)
        "TIME_SEC_BEFORE_ADJUST": 1,  # time in seconds before adjusting sample f, change here to set
    }

    # feedback texts
    texts = {
        "idle": "Standby...",
        "rec": "Recording...",
        "defaultName": "Internal",
    }

    def __init__(
        self,
    ):
        # init serial
        self.Serial = FakeSerial()

        # check chips
        [chip.whois() for chip in self.I2CSensor.values()]

        # setup
        self.setup()
        self._setup_interrupts()

    def timerHandler(self, *args):
        callCounter += 1

    def setLed(self, state):
        # set led to state if led is present onboard
        pass

    def feedback(self, txt):
        print("TODO feedback", txt)

    def feedbackstats(self, txt):
        print("Feedback stats", txt)

    def adjustFreq(self, freq):
        if not (self.settings["min_freq_hz"] <= freq <= self.settings.timer_freq_hz):
            return
        self.feedbackstats(f"{freq:.1f} Hz")

        # limit loops before adjust to 10 if sample rate is lower than TIME BEFORE ADJUST
        if freq > 10:
            self.settings["loops_before_adjust"] = self.settings[
                "TIME_SEC_BEFORE_ADJUST"
            ]
        else:
            self.settings["loops_before_adjust"] = 10

        self.settings.current_timer_freq_hz = freq
        self.loopCounter = self.callCounter

    def sample(self):
        # trigger sensor reset if needed
        [
            sens.check_and_trigger()
            for sens in self.I2CSensor.values()
            if (sens.connected and sens.record)
        ]

        # sample sensors
        [
            sens.sample()
            for sens in self.I2CSensor.values()
            if (sens.connected and sens.record)
        ]

        # read data
        self.doc_out = {
            "time": time.time(),
            "sDt": self.sampleDT,
            **{
                sens_name: sens.getSampledData()
                for sens_name, sens in self.I2CSensor.values()
                if (sens.connected and sens.record)
            },
        }
        self.sendData()
    
    def idle(self):
        """
        idle loop that checks if sensors are connected etc
        """
        # asjust freq to idle freq:
        if self.settings["current_timer_freq_hz"] != self.settings["idle_freq_hz"]:
            self.adjustFreq(self.settings["idle_freq_hz"])

        self.feedback(self.texts["idle"])

        # test sensors & stop if running
        [(sens.test_connection(), sens.stop()) for sens in self.I2CSensor.values()]

        # get data from sensors
        self.doc_out = {
            "idle": True,
            "CTRL": {"name": self.NAME},
            **{sens_name: sens.getInfo() for sens_name, sens in self.I2CSensor.items()},
        }
        self.sendData()

    def run(self):
        """
        called when starting recording, inits sensors etc
        """
        self.feedback(self.texts["rec"])

        # start sensors
        [sens.init() for sens in self.I2CSensor.values()]

        # set sampling freq
        self.adjustFreq(self.settings["timer_freq_hz"])

    def procCmd(self, cmd):
        if not isinstance(cmd, dict):
            print("unknown cmd: ", cmd)
            return

        # split commands in controller and sensor commands and send to processing functions:
        [
            self.control(k, v) if k == "CTRL" else self.I2CSensor[k].doCmd(v)
            for k, v in cmd.items()
        ]
    
    def control(self, key, value):
        """
        Instructions for controller

        Args:
            key (str): name of setting to change
            value: new value for setting
        """

        if key == 'freq':
            self.settings['timer_freq_hz'] = value
            self.adjustFreq(value)

        elif key == 'run':
            self.START = bool(value)
            self.run() if self.START else self.idle()
        
        elif key == "name":
            self.setName(value)
    
    def setName(self, name):
        self.NAME = name
        self.feedback(name)
        print("TODO save name in settings?")
    
    def loadName(self):
        print("TODO load name from settings")

    def readInput(self):
        while self.Serial.available():
            # read inputs
            self.doc_in  = self.Serial.read()

            # process inputs
            [self.procCmd(k, v) for k, v in self.doc_in.items()]
    
    def sendData(self):
        self.Serial.println(self.doc_out)
    
    def setup(self):
        self.loadName()

        # TODO: setup i2c bus here?
        
        # set freq
        self.adjustFreq(self.settings['idle_freq_hz'])

        self.startTime = time.time()
        self.loopCounter = self.callCounter - 1

    def loop(self):
        # read input data
        self.readInput()

        self.loopBehind = self.callCounter - self.loopCounter

        if not self.loopBehind:
            # next time point was not called yet
            return
        
        self.loopStart = time.perf_counter_ns() // 1000
        self.loopCounter += 1

        # run idle if START is not set
        if not self.START:
            return self.idle()
        
        # sample:
        self.sample()
        self.sampleDT = time.perf_counter_ns() // 1000 - self.loopStart

        # Blink Led every 0.5 seconds
        # if not (self.callCounter % (self.settings['current_timer_freq_hz'] // 2)):
        #     self.setLed()

        # TIMING:
        if self.loopBehind > self.settings['loops_before_adjust']:
            self.adjustFreq(self.settings['current_timer_freq_hz'] / 2)
        
        if self.settings['current_timer_freq_hz'] < self.settings['timer_freq_hz']:
            self.lastLoop = self.loopStart
        
        self.dt = time.perf_counter_ns() // 1000 - self.loopStart

        # increase speed if dt is short enough 
        if (1_000_000 / (self.dt + 10)) > (self.settings['current_time_freq_hz'] * 2):
            if self.settings['current_timer_freq_hz'] * 2 <= self.settings['timer_freq_hz']:
                self.increaseCounter += 1
                if self.increaseCounter >= self.settings['loops_before_adjust']:
                    self.increaseCounter = 0
                    self.adjustFreq(self.settings['current_timer_freq_hz'] * 2)


    # INTERRUPT TIMER
    def _run_loop(self):
        """
        runs timing and loop functions repeatedly
        """
        self.timerHandler()

        # do not execute loop if another loop is still running
        if self._interupt_lock.locked():
            return
        
        # Run loop with lock
        with self._interupt_lock:
            self.loop()
    

    def _periodic_call_abs(self, scheduler, action, actionargs=()):
        """
        creates repeated scheduler that calls the _run_loop function
        calls are scheduled based on current time + sample freq in seconds
        """

        if self.Serial.CLOSED:
            [self._scheduler.cancel(e) for e in self._scheduler.queue]
            return
        self._next_time += (1 / self.settings['current_timer_freq_hz']) # add current freq in sec for next step
        self._scheduler.enterabs(
            self._next_time, 
                           0, 
                           self._periodic_call_abs,
                           (self._scheduler, action, actionargs)) # schedule the next call
        action(*actionargs) # execute the action

    def _setup_interrupts(self):
        """
        sets up scheduler, lock and timers for interrupt timer
        """
        self._scheduler = sched.scheduler(time.perf_counter, time.sleep)
        self._next_time = time.perf_counter()
        self._interupt_lock = Lock()
        self._periodic_call_abs(self._scheduler, self._run_loop) # start the periodic task
        self._scheduler.run()
    
if __name__ == '__main__':
    ...