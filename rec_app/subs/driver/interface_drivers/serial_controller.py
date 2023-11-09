"""
Interface driver for RPi pico micro controller


"""
from subs.driver.interface_drivers.controller_template import Controller

import asyncio
import serial
import serial_asyncio
from serial.tools import list_ports

import json
from json import JSONDecodeError


# Logger
try:
    from subs.log import create_logger

    logger = create_logger()

    def log(message, level="info"):
        cls_name = "PICO"
        getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here

except:
    log = lambda *args: print("SERIAL_CTRL", *args)


class IOProtocol(asyncio.Protocol):
    sub_buffer = bytearray()  # sub buffer to cache incoming data until '\n is found'
    parent = None
    transport = None

    RECV_BUFFER_SIZE = 10000
    DELIMITER = b"\n"

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

    def save(self, incoming):
        self.sub_buffer.extend(incoming)
        if self.DELIMITER in self.sub_buffer:
            *data, self.sub_buffer = self.sub_buffer.split(self.DELIMITER)
            [self.do(d) for d in data]

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
        print(f"pause writing; buffer: {self.transport.get_write_buffer_size()}")
        self.on_write_pause()

    def resume_writing(self):
        print(f"resume writing; buffer: {self.transport.get_write_buffer_size()}")
        self.on_write_resume()

    def do(self, *args, **kwargs):
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


class SerialController(Controller):
    protocol = None
    transport = None

    # indicates that usb dev is disconnected
    disconnected = asyncio.Event()
    connected = asyncio.Event()

    device = None  # placeholder for device

    EXIT = asyncio.Event()  # exit flag
    SCAN_DT = 1  # dt for usb scan
    DEVICES = (
        r"Adafruit ItsyBitsy M4|Pico.*Board CDC|Nano 33 BLE"  # regex to select devices
    )
    BAUDRATE = 20_000_000

    async def start(self) -> None:
        await self._setup_reader(self.device)
        log(f"connected to {self.device}", "info")

    def _on_connection_loss(self):
        self.disconnected.set()
        self.EXIT.set()
        self.connected.clear()
        self.on_disconnect(self)

    async def _setup_reader(self, dev):
        log(f"connecting to {dev}, baudrate: {self.BAUDRATE}")
        
        # create transport
        self.transport, self.protocol = await serial_asyncio.create_serial_connection(
            asyncio.get_event_loop(),
            IOProtocol,
            dev,
            baudrate=self.BAUDRATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )

        # connect functions that are called on new data, and changes in connection
        self.protocol.do = self._preprocess_data
        self.protocol.on_connection_loss = self._on_connection_loss
        self.protocol.on_write_pause, self.protocol.on_write_resume = (
            self.on_write_pause,
            self.on_write_resume,
        )

        await self.on_connect_default(dev)

    def write(self, data):
        if not self.protocol:
            return
        data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode()
        self.protocol.write(data + b"\n")

    def _preprocess_data(self, data):
        try:
            data = json.loads(data)
        except (JSONDecodeError, TypeError):
            pass  # data is string (feedback etc)
        self.do(data)

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
