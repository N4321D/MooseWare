"""
scanner that scans if interfaces are connected
and integrates them into IO
"""


from serial.tools import list_ports

from subs.driver.interfaces import Interface
from subs.driver.interface_drivers.internal import InternalController
from subs.driver.interface_drivers.serial_controller import SerialController

import asyncio

from subs.log import create_logger

logger = create_logger()


def log(message, level="info"):
    cls_name = "INTERFACE FACT"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here


class InterfaceFactory:
    SCAN_DT = 1
    EXIT = asyncio.Event()  # exit flag
    DEVICES = (
        r"Adafruit ItsyBitsy M4|Pico.*Board CDC|Nano 33 BLE"  # regex to select devices
    )
    BAUDRATE = 20_000_000

    device_change_event = asyncio.Event()

    def __init__(
        self,
        on_connect=lambda *x: x,
        on_disconnect=lambda *x: x,
        EXIT=None,
    ) -> None:
        if EXIT:
            self.EXIT = EXIT

        self.external_on_connect = on_connect
        self.external_on_disconnect = on_disconnect

        # add always connected interfaces to connected devices
        self.connected_devices = (
            {}
        )  # dictionary with port as key and task of connecting or connected interface if connected as value

    async def scan(self):
        """
        Scan for USB devices and update the connected devices.

        This function runs a loop that checks for USB devices using the check_usb method and sleeps for a specified interval. It also awaits the tasks stored in the self.tasks attribute. The loop exits when the self.EXIT event is set.

        Args:
            self (DeviceManager): The instance of the DeviceManager class.

        Returns:
            Awaitable[None]: An awaitable object that resolves when the scan loop is finished.
        """
        log("scanning for devices", "info")
        int_interface_task = asyncio.create_task(self.create_internal_interfaces())
        self.device_change_event.set()

        while not self.EXIT.is_set():
            result = await asyncio.gather(
                self.check_usb(), asyncio.sleep(self.SCAN_DT), return_exceptions=True
            )

        # stop:
        int_interface_task.cancel()
        self.exit()

    async def check_usb(self) -> None:
        """
        Check for USB devices and update the connected devices.

        This function gets the current USB ports and compares them with the
        connected devices dictionary. It removes the disconnected devices using
        the remove_usb_interface method and creates new devices using the
        create_serial_interface method.
        """
        usb_ports = set(p.device for p in list_ports.comports())
        new_devices = usb_ports.difference(self.connected_devices)
        disconnected_devices = set(self.connected_devices).difference(usb_ports)

        if not any(new_devices) or not any(disconnected_devices):
            return

        # remove old devices
        [self.remove_usb_interface(d) for d in disconnected_devices]

        for d in new_devices:
            self.connected_devices[d] = asyncio.create_task(
                self.create_serial_interface(d)
            )

        self.device_change_event.set()  # flag that devices are connected or disconnected

    async def create_serial_interface(
        self,
        port: str,
    ) -> None:
        """
        Create and start a serial interface for the given port.

        This function creates an Interface object with the given port,
        on_connect, and on_disconnect callbacks, and a SerialController.
        It then awaits the interface's async_start method and adds it to the
        connected_devices dictionary.

        Args:
            port (str): The serial port to connect to.

        """
        interface = Interface(
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
            Controller=SerialController,
            device=port,
        )
        await interface.async_start()
        self.connected_devices[port] = interface

    def remove_usb_interface(
        self,
        dev: str,
    ):
        """
        Remove a USB interface from the connected devices.

        This function checks if the specified device is an asyncio task
        or an Interface instance and performs the appropriate cancellation
        or exit operation before removing it from the connected devices dictionary.

        Parameters:
        - self (DeviceManager): The instance of the DeviceManager class.
        - dev (str): The device identifier used to reference the connected device.

        Returns:
        - None
        """
        if isinstance(self.connected_devices[dev], asyncio.Task):
            self.connected_devices[dev].cancel()

        if isinstance(self.connected_devices[dev], Interface):
            self.connected_devices[dev].exit()

        del self.connected_devices[dev]

    async def create_internal_interfaces(self) -> None:
        """
        Connect all permanently connected / internal interfaces here suchs as i2c bus,
        camera, network etc.
        """
        interfaces = []

        async def init_interface(interface):
            await interface.async_start()
            self.connected_devices["internalbus"] = interface

        interfaces.append(
            Interface(
                on_connect=self.on_connect,
                on_disconnect=self.on_disconnect,
                Controller=InternalController,
                device="internalbus",
            )
        )
        asyncio.gather(
            *[init_interface(interface) for interface in interfaces],
            return_exceptions=True,
        )

    def on_connect(self, interface):
        self.external_on_connect(interface)

    def on_disconnect(self, interface):
        self.external_on_disconnect(interface)

    async def connect(self):
        try:
            port = self.serial_device.device
            log(f"connecting to: {self.serial_device}", "info")

            await self._setup_reader(self.serial_device)
            log(
                f"connected to {self.serial_device.manufacturer} "
                f"{self.serial_device.description} at {port}",
                "info",
            )
            self.disconnected.clear()
            self.connected.set()
            await self.disconnected.wait()  # stop until disconnected again

        except StopIteration:
            # No usb device found
            pass

    def exit(self):
        pass
