"""
scanner that scans if interfaces are connected
and integrates them into IO
"""


from serial.tools import list_ports

from subs.driver.interfaces import Interface
from subs.driver.interface_drivers.internal_controller import InternalController
from subs.driver.interface_drivers.serial_controller import SerialController
from subs.driver.interface_drivers.broadcast_receiver import BroadCastController

import asyncio
import traceback
from subs.log import create_logger



def extract_tb(e):
    """
    extract traceback from exception

    Args:
        e (Exception): exception to extract tb from

    Returns:
        str: traceback
    """
    return f"{type(e).__name__}: " + "".join(traceback.format_exception(e))

logger = create_logger()


def log(message, level="info"):
    cls_name = "INTERFACE FACTORY"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here


class InterfaceFactory:
    """
    A factory class for creating and managing interfaces.

    Attributes:
        SCAN_DT (int): The interval at which to scan for devices.
        EXIT (asyncio.Event): An event that signals when to exit.
    """

    SCAN_DT = 1
    EXIT = asyncio.Event()  # exit flag

    def __init__(
        self,
        on_connect=lambda *x: x,
        on_disconnect=lambda *x: x,
        EXIT=None,
        IO = None,    # Parent class
        interfaces={},  # pass interfaces of parent class
    ) -> None:
        """
        Initialize the InterfaceFactory.

        Args:
            on_connect (callable, optional): A callback function to be called when a device is connected.
            on_disconnect (callable, optional): A callback function to be called when a device is disconnected.
            EXIT (asyncio.Event, optional): An external event that signals when to exit.
        """
        if EXIT:
            self.EXIT = EXIT

        self.interfaces = interfaces
        self.IO = IO
        self.external_on_connect = on_connect
        self.external_on_disconnect = on_disconnect

        # add always connected interfaces to connected devices
        self.connected_usb_devices = (
            {}
        )  # dictionary with port as key and task of connecting or connected interface if connected as value
        self.connected_internal_devices = (
            {}
        )  # dictionary with port as key and task of connecting or connected interface if connected as value

    async def scan(self):
        """
        Scan for USB devices and update the connected devices.

        This function scans and connects all devices.
        It runs a loop that checks for USB devices using the check_usb
        method and sleeps for a specified interval.
        The loop exits when the self.EXIT event is set.

        """
        # internal interfaces
        log("connecting internal interfaces", "info")
        int_interface_task = asyncio.create_task(self.create_internal_interfaces())

        # external interfaces
        log("scanning for devices", "info")
        while not self.EXIT.is_set():
            result = await asyncio.gather(
                self.check_usb(), asyncio.sleep(self.SCAN_DT), return_exceptions=True
            )

            # check exceptions
            tasks = [int_interface_task] + [
                t for t in self.connected_usb_devices.values() if isinstance(t, asyncio.Task)
            ]

            for t in tasks:
                if (exception := t.exception()) is not None:
                    log(
                        f"{t.get_coro()} Exception: "
                        f"{''.join(extract_tb(exception))}",
                        "critical",
                    )

        # stop:
        int_interface_task.cancel()
        [t.cancel() for t in self.connected_usb_devices.values() if isinstance(t, asyncio.Task)]
        self.exit()

    async def check_usb(self) -> None:
        """
        Check for USB devices and update the connected devices.

        This function gets the current USB ports and compares them with the
        connected usb devices dictionary. It removes the disconnected devices using
        the remove_usb_interface method and creates new devices using the
        create_serial_interface method.
        """
        usb_ports = set(p.device for p in list_ports.comports())
        new_devices = usb_ports.difference(self.connected_usb_devices)
        disconnected_devices = set(self.connected_usb_devices).difference(usb_ports)

        if not new_devices and not disconnected_devices:
            return

        # remove old devices
        [self.remove_usb_interface(d) for d in disconnected_devices]

        for d in new_devices:
            self.connected_usb_devices[d] = asyncio.create_task(
                self.create_serial_interface(d)
            )

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
            SerialController,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
            device=port,
            other_names=self.interfaces,
        )
        await interface.async_start()
        self.connected_usb_devices[port] = interface  # add port to interface
        await interface.async_run()

    def remove_usb_interface(
        self,
        port: str,
    ):
        """
        Remove a USB interface from the connected devices.

        This function checks if the specified device is an asyncio task
        or an Interface instance and performs the appropriate cancellation
        or exit operation before removing it from the connected devices dictionary.

        Parameters:
        - port (str): The port used to reference the connected device.

        """
        print(f"remove {port}")

        if isinstance(self.connected_usb_devices[port], asyncio.Task):
            self.connected_usb_devices[port].cancel()

        if isinstance(self.connected_usb_devices[port], Interface):
            self.connected_usb_devices[port].exit()

        del self.connected_usb_devices[port]

    async def create_internal_interfaces(self) -> None:
        """
        Connect all permanently connected / internal interfaces such as i2c bus,
        camera, network etc.

        This function creates an Interface object for each internal interface and
        initializes it. The interfaces are stored in the self.connected_internal_devices dictionary.
        """
        interfaces = []

        async def init_interface(interface):
            await interface.async_start()
            self.connected_internal_devices[interface.device] = interface

        interfaces.append(
            Interface(
                InternalController,
                on_connect=self.on_connect,
                on_disconnect=self.on_disconnect,
                device="internalbus",
            )
        )

        # broadcast receiver
        interfaces.append(
            Interface(
                BroadCastController,
                on_connect=self.on_connect,
                on_disconnect=self.on_disconnect,
                device="broadcast",
            )
        )


        await asyncio.gather(
            *[init_interface(interface) for interface in interfaces],
            return_exceptions=True,
        )

    def on_connect(self, interface):
        """
        Handle a connection event.

        This function calls the external_on_connect callback with the given interface.

        Args:
            interface: The interface that has been connected.
        """
        self.external_on_connect(interface)

    def on_disconnect(self, interface):
        """
        Handle a disconnection event.

        This function calls the external_on_disconnect callback with the given interface.

        Args:
            interface: The interface that has been disconnected.
        """
        self.external_on_disconnect(interface)

    def exit(self):
        """
        Exit the interface. This function is a placeholder for an exit routine.
        """
        pass
