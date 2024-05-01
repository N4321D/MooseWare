"""
Template for Controller 
"""

import asyncio
from subs.log import create_logger
from typing import final


logger = create_logger()


class Controller:
    connected = asyncio.Event()
    disconnected = asyncio.Event()

    device = None # placeholder for the device or bus driver

    @final
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
        self._setup()

    @final
    def _log(self, message, level="info"):
        getattr(logger, level)(f"CTRL:{self.name}: {message}")

    async def start(self) -> None:
        pass

    async def run(self) -> None:
        """
        loop or event that has to be awaited or run to record
        called from app.IO interface factory
        """
        await self.disconnected.wait()

    def stop(self) -> None:
        pass

    def write(self, data) -> None:
        pass

    def do(self, *args, **kwargs) -> None:
        """
        placeholder for function called with new data
        TODO: run async?
        """
        pass

    async def on_connect_default(self, *args, **kwargs) -> None:
        """
        called when connected
        """
        self.connected.set()
        self.disconnected.clear()
        return await self.on_connect(*args, **kwargs)

    def on_disconnect_default(self, *args, **kwargs) -> None:
        """
        called when disconnected
        """
        self.connected.clear()
        self.disconnected.set()
        return self.on_disconnect(*args, **kwargs)

    async def on_connect(self, *args, **kwargs) -> None:
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
        Overwrite to setup device etc.
        Dont forget to connect the protocol or devices method that is called on new
        data here to self._preprocess_data
        """
        pass

    def _preprocess_data(self, data):
        """
        overwrite this method to preprocess or unpack data,
        make sure that it calls self.do with data at the end
        Args:
            data (_type_): _description_
        """
        self.do(data)
  
    def exit(self, *args, **kwargs):
        pass
