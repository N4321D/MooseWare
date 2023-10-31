import asyncio
import json
from json import JSONDecodeError

import time

from subs.recording.buffer import SharedBuffer

from subs.driver.sensor_files.chip import Chip

import numpy as np

from kivy.event import EventDispatcher
from kivy.app import App
from kivy.clock import Clock

from subs.driver.interface_drivers.pico import Pico
from subs.driver.interface_drivers.dummy import DummyMicro
from subs.driver.interface_drivers.internal import InternalInterface



# Logger
from subs.log import create_logger
logger = create_logger()
def log(message, level="info"):
    cls_name = "SERIAL_CONTROLLER"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here

from subs.gui.vars import MAX_MEM



class Interface():
    """
    A class representing an interface for microcontroller devices

    Attributes:
        MAX_MEM (float): The maximum memory buffer that can be used.
        dtypes (dict): A dictionary specifying the data types for saving.
        sensors (dict): A dictionary of connected sensors.
        parameters (set): A set of parameter names.
        data_dtype_fields (dict): The dtype fields of the current data.
        name (str): The name of the controller.
        disconnected (asyncio.Event): An event indicating if the controller is disconnected.
        connected (asyncio.Event): An event indicating if the controller is connected.
        starttime (float): The start time of the controller.
        lasttime (float): The last recorded time.
        run (bool): Indicates if the controller is running.
        samplerate (int): The sample rate of the controller.
        emarate (float): The theoretical maximum of the EMA (Exponential Moving Average) rate.
        current_rate (int): The current sample rate.
        buffer_length (int): The length of the buffer.
        micro (MicroController): The microcontroller object.
        shared_buffer (SharedBuffer): The shared buffer object.

    Methods:
        connect_buffer(): Connects the buffer and sets the data structure.
        set_buffer_dims(data): Sets the dimensions of the buffer.
        async_start(): Asynchronously starts the controller.
        start_stop(start=None): Starts or stops the controller.
        adjust_freq(freq): Adjusts the sample frequency of the controller.
        _on_connect(dev): Callback function when the controller is connected.
        on_connect(dev): Callback function when the controller is connected.
        _on_disconnect(dev): Callback function when the controller is disconnected.
        on_disconnect(dev): Callback function when the controller is disconnected.
        on_incoming(): Handles incoming data from the microcontroller.
        do_idle(data): Processes idle data received from the microcontroller.
        do_new_data(data): Processes new data received from the microcontroller.
        save_data(data): Saves the data in memory.
        do_feedback(data, e): Handles feedback messages received from the microcontroller.
        set_dev(dev): Sets the connected device information.
        _do_time(data): Processes the timestamp of the data.
        _calc_ema(dt): Calculates the Exponential Moving Average (EMA) rate.
        exit(): Stops the controller and performs cleanup operations.
    """
    # Max memory buffer can use, can be overwritten by  IO class with actual mem limit defined in vars.py
    MAX_MEM = 128e6

    # specify dtypes for saving
    dtypes = {
        "time": "f8",
        "us": "u4",
        "sDt": "u2",
        None: "f4"
    }

    def __init__(self, testing=False, **kwargs) -> None:
        self.sensors = {}
        self.parameters = {}
        self.data_dtype_fields = {}
        self.name = None
        self.disconnected = asyncio.Event()
        self.connected = asyncio.Event()
        self.starttime = 0
        self.lasttime = None

        self.record = True               # enable or disable recording from controller
        self.run = False
        self.samplerate = 256            # start sample rate
        self.emarate = 0                 # theoretical max
        self.current_rate = 0            # current sample rate
     
        # length of buffer (will be calculated from buffer_time * startrate)
        self.line_buffer = np.array([])
        self.buffer_length = 0
        self.__dict__.update(kwargs)
        self.app = App.get_running_app()

        if testing:
            self.micro = DummyMicro(do=self.on_incoming,
                                    on_connect=self._on_connect,
                                    on_disconnect=self._on_disconnect,)

        else:
            self.micro = Pico(do=self.on_incoming,
                                 on_connect=self._on_connect,
                                 on_disconnect=self._on_disconnect,
                                 )
        self.disconnected = self.micro.disconnected
        self.connected = self.micro.connected

        self.shared_buffer = SharedBuffer()

    def connect_buffer(self):
        self.data_structure = self.shared_buffer.data_structure
        self.buffer = self.shared_buffer.buffer

        if self.name in self.buffer:
            # clear existing data
            self.shared_buffer.reset(par=self.data_name)

    def set_buffer_dims(self, *args):
        bytes_per_samplepoint = self.line_buffer.nbytes
        

        self.buffer_length = int(self.MAX_MEM / bytes_per_samplepoint)
        self.shared_buffer.add_parameter(self.name, self.line_buffer.dtype, 
                                         self.buffer_length)

        self.parameters = set(self.line_buffer.dtype.names)

    async def async_start(self):
        await self.micro.start()

    def start_stop(self, start=None):
        if start is not None:
            self.run = start
        else:
            self.run = not self.run

        out = {"run": int(self.run)}

        if self.run:
            # Start
            self.lasttime = None
            self.starttime = time.time()
            self.emarate = 0
            out["freq"] = self.samplerate

        else:
            # Stop
            self.starttime = 0
        
        # clear / reset buffers
        self.buffer_length = 0
        self.micro.recv_buff.clear()

        # write start
        self.micro.write(json.dumps({"CTRL": out}))

        self.sensors['CTRL'].status = 5 if self.run else 0

    def adjust_freq(self, freq):
        self.samplerate = freq
        self.micro.write(json.dumps({"CTRL": {"freq": freq}}))
        self.current_rate = freq

    async def _on_connect(self, dev):
        while self.name is None:
            await asyncio.sleep(0.1)

        self.connect_buffer()
        self.sensors["CTRL"] = Chip(
                "CTRL", 
                {"name": "Controller",
                 "control_str": json.dumps([
                     {
                    "title": "Controller Name",
                    "type": "string",
                    "desc": "set / change the name of the controller",
                    "key": "name",
                    },
                     {"title": "Recording Frequency",
                    "type": "plusminin",
                    "desc": "Recording Frequency (Hz)",
                    "key": "freq",
                    "steps": [[1, 32, 8], [32, 64, 32], [64, 128, 64], [128, 256, 128], [256, 512, 256], [512, 1024, 256], [1024, 2048, 512]], 
                    "limits": [1, 2048],                            
                    "live_widget": True}]),
                 "#ST": 0,
                 "parameter_names": [],
                 "parameter_short_names": []}, 
            self, 
            send_cmd=self._send_cmd)

        self.sensors['CTRL'].name = self.name

        self.on_connect(self)

    def on_connect(self, dev):
        pass

    def _on_disconnect(self, dev):
        self.on_disconnect(self)
        self.name = ""

    def on_disconnect(self, dev):
        pass

    def on_incoming(self):
        # TODO speed_up by making async? -> on incoming sets flag and when flag is set 
        #       get fifo is async or multiprocessing processed?
        while True:
            data = self.micro.read()

            if data is None:
                return

            try:
                # process jsons
                data = json.loads(data)
                if "idle" in data:
                    self.do_idle(data)
                    
                else:
                    # incoming data
                    self.do_new_data(data)

            except (JSONDecodeError, TypeError) as e:
                # no a json but feedback message
                self.do_feedback(data, e)

    def do_idle(self, data):
        data.pop("idle")

        if self.name is None and "CTRL" not in data:
            return # wait for control pars to be received first

        for name, chip_d in data.items():
            status = chip_d.pop('#ST') if '#ST' in chip_d else 0
            if name not in self.sensors:
                self.sensors[name] = Chip(name, chip_d, self)

            else:
                self.sensors[name].update(chip_d)

            self.sensors[name].status = status
            if name == "CTRL":
                [setattr(self, k, v) for k, v in chip_d.items()]

        self.parameters = {f"{k}_{par}": k for k, chip in self.sensors.items() if (chip.status >= 0 and chip.record and hasattr(chip, 'parameter_short_names'))
                           for par in chip.parameter_short_names 
                           }   

    def do_new_data(self, data):
        data['time'] = self._do_time(data['us'])

        self._calc_ema(data.pop('sDt'))

        if self.buffer_length == 0:
            self.create_line_buffer(data)

            # create buffer based on incoming data
            self.set_buffer_dims()
            
            # save dtype of current data
            self.data_dtype_fields = self.line_buffer.dtype.fields
        
        
        _last_chip = ""
        # unpack dictionary
        for parname in self.data_dtype_fields:
            par, *subpar = parname.split("_")
            val = data.get(par, np.nan)
            
            if isinstance(val, dict):
                # add data to line buffer
                self.line_buffer[parname] = val.get(subpar[0], np.nan)
                # get status
                if par != _last_chip:
                    _status = val.get('#ST')
                    if _status is not None:
                        self.sensors[par].status = _status
                    _last_chip = par
            else:
                # add data to line_buffer
                self.line_buffer[par] = val
                
        self.save_data()
        

    def create_line_buffer(self, data):
        dtypes = []
        
        sensors = self.sensors
        for par, val in data.items():
            if isinstance(val, dict):
                _status = val.get("#ST")
                if par in sensors:
                    if _status is not None:
                        sensors[par].status = _status
                else:
                    sensors[par] = Chip(par, {"status":  _status if _status is not None else 0}, self)
                if  _status is None or _status >= 0:
                    # if status is ok, add dtype to pars
                    dtypes += [(f"{par}_{subpar}", 
                                    self.dtypes.get(subpar, self.dtypes[None]))
                                          for subpar in val]
        else:
            dtypes.append((par, self.dtypes.get(par, self.dtypes[None])))
        
        self.line_buffer = np.zeros(1, dtype=dtypes)

    def save_data(self,):
        # save data in memory
        self.shared_buffer.add_1_to_buffer(
            self.name,
            # tuple(data.values())
            self.line_buffer
        )

    def do_feedback(self, data, e):
        try:
            data = data.decode()
            if data[-4:] == " Hz\r":
                self.current_rate = float(data[:-4])
            else:
                print(f"{self.name}:    {data}")
        except:
            log(f"feedback error: {type(e)} - {e}: {data}", "info")
            self.error_data = data

    def set_dev(self, dev):
        txt = f"{dev.manufacturer} - {dev.product}" if dev else 'disconnected'
        try:
            self.root.ids.dev.text = txt
        except:
            pass

    def _do_time(self, us):
        # get microseconds
        sec = us * 1e-6

        if self.lasttime is None:
            # adjust starttime to start of rec on arduino
            self.starttime -= sec
            self.lasttime = 0

        # track last time to count loop of us
        if sec < self.lasttime:
            self.starttime += (0xFFFF_FFFF / 1e6)
        self.lasttime = sec

        t = self.starttime + sec
        return t

    def _calc_ema(self, dt):
        if dt == 0:
            return
        dt = dt / 1e6
        if self.emarate == 0:
            self.emarate = 1 / dt
        else:
            n = self.samplerate * 60   # ema over 1 min
            self.emarate = (self.emarate - (self.emarate / n)) + ((1 / dt) / n)
    
    
    def _send_cmd(self, value):
        # process controller commands / config
        try:
            self.record = value['record']
            return
        
        except (KeyError):
            value = json.dumps({'CTRL': value})
            self.micro.write(value)

    def exit(self):
        self.start_stop(False)
        self.micro.stop()


