"""
Template file for sensor drivers.

Use this as super class for the specific sensor and override the
methods to customize it.


NOTES:
on RPI: Find address of chips with "i2cdetect -y 1" in terminal


sensor.status indicates state of the sensor:
0: N.C. / Error, sensor lost connection/ os error / ...
1: Sensor connected, standby
2: Sensor Recording / active
3 - x: Extra sensor specific states (stimulating etc)
"""

# create logger
try:
    from subs.log import create_logger
    logger = create_logger()

except:
    logger = None

def log(message, level="info"):
    cls_name = "SENSOR"    # change CLASSNAME here
    try:
        getattr(logger, level)(f"{cls_name}: {message}")  
        
    except AttributeError:
        print(f"{cls_name} - {level}: {message}")

# imports
try:
    import smbus   # DO NOT USE SMBUS2
except ModuleNotFoundError:
    raise ImportError("\n SMBus not found")

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    ImportError("RPi.GPIO not found")

import time

# set GPIO mode
GPIO.setmode(GPIO.BCM)
# disable port in use warning
GPIO.setwarnings(False)

# I2C channel 1 is connected to the GPIO pins
channel = 1

# Initialize I2C (SMBus)
bus = smbus.SMBus(channel)


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
    defaults = {'maxrate': None, }        # Max samplerate in Hz of this sensor
    out_vars = {}
    datatype = {}
    
    shv = {                                  # shared values 
           'status': 0,                     # interger which can be used to describe status of the chip e.g 0: standby, 1: recording, 2: stimulating
           'reset_count': 0,
           't_last_reset': 0.0,
           }                                # dict with shared values name (key) and defaults (value) will be replaced with shared table on init
    


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

    def whois(self):
        # function to test connection, returns unique identifier
        return self.rw_byte(reg=self.whoisreg, mode='read')

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
        self.shv.set(2, 'status', 0)
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
        """
        read or write bytes from/to i2c bus
        - reg: register to read or write from
        - byte: when mode is write: byte(s) to write (use list to write multiple)
                when mode is read: number of bytes to read from starting address (reg)
                    WARNING: this does not always work, for some sensors the sequential
                    addresses have to requested individually
        - mode: "read" to read "write" to write
        """
        out = None
        try:
            if mode == 'write':
                # WRITE
                if isinstance(byte, (list, tuple)):
                    # write list
                    bus.write_i2c_block_data(self.address, reg, byte)
                else:
                    # write one byte
                    bus.write_byte_data(self.address, reg, byte)

            else:
                # READ
                if byte:
                    # read list
                    out = bus.read_i2c_block_data(self.address, reg, byte)
                else:
                    # read one byte
                    out = bus.read_byte_data(self.address, reg)
                    
            # indicate succesful read/write command if failed before
            if self.disconnected:
                self.shv.set(1, 'status', 0)
                self.disconnected = False

        except OSError as e:
            # indicate unsuccessful read/write command
            self.shv.set(0, 'status', 0)
            self.disconnected = True
            if mode == 'read':
                out = [self.errorout] * byte if byte else self.errorout

        return out

    def conversion(self, data_in, var=None, **kwargs):
        """
        this function converts the data from bits to chosen units
        but is overwritten for specific sensors with the conversion method
        - data_in: data to convert
        - var: be used to specify output e.g. temp and humidity
        """
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
        # self.shv.set(0, 'status', 0)
        if self.reset_command["reg"] is not None:
            self.rw_byte(**self.reset_command, mode='write')
        else:
            self.whois()
        self.init()
        
        self.shv.set(self.shv.get('reset_count', 0) + 1, 'reset_count', 0)
        self.shv.set(time.time(), 't_last_reset', 0)

    def stop(self):
        """
        stops sensor
        """
        self._stop()
        self.shv.set(1, 'status', 0)
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
        return [{
            # on off button
            "title": "Record",
                "type": "bool",
                "desc": "Record data from this chip",
                "section": self.name,
                "key": "record",
            }
            ]
    
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