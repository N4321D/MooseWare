"""
interface driver for RPi internal i2c / GPIO etc interface
"""
import asyncio


from kivy.event import EventDispatcher
from kivy.clock import Clock

# import internal chip stuff
from subs.recording.recorder import Recorder, chip_d_short_name, get_connected_chips_and_pars, ReadWrite, TESTING, shared_vars, get_connected_chips
from subs.gui.vars import MAX_MEM

import json


class InternalInterface(EventDispatcher):

    # TODO Finish this for internal chips

    connected = True
    disconnected = False

    recv_buff = []
    name = "Internal"

    _internal_control_str = ("[{\"title\": \"Recording Frequency\","
                                "\"type\": \"plusminin\","
                                "\"desc\": \"Recording Frequency (Hz)\","
                                "\"key\": \"freq\","
                                "\"steps\": [[1, 32, 8], [32, 64, 32], [64, 128, 64], [128, 256, 128], [256, 512, 256], [512, 1024, 256], [1024, 2048, 512]]," 
                                "\"limits\": [1, 2048]}"
                                "]")
    
    _recording = False
    _rec_freq = 256
    _recorder = None        # placeholder for recorder class
    _rec_pr = None          # placeholder for multiprocessing Process class of recording

    def __init__(self,  **kwargs) -> None:
        self.__dict__.update(kwargs)
        self.loop_event = Clock.schedule_interval(self._loop, 0.5)

        # Clock.schedule_once(self.on_connect, 0)
        Clock.schedule_once(lambda dt: asyncio.run_coroutine_threadsafe(self.on_connect(self), 
                                                                        asyncio.get_event_loop()), 
                                                                        0) 

    async def on_connect(self, *args, **kwargs):
        pass

    def on_disconnect(self, *args, **kwargs):
        pass

    def start(self, *args, **kwargs):
        print("Internal interface start called")

    def stop(self, *args, **kwargs):
        print("Internal interface stop called")

    def write(self, data):
        print(f"{self.name} - writing to sensor: {data}")

        for chip_name, cmd in json.loads(data).items():
            # unpack outgoing data and send / process it
            # instruction for Internal controller:
            if chip_name == "CTRL":
                # start recording
                if cmd.get("run") == 1:
                    self._recording = True
                    self._recorder = Recorder(start_rate=self._rec_freq, 
                                              MAX_MEM=MAX_MEM)
                    self._rec_pr = self._recorder.start()

                # stop recording
                if cmd.get("run") == 0:
                    self._recording = False
                    if self._recorder is not None:
                        self._recorder.stop()
                        self._rec_pr.join()
                        self._rec_pr = None                    

                # change recording frequency
                freq = cmd.get("freq")
                if freq:
                    # TODO change freq based on incoming current freq of recorder
                    self._rec_freq = freq
                    self.recv_buff.append(f"{freq} Hz\r".encode())                        

            # send to chips:
            elif chip_name in chip_d_short_name:
                for par, value in cmd:
                    if self._recording:
                        self._recorder.q_in.put(chip_name, "do_config", (par, value))
                    else:
                        chip_d_short_name[chip_name].do_config(par, value)  # send instructions to chip driver

    def _read_feedback(self):
        """
        Process feedback from Recorder
        """
        # TODO: Finish
        feedback = ... 
        self.recv_buff.append(feedback)
        self.do()

    def _loop(self, dt):
        """
        Main loop checking for new feedback or extracting idle data
        """
        if self._recording:
            self._read_feedback()
        else:
            self._idle_loop()
    
    def _idle_loop(self):
        """
        function called to extract idle data
        """
        self.recv_buff.append(
            json.dumps(
                {"idle": True,
                 "CTRL":{"name": self.name, 
                         "control_str": self._internal_control_str},
                 **{chip.short_name: chip.get_idle_status() 
                        for chip in chip_d_short_name.values()}
                    }
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