"""
Recorder for internal bus of RPi in similar styles as the driver for external recording 
on micro controlelrs
"""

from subs.log import create_logger

logger = create_logger()

import time


def log(message, level="info"):
    cls_name = "RECORDER"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here


# import sensors from driver
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


class Recorder:
    # IO variables
    doc_out = {}  # outgoing data as python dict or json
    don_in = {}  # incoming data as python dict or json

    # sensor list
    I2CSensor = chip_d  # dict with i2c sensors and interfaces to sample

    # sampling counter
    callCounter = 0  # counts the number of calls to ImterHandler by interupt clock
    loopCounter = 0  # counts the number of finished loop calls
    loopBehind = 0  # difference between callCoutner & loopCounter

    # timers
    loopStart = 0  # timepoint of start of loop
    lastLoop = 0  # start time of last loop
    startTime = 0  # start of recording in micros

    dt = 0  # duration of loop
    sampleDT = 0  # time needed to sample sensors

    START = False

    NAME = "Internal"  # Name of interface

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
        # check chips
        [chip.whois() for chip in self.I2CSensor.values()]

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

    def idle(self):
        """
        idle loop that checks if sensors are connected etc
        """
        # asjust freq to idle freq:
        if self.settings["current_timer_freq_hz"] != self.settings["idle_freq_hz"]:
            self.adjustFreq(self.settings["idle_freq_hz"])

        self.feedback(self.texts["idle"])

        # test sensors
        [sens.test_connection() for sens in self.I2CSensor.values()]

        # send current controller parameters
        self.doc_out = {
            "idle": True,
            "CTRL": {"name": self.NAME},
            **{sens_name: sens.getInfo() for sens_name, sens in self.I2CSensor.items()},
        }

    def run(self):
        """
        called when starting recording, inits sensors etc
        """
        self.feedback(self.texts['rec'])
    
