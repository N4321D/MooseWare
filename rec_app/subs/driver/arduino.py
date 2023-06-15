import serial
import serial_asyncio
from serial.tools import list_ports

import asyncio
import json
import time

from subs.recording.buffer import SharedBuffer

import numpy as np

from json import JSONDecodeError

from kivy.event import EventDispatcher
from kivy.app import App
from kivy.clock import Clock

# Logger
from subs.log import create_logger
logger = create_logger()
def log(message, level="info"):
    cls_name = "SERIAL_CONTROLLER"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here



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

        # stop callbacks again immediately
        # self.pause_reading()

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
    DEVICES = r'Adafruit ItsyBitsy M4|Pico.*Board CDC'    # regex to select devices
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
                log("connecting to: {self.device}", "info")

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
        self.on_connect(dev)

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
            self.protocol.write(data)

    def get_fifo(self):
        """
        get first received data
        """
        if self.recv_buff:
            return self.recv_buff.pop(0)
        

    def on_connect(self, dev):
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
    name = "TEST_MICRO"

    _rec_dt = 1/256

    def __init__(self,  **kwargs) -> None:
        self.__dict__.update(kwargs)

        self.data_event = Clock.schedule_interval(self._gen_data, self._rec_dt)
        self.data_event.cancel()
        self.idle_event = Clock.schedule_interval(self._gen_idle, 2)

        Clock.schedule_once(self.on_connect, 0)

    def on_connect(self, *args, **kwargs):
        pass

    def on_disconnect(self, *args, **kwargs):
        pass

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass

    def write(self, data):
        print(f"writing to micro: {data}")
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
                     "OIS": {"name": "Optical Intrisic Signal",
                             "output_text": "",
                             "i2c_status": 0,
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


class Controller():


    # Max memory buffer can use, can be overwritten by  IO class with actual mem limit defined in vars.py
    MAX_MEM = 200 * 1.024e6

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
        self.name = ""
        self.disconnected = asyncio.Event()
        self.connected = asyncio.Event()
        self.starttime = 0
        self.lasttime = None

        self.run = False
        self.samplerate = 256            # start sample rate
        self.emarate = 0                 # theoretical max
        self.current_rate = 0            # current sample rate
     
        # length of buffer (will be calculated from buffer_time * startrate)
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
                                 # on_write_pause=lambda *_: self.text_event.cancel(),
                                 # on_write_resume=lambda *_: self.text_event(),
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

    def set_buffer_dims(self, data):
        # bytes_per_samplepoint = sum([np.dtype(i[1]).itemsize for i in dtypes])
        dtypes = list({k: self.dtypes.get(k, self.dtypes[None])
                       for k in data}.items())

        # make one example row and count nbytes
        bytes_per_samplepoint = np.empty(1, dtype=dtypes).nbytes

        self.buffer_length = int(self.MAX_MEM / bytes_per_samplepoint)
        self.shared_buffer.add_parameter(self.name, dtypes, self.buffer_length)

        self.parameters = set(data.keys())

    async def async_start(self):
        await self.micro.start()

    def start_stop(self, start=None):
        if start is not None:
            self.run = start
        else:
            self.run = not self.run

        out = {"run": int(self.run)}
        if self.run:
            self.lasttime = None
            self.starttime = time.time()
            self.emarate = 0
            out["freq"] = self.samplerate

        else:
            self.starttime = 0

        self.buffer_length = 0
        self.micro.recv_buff.clear()
        self.micro.write(json.dumps({"CTRL": out}))

    def adjust_freq(self, freq):
        self.samplerate = freq
        self.micro.write(json.dumps({"CTRL": {"freq": freq}}))
        self.current_rate = freq

    def _on_connect(self, dev):
        print(f"CONNECTED TO: {self.micro.name}")
        self.name = self.micro.name
        self.connect_buffer()

        self.on_connect(self)

    def on_connect(self, dev):
        pass

    def _on_disconnect(self, dev):
        self.on_disconnect(self)
        self.name = ""

    def on_disconnect(self, dev):
        pass

    def on_incoming(self):
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

            except JSONDecodeError as e:
                # no a json but feedback message
                self.do_feedback(data, e)

    def do_idle(self, data):
        data.pop("idle")
        self.sensors = data
        self.parameters = {f"{k}_{par}": k for k, v in self.sensors.items()
                           for par in v['parameter_short_names'] if v.get("i2c_status") == 0}
        

    def do_new_data(self, data):
        data_unpacked = self._do_time(data)

        # data_unpacked = {}
        for sens in tuple(data_unpacked):
            if isinstance(data_unpacked[sens], dict):
                v = data_unpacked.pop(sens)
                _status = v.get("!I2C", 0)
                self.sensors.setdefault(sens, {})['i2c_status'] = _status

                if _status > 0:
                    # handle errors
                    continue  # do not include sensor in data

                else:
                    # upack dictionary
                    data_unpacked.update({f"{sens}_{k2}": v[k2]
                                          for k2 in v})

        if self.buffer_length == 0:
            # create buffer based on incoming data
            self.set_buffer_dims(data_unpacked)
            
            # save dtype of current data
            self.data_dtype_fields = self.shared_buffer.buffer[self.name].dtype.fields

        self.save_data(data_unpacked)
        self._calc_ema(data_unpacked['sDt'])


    def save_data(self, data):
        # get data or replace with nans
        data = tuple(data.get(k, np.nan if v[0].kind == 'f' else 0) 
                for k, v in self.data_dtype_fields.items())
        # save data in memory
        self.shared_buffer.add_1_to_buffer(
            self.name,
            # tuple(data.values())
            data
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

    def _do_time(self, data):
        # get microseconds
        sec = data['us'] * 1e-6

        if self.lasttime is None:
            # adjust starttime to start of rec on arduino
            self.starttime -= sec
            self.lasttime = 0

        # track last time to count loop of us
        if sec < self.lasttime:
            self.starttime += (0xFFFF_FFFF / 1e6)
        self.lasttime = sec

        data['time'] = self.starttime + sec
        return data

    def _calc_ema(self, dt):
        if dt == 0:
            return
        dt = dt / 1e6
        if self.emarate == 0:
            self.emarate = 1 / dt
        else:
            n = self.samplerate * 60   # ema over 1 min
            self.emarate = (self.emarate - (self.emarate / n)) + ((1 / dt) / n)

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
            self.control = Controller()
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