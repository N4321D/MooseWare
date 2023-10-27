"""
Interface driver for RPi pico micro controller


"""

import asyncio
import serial
import serial_asyncio
from serial.tools import list_ports


# Logger
try:
    from subs.log import create_logger
    logger = create_logger()
    def log(message, level="info"):
        cls_name = "PICO"
        getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here
except:
    log = lambda *args: print("PICO", *args)

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


class Pico():
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
