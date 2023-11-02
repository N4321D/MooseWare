"""
scanner that scans if interfaces are connected
and integrates them into IO
"""


from serial import list_ports
from subs.driver.interfaces import Interface



class InterfaceFactory():
    def __init__(self) -> None:
        pass