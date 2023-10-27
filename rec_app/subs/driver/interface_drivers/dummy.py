"""
dummy interface for testing
"""

from kivy.event import EventDispatcher
from kivy.clock import Clock

import asyncio
import json

import time
import numpy as np

class DummyMicro(EventDispatcher):
    """
    returns random data for testing
    """
    connected = True
    disconnected = False

    recv_buff = []
    name = "TEST MICRO"

    _rec_dt = 1/256

    def __init__(self,  **kwargs) -> None:
        self.__dict__.update(kwargs)
        self.data_event = Clock.schedule_interval(self._gen_data, self._rec_dt)
        self.data_event.cancel()
        self.idle_event = Clock.schedule_interval(self._gen_idle, 2)

        # Clock.schedule_once(self.on_connect, 0)
        Clock.schedule_once(lambda dt: asyncio.run_coroutine_threadsafe(self.on_connect(self), asyncio.get_event_loop()), 0) 

    async def on_connect(self, *args, **kwargs):
        pass

    def on_disconnect(self, *args, **kwargs):
        pass

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass

    def write(self, data):
        print(f"TEST_MICRO - writing to micro: {data}")
        data = json.loads(data)
        cmd = data.get("CTRL")
        if cmd:
            if cmd.get("run") == 1:
                self.idle_event.cancel()
                self.data_event()
                self.recv_buff.append(f"{1/self._rec_dt} Hz\r")


            if cmd.get("run") == 0:
                self.data_event.cancel()
                self.idle_event()

            freq = cmd.get("freq")
            if freq:
                self._rec_dt = 1 / freq
                self.data_event.timeout = self._rec_dt
                self.recv_buff.append(f"{freq} Hz\r".encode())


    def _gen_data(self, dt):
        if len(self.recv_buff) < 5:
            self.recv_buff.append(
                json.dumps(
                    {"us": time.time_ns() // 1000 & 0xFFFF_FFFF,
                     "sDt": int(self._rec_dt * 1e6),
                     "OIS": {
                        "SIG": np.random.random(),
                        "BGR": np.random.randint(0, 1000) / 100000,
                        "STIM": 0, }
                     })
            )
        self.do()

    def _gen_idle(self, dt):
        if len(self.recv_buff) < 5:
            self.recv_buff.append(
                json.dumps(
                    {"idle": True,
                     "CTRL":{"name": self.name},
                     "OIS": {"name": "Optical Intrisic Signal",
                             "control_str": json.dumps([
                            {"title": "Blue Light Stimulation",
                                  "type":"stim",
                                  "desc": "Create / Start / Stop blue light stimulation protocol",
                                  "key": "stim",},
                             {"title": "Green Led Intensity",
                             "type":"plusminin",
                             "desc": "Power in mA of the green LEDs",
                             "key": "amps",
                             "steps": [[0, 10, 1], [10, 20, 2], [20, 100, 10]], 
                             "limits": [0, 65],                            
                             "live_widget": True},
                            {"title": "Purple Light Stimulation",
                             "type":"stim",
                             "desc": "Create / Start / Stop purple light stimulation protocol",
                             "key": "purple_stim",},
                             ]),
                             "#ST": 0,
                             "parameter_names": ["OIS Background", "OIS Signal", "OIS Stimulation mA"],
                             "parameter_short_names": ["BGR", "SIG", "STIM"]}, }
                )
            )
        self.do()

    def do(self, *args, **kwargs):
        pass

    def get_fifo(self):
        """
        get first received data
        """
        if self.recv_buff:
            return self.recv_buff.pop(0)
