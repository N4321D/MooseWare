import json
from subs.gui.misc.Stimulation import StimController

class Chip():
    """
    A class representing a chip device on an interface

    Attributes:
        interface (Controller): The interface object to which the chip is connected.
        parent_name (str): The name of the parent device or interface.
        connected (bool): Indicates if the chip is currently connected.
        status (int): Indicates the current status of the chip (see vars.py for all status options)
        name (str): The full name of the chip.
        short_name (str): A short name or identifier for the chip.
        record (bool): Indicates whether data from this chip should be recorded.
        control_panel (list): A list of control panel settings for the chip.
        
    Methods:
        return_default_options(): Returns the default options for the chip.
        __setattr__(name: str, value): Overrides the default setattr behavior to handle attribute changes.
        send_cmd(val): Sends a command to the chip.
        update(chip_dict): Updates the chip attributes using a dictionary.
        json_panel() -> list: Returns the control panel settings in JSON format.
        do_config(par, value): Performs configuration for the chip.

    """
    def __init__(self, short_name, chip_dict, interface, **kwargs) -> None:
        self.interface = interface
        self.stim_control = {}
        self.parent_name = interface.name if interface is not None else ""      
        self.connected = True
        self.status = 0                  # indicates what chip is doing (see vars.py sensor status) negative values are errors
        self.resets = 0                  # counts number of resets #TODO: implement
        self.name = short_name
        self.short_name = short_name
        self.record = True
        self.__dict__.update(kwargs)        
        self.update(chip_dict)

        _buttons = chip_dict.get("control_str", [])
        if isinstance(_buttons, (str, bytes, bytearray)):
            _buttons = json.loads(_buttons or "[]")

        self.control_panel = [{"title": "Record",
                     "type": "bool",
                     "desc": "Record data from this device",
                     "key": "record",
                     "default_value": True,
                  }] + _buttons
        
        # add section for saving settings
        for i in self.control_panel:
            i["section"] = f"{self.parent_name}: {self.name}"
            if i['type'] == "stim":
                par = i['key']   # do not remove otherwise will use the wrong item from dict
                if par not in self.stim_control:
                    self.stim_control[par] = StimController()
                    self.stim_control[par].do_stim = lambda dur, amp: self.do_stim(par, dur, amp)
        
        self.__setattr__ = self.setattr

    def setattr(self, name: str, value) -> None:
        if hasattr(self, name) and getattr(self, name) != value:
            if name == 'status':
                self.connected = (value >= 0)
            else:
                self.send_cmd({self.short_name: {name: value}})

        super().__setattr__(name, value)

    def send_cmd(self, val):
        """
        Place Holder for send cmd from interface

        Args:
            val (dict): command to send to chip or interface
        """
        
    def update(self, chip_dict):
        self.__dict__.update(chip_dict)
    
    def json_panel(self) -> list:
        return self.control_panel
    
    def do_config(self, par, value):
        if (par == "stim"):
            try:
                value["stim_Strt_T"]
                return
            except:
                pass
            
        self.send_cmd({self.short_name: {par: value}})
    
    def do_stim(self, par, dur, amp):
        self.send_cmd({self.short_name: {par: [dur, amp]}})
