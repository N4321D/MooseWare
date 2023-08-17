"""
Template file for dummy sensor drivers.

Use this as super class for the specific sensor and override the
methods to customize it.

sensor.status indicates state of the sensor:
0: N.C. / Error, sensor lost connection/ os error / ...
1: Sensor connected, standby
2: Sensor Recording / active
3 - x: Extra sensor specific states (stimulating etc)
"""
DUMMY_LOGO = ""  # added to sensor name if dummy is loaded
# create logger
try:
    from subs.log import create_logger
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None: 
                f = lambda *x: print("SENSOR DRIVER: ", *x)  # change messenger in whatever script you are importing
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()

def log(message, level="info"):
    getattr(logger, level)("SENSOR TEMPLATE: {}".format(message))  # change RECORDER SAVER IN CLASS NAME

# imports
from math import sin, tan
import time
import json

try:
    from subs.driver.sensor_files.dummy_gpio import bus, GPIO   # do not remove, used by other scripts
except:
    from dummy_gpio import bus, GPIO                            # do not remove, used by other scripts


class Sensor():
    '''
    default sensor class
    '''
    # variables
    address = None                                          # address of sensor
    disconnected = True                                  # disconnected or not
    whoisreg = 0x0F                            # register with whois identifier
    name = ''                                             # full name of sensor
    short_name = ''                                 # name used after importing
    record = True                         # set to false to not use this sensor
    reset_command = {'reg': None,
                     'byte': None}                    # Reg and value for reset
    trigger_required = False          # True if sensor needs trigger to measure
    errorout = float('NaN')                       # output if no data recorded:
    #                                (if set to None, last value will be saved)
    defaults = {'maxrate': None,}                 # Max samplerate in Hz of this sensor
    out_vars = {}
    datatype = {}
         
    shv = {'status': -1,  # interger which can be used to describe status of the chip
                                           # e.g 0: standby, 1: recording, 2: stimulating

           'reset_count': 0,
           't_last_reset': 0.0,
           }                    # dict with shared values name (key) and defaults (value) will be replaced with shared table on init
    
    def __init__(self, shared_vars):
        '''
        dict with output vars and function to read
        if it contains commands it should be
        {'Var Name' {'cmd' read_method,
                       'sel' 'selection criteria' or False (if no sel crit)}}
        if False the var name will be deleted (can be used as placeholder
        for future functions)
        '''
        self.defaults = self.defaults.copy()           # copy to prevent unintended shareing between sensors

        self.settings = self.defaults.copy()           # copy default settings

        # link to shared table
        self.shv = shared_vars


        # specifiy data types to save data in per parameter,
        # default is float64
        self.datatype = {}

        # delete unused output vars:
        self.defaults['out_vars'] = self.out_vars.copy()
        self.out_vars = {key: self.out_vars[key]
                         for key in self.out_vars
                         if self.out_vars[key]}

    @property
    def out_vars(self):
        return self._out_vars

    @out_vars.setter
    def out_vars(self, x):
        self._out_vars = {(f"{k}{DUMMY_LOGO}" if not k.endswith(DUMMY_LOGO)
                           else k): v 
                           for k, v in x.items()}

    def whois(self):
        # function to test connection, returns unique identifier
        self.rw_byte(mode="read", reg=0)

    def init(self):
        # contains the commands to setup the sensor with right pars
        return

    def start(self):
        # placeholder for trigger function
        return

    def readself(self):
        """
        placeholder for read protocol of sensor this is called from
        recoder
        needs to return {'name of par': value}
        returns float('NaN') as value if disconnected
        """
        self.status = 0 
        output = {}
        for key in self.out_vars:
            run = self.out_vars[key]
            if run['sel']:
                output[key] = self.conversion(run['cmd'](run['sel']), 
                                              run['sel'])
            else:
                output[key] = self.conversion(run['cmd']())
        return output

    def rw_byte(self, reg=None, byte=None, mode='read'):
        # write custom byte to address set mode to read or write
        # for reading use byte to indicate the number of bytes
        out = None
        if mode == 'write':
            pass

        else:
            _out = int((0.2 + (sin(time.time()) * tan(0.1 * time.time()) / 13)) 
                        * 0xff)
            if _out < 0:
                _out = 0
            if _out > 0xFF:
                _out = 0xFF
            # READ
            if byte:
                # write list
                out = [_out
                       for i in range(byte)]
            else:
                # read one byte
                out = _out

            
            if out is None:
                # error
                self.status = -1
                self.disconnected = True
                if mode == 'read':
                    out = [self.errorout] * byte if byte else self.errorout
                return self.errorout

            # indicate succesful read/write command if failed earlier
            if self.disconnected:
                self.disconnected = False
                self.shv.set(0, 'status', 0)
        
        return out

    def conversion(self, data_in, var=None, **kwargs):
        # this function converts the data from bits to chosen units
        # var can be used to specify output e.g. temp and humidity
        return data_in

    def byte2int(self, input_bytes, order="big", signed=False):
        """
        converts list or tuple of bytes to int
        input bytes can be bytestring too.
        order:
            - big: MSB -> LSB
            - little: LSB -> MSB
        signed:
            - False: returns bytes from 0 - max
            - True: 2s complement (-0.5 max to + 0.5max)
        """
        if (not hasattr(input_bytes, "__iter__") 
            or any([(i != i) or isinstance(i, float) for i in input_bytes])
            ):
            return self.errorout

        else:
            return int.from_bytes(input_bytes, byteorder=order, signed=signed)

    def reset(self):
        if self.reset_command["reg"] is not None:
            self.rw_byte(**self.reset_command, mode='write')
        else:
            self.whois()
        self.init()
        
        self.shv.set(self.shv.get('reset_count', 0) + 1, 'reset_count', 0)
        self.shv.set(time.time(), 't_last_reset', 0)

        # 

    def stop(self):
        """
        stops sensor
        """
        self._stop()
        self.shv.set(0, 'status', 0)
        self.shv.set(0, 'reset_count', 0)
        self.shv.set(0.0, 't_last_reset', 0)


    def _stop(self):
        """
        placeholder for stop commands
        """
        pass

    def json_panel(self):
        """
        return json panel with properties for kivy intrenface 
        to change in settings panel
        """
        return [{"title": "Record",
                "type": "bool",
                "desc": "Record data from this chip",
                "section": self.name,
                "key": "recording",
            }]
    
    def return_default_options(self):
        """
        returns dict with default options for kivy settings panel
        """

        return {"record": self.record}
    

    def do_config(self, par, value):
        """
        changes config based on input
        from settings panel
        """
        pass

    def get_idle_status(self):
        """
        Return idle stats in the same format as the microcontroller chip drivers
        """
        return {self.short_name: {
            "name": self.name,
            "#ST": -4 if (self.whois() or self.disconnected) else 0,
            "record": self.record,
            "par_names": self.out_vars.keys(),
            "par_short_names": self.out_vars.keys(),
            "control_str": json.dumps(self.json_panel()),
            }
        }