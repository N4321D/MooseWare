import serial
import serial_asyncio
from serial.tools import list_ports

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

# import internal chip stuff
from subs.recording.recorder import Recorder, chip_d_short_name, get_connected_chips_and_pars, ReadWrite, TESTING, shared_vars, get_connected_chips


# Logger
from subs.log import create_logger
logger = create_logger()
def log(message, level="info"):
    cls_name = "SERIAL_CONTROLLER"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here

from subs.gui.vars import MAX_MEM



class IOProtocol(asyncio.Protocol):
    buffer = []
    sub_buffer = bytearray()  # sub buffer to cache incoming data until '\n is found'
    parent = None
    transport = None

    RECV_BUFFER_SIZE = 10000
    DELIMITER = b'\n'

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
        super().__init__()

    def connection_made(self, transport):
        self.transport = transport
        transport.serial.rts = False  # You can manipulate Serial object via transport

    def connection_lost(self, exc):
        self.on_connection_loss()

    def data_received(self, data):
        self.save(data)

    def save(self, data):
        self.sub_buffer.extend(data)
        if self.DELIMITER in self.sub_buffer:
            *_buff, self.sub_buffer = self.sub_buffer.split(self.DELIMITER)
            self.buffer.extend(_buff)
            self.do()

        if len(self.buffer) > self.RECV_BUFFER_SIZE:
            del self.buffer[0]

    def write(self, data):
        if self.transport is not None:
            self.transport.write(data)

    def write_lines(self, data):
        if self.transport is not None:
            self.transport.writelines(data)

    def pause_reading(self):
        # This will stop the callbacks to data_received
        self.transport.pause_reading()

    def resume_reading(self):
        # This will start the callbacks to data_received again with all data that has been received in the meantime.
        self.transport.resume_reading()

    def pause_writing(self):
        print(
            f'pause writing; buffer: {self.transport.get_write_buffer_size()}')
        self.on_write_pause()

    def resume_writing(self):
        print(
            f'resume writing; buffer: {self.transport.get_write_buffer_size()}')
        self.on_write_resume()

    def do(self):
        """
        placeholder for function which is called with new data
        """
        pass

    def on_connection_loss(self):
        """
        placeholder for what is called when connection is lost
        """
        pass

    def on_write_pause(self):
        """
        called when writing is paused
        """
        pass

    def on_write_resume(self):
        """
        called when writing is paused
        """
        pass


class Arduino():
    protocol = None
    transport = None

    recv_buff = []
    write_buffer = []

    # indicates that usb dev is disconnected
    disconnected = asyncio.Event()
    connected = asyncio.Event()

    device = None                                   # placeholder for device
    name = ''

    EXIT = asyncio.Event()                     # exit flag
    SCAN_DT = 1                                   # dt for usb scan
    DEVICES = r'Adafruit ItsyBitsy M4|Pico.*Board CDC|Nano 33 BLE'    # regex to select devices
    BAUDRATE = 20_000_000

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
        self.EXIT.clear()

    async def start(self) -> None:
        log("scanning for devices", "info")
        await self.scan_usb()

    async def scan_usb(self):
        while not self.EXIT.is_set():
            try:
                self.device = next(list_ports.grep(self.DEVICES))
                port = self.device.device
                log(f"connecting to: {self.device}", "info")

                await self._setup_reader(self.device)
                print(f"connected to {self.device.manufacturer} "
                      f"{self.device.description} at {port}")
                self.disconnected.clear()
                self.connected.set()
                await self.disconnected.wait()          # stop until disconnected again


            except StopIteration:
                # No usb device found
                pass

            await asyncio.sleep(self.SCAN_DT)
        
    def _on_connection_loss(self):
        self.disconnected.set()
        self.EXIT.set()
        self.connected.clear()
        self.on_disconnect(self)
        self.device is None
        self.name = ''
        
    async def _setup_reader(self, dev):
        baudrate = self.BAUDRATE  # min(self.BAUDRATE, max(dev.BAUDRATES))
        print(f"connecting to {dev.device}, baudrate: {baudrate}")
        self.transport, self.protocol = await (serial_asyncio
                                               .create_serial_connection(
                                                   asyncio.get_event_loop(),
                                                   IOProtocol,
                                                   dev.device,
                                                   baudrate=baudrate,
                                                   parity=serial.PARITY_NONE,
                                                   stopbits=serial.STOPBITS_ONE)
                                               )
        self.recv_buff = self.protocol.buffer
        self.protocol.do = self.do
        self.protocol.on_connection_loss = self._on_connection_loss
        self.protocol.on_write_pause, self.protocol.on_write_resume = self.on_write_pause, self.on_write_resume

        self.name = f"{dev.manufacturer} - {dev.product}"
        await self.on_connect(dev)

    def do(self, *args, **kwargs):
        '''
        placeholder for function called with new data
        # TODO: run async? 
        '''
        pass

    def write(self, data):
        if not self.protocol:
            return
        if isinstance(data, (list, tuple, set)):
            self.protocol.write_lines(data)
        else:
            if isinstance(data, str):
                data = data.encode()
            self.protocol.write(data + b"\n")

    def get_fifo(self):
        """
        get first received data
        """
        if self.recv_buff:
            return self.recv_buff.pop(0)
        

    async def on_connect(self, dev):
        """
        called when connected
        """
        print("connected")
        pass

    def on_disconnect(self):
        """
        called when disconnected
        """
        print("disconnected")
        pass

    def on_write_pause(self):
        """
        called when writing is paused
        """
        print("writing paused")
        pass

    def on_write_resume(self):
        """
        called when writing is paused
        """
        print("writing resumed")
        pass

    def stop(self):
        self.EXIT.set()

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
            # self.recv_buff.append(
            #     json.dumps(
            #         {"idle": True,
            #          "CTRL": {"name": self.name}}
            #     )
            # )
        self.do()

    def do(self, *args, **kwargs):
        pass

    def get_fifo(self):
        """
        get first received data
        """
        if self.recv_buff:
            return self.recv_buff.pop(0)

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
            self.micro = Arduino(do=self.on_incoming,
                                 on_connect=self._on_connect,
                                 on_disconnect=self._on_disconnect,
                                 )
        self.disconnected = self.micro.disconnected
        self.connected = self.micro.connected

        self.shared_buffer = SharedBuffer()
        self.delme = []

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
            data = self.micro.get_fifo()

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