if __name__ == "__main__":
    """
    """
    from kivy.app import App
    from kivy.lang.builder import Builder
    from kivy.clock import Clock
    from datetime import datetime

    kv_str = r"""
BoxLayout:
    orientation: 'vertical'
    Label:
        id: dev
        text: app.control.micro.name if app.control.micro.name else "disconnected"
        font_size: "40sp"

    Label:
        id: txt
        text: 'incoming'
        text_size: self.size
        halign: 'left'
        valign: 'middle'
        font_size: "30sp"

    Button:
        id: butt
        text: 'Press'
        on_release: app.start_rec()

            
        
    """

    class AsyncApp(App):
        data = {}
        run_ard = False

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.loop = asyncio.get_event_loop()
            self.control = Interface()
            # self.text_event = Clock.schedule_interval(self.send_text, 1)

        def start_rec(self):
            self.control.start_stop()

        def set_dev(self, dev):
            txt = f"{dev.manufacturer} - {dev.product}" if dev else 'disconnected'
            try:
                self.root.ids.dev.text = txt
            except:
                pass

        def build(self):
            return Builder.load_string(kv_str)

        async def kivyCoro(self):
            """
            This is the method that's gonna launch your kivy app
            and 'async__init__' for app
            """

            await self.async_run(async_lib='asyncio')

        # This func will start all the "tasks", in this case the only task is the kivy app
        async def base(self):
            tasks = {asyncio.create_task(t) for t in
                     {self.kivyCoro(), self.control.async_start()}}
            done, pending = await asyncio.wait(tasks, return_when="FIRST_COMPLETED")

        def start(self):
            self.loop.run_until_complete(self.base())
            # # loop.run_until_complete(reader())
            self.loop.close()

    app = AsyncApp()  # You have to instanciate your App class
    app.start()

# TODO: use more async in protocol?