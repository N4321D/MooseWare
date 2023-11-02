"""
scanner that scans if interfaces are connected
and integrates them into IO
"""


from serial import list_ports

from subs.driver.interfaces import Interface
from subs.driver.interface_drivers.internal import InternalController

import asyncio


class InterfaceFactory():
    def __init__(self) -> None:
        pass