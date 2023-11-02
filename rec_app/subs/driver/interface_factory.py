"""
scanner that scans if interfaces are connected
and integrates them into IO
"""


from serial import list_ports

from subs.driver.interfaces import Interface
from subs.driver.interface_drivers.internal import InternalController

import asyncio

from subs.log import create_logger

logger = create_logger()

def log(message, level="info"):
    cls_name = "INTERFACE FACT"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here


class InterfaceFactory():
    SCAN_DT = 0.5
    EXIT = asyncio.Event()                        # exit flag
    DEVICES = r'Adafruit ItsyBitsy M4|Pico.*Board CDC|Nano 33 BLE'    # regex to select devices
    BAUDRATE = 20_000_000


    def __init__(self, interfaces) -> None:
        self.interfaces = interfaces

    async def scan_usb(self):
        while not self.EXIT.is_set():
            try:
                self.serial_device = next(list_ports.grep(self.DEVICES))
                port = self.serial_device.device
                log(f"connecting to: {self.serial_device}", "info")

                await self._setup_reader(self.serial_device)
                log(f"connected to {self.serial_device.manufacturer} "
                        f"{self.serial_device.description} at {port}", "info")
                self.disconnected.clear()
                self.connected.set()
                await self.disconnected.wait()          # stop until disconnected again


            except StopIteration:
                # No usb device found
                pass

            await asyncio.sleep(self.SCAN_DT)
    
    def exit(self):
        self.EXIT.set()