"""
Template for Controller 
"""

import asyncio
from subs.log import create_logger


logger = create_logger()


class Controller:
    recv_buffer = []  # TODO: use queue?
    write_buffer = []  # TODO: use queue?

    connected = True
    disconnected = False

    device = None # placeholder for the device or bus driver
    name = ""  # name of device

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
        self._setup()

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def write(self, data) -> None:
        pass

    def read(self) -> None:
        pass

    def do(self, *args, **kwargs) -> None:
        """
        placeholder for function called with new data
        TODO: run async?
        """
        pass

    def on_connect(self, *args, **kwargs) -> None:
        """
        called when connected
        """
        print("connected")

    def on_disconnect(self, *args, **kwargs) -> None:
        """
        called when disconnected
        """
        print("disconnected")

    def _setup(self, *args, **kwargs) -> None:
        """
        overwrite to setup device etc
        """
        pass

    def _log(self, message, level="info"):
        getattr(logger, level)(f"CTRL:{self.name}: {message}")
    

    def exit(self, *args, **kwargs):
        pass
