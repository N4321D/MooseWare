import json
from subs.gui.misc.Stimulation import StimController

class Chip():
    """
    A class representing a chip device on microcontrollers

    Attributes:
        controller (Controller): The controller object to which the chip is connected.
        parent_name (str): The name of the parent device or controller.
        connected (bool): Indicates if the chip is currently connected.
        status (int): Indicates the current status of the chip (see vars.py for all status options)
        name (str): The full name of the chip.
        short_name (str): A short name or identifier for the chip.
        i2c_status (int): The status of the I2C connection.
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
    def __init__(self, short_name, chip_dict, controller, **kwargs) -> None:
        self.controller = controller
        self.stim_controls = None
        self.parent_name = controller.name if controller is not None else ""      
        self.connected = True
        self.status = 1                  # indicates what chip is doing (see vars.py sensor status)
        self.name = short_name
        self.short_name = short_name
        self.i2c_status = 0
        self.record = True
        self.__dict__.update(kwargs)
        
        self.update(chip_dict)
        self.control_panel = [{"title": "Record",
                     "type": "bool",
                     "desc": "Record data from this device",
                     "key": "record",
                     "default_value": True,
                  }] + (json.loads(chip_dict.get("control_str") or "[]")
                 )
        
        # add section for saving settings
        for i in self.control_panel:
            i["section"] = f"{self.parent_name}: {self.name}"
            if i['type'] == "stim":
                self.stim_control = StimController()
                self.stim_control.do_stim = self.do_stim
        
        
    
    def return_default_options(self):
        return {"record": self.record}

    def __setattr__(self, name: str, value) -> None:
        if hasattr(self, name) and getattr(self, name) != value:
            if name == 'i2c_status':
                self.connected = (value == 0)
                self.status = 1 if self.connected else 0
            else:
                self.send_cmd({name: value})
        super().__setattr__(name, value)

    def send_cmd(self, val):
        val = json.dumps({self.short_name: val})
        print(f"Sending {val}")
        self.controller.micro.write(val)
        
    def update(self, chip_dict):
        self.__dict__.update(chip_dict)
    
    def json_panel(self) -> list:
        return self.control_panel
    
    def do_config(self, par, value):
        self.send_cmd({par: value})
    
    def do_stim(self, dur, amp):
        self.send_cmd({'stim': [dur, amp]})

