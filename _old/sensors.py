"""
Created on Fri Jan 11 11:04:21 2019
@author: Dmitri Yousef Yengej

Setup File for sensors

Gathers all available sensors and adds them to
chip_d dictionary
"""
# create logger
try:
    from subs.log import create_logger
    logger = create_logger()

except:
    logger = None

def log(message, level="info"):
    cls_name = "SENSOR DRIVER"
    try:
        getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here
    except AttributeError:
        print(f"{cls_name} - {level}: {message}")

# import sensors
try:
    from subs.driver.sensor_files.sensor_template import bus, GPIO
    TESTING = False
    log("Drivers Loaded", "info")
except Exception as e:
    from subs.driver.sensor_files.dummy_sensor_template import bus, GPIO
    TESTING = True
    log(f"Drivers not found, dummy driver loaded: {e}", "info")


from subs.misc.shared_mem_np_dict import SharedTable

# from subs.driver.sensor_files.temperature import TempSens
from subs.driver.sensor_files.ois import LightSens
from subs.driver.sensor_files.motion import MoSens
from subs.driver.sensor_files.pressure import PressSens, PressExt
from subs.driver.sensor_files.humidity import HumidityTemperature
from subs.driver.sensor_files.lightstrip import LightStrip
from subs.driver.sensor_files.readgpio import ReadGpio

chip_d = {}     # dictionary that includes all chips

def sensTest(verbose=True):
    result = {}
    if verbose:
        print('{0: <25}'.format('Sensor Test' + ': '),
              '{0: <10}'.format('Status'), 'I.D.\n')
    for chip in chip_d.values():
        whois = chip.whois()
        if whois == whois:                                        # remove nans
            whois = bin(whois) if whois is not None else ''
        result[chip.name] = False if chip.disconnected else True
        if verbose:
            print('{0: <25}'.format(chip.name + ': '),
                  '{0: <10}'.format('%s' % ('OK' if result[chip.name]
                                            else 'N.C.')), whois)
    return result

def get_pars():
    """
    gathers all recordable parameters from all connected sensors
    returns dict with parameter as key and as value: tuple with
    (true/ false if connected, name of chip)
    """
    result = {}
    for chip in chip_d.values():
        whois = chip.whois()
        if whois == whois:
            whois = bin(whois) if whois is not None else ''
        for key in chip.out_vars:
            result[key] = (False if chip.disconnected else True, chip.name)
    return result

def get_connected_chips_and_pars(filter_pars=False):
    """
    returns two dicts, one with the connected chips and a link to the driver
    the second one with par: chipname
    - filter_pars:   set to True to filter pars for only the chips that are selected for recording (if false pars are returned for all selected chips)
    """
    chips, pars = {}, {}
    for chip_name, chip in chip_d.items():
        chip.whois()
        if chip.disconnected is False:
            # NOTE: DO NOT RESET CHIPS HERE!! -> it will add to reset count and mess up the chips functioning
            
            # add chip: chip driver to chips
            chips[chip_name] = chip
            if filter_pars and not chip.record:
                continue
            # add par: chipname to pars
            pars.update({k: chip_name for k in chip.out_vars})

    return chips, pars

def get_connected_chips():
    """
    returns the connected chips and a link to the driver
    """
    return {chip_name: chip for chip_name, chip in chip_d.items() 
            if (chip.whois() or (chip.disconnected is False))}



# ========================
#
#   OTHER
#
# ========================


class ReadWrite():
    """
    used to read and write bytes
    to specific i2c addresses 
    (can be used for testing new sensors etc)
    """
    def __init__(self):
        self.disconnected = False

    def writebyte(self, reg, address, byte):
        # write custom byte to address
        try:
            bus.write_byte_data(address, reg, byte)
        except OSError:
            self.disconnected = True

    def readbyte(self, reg, address):
        # write custom byte to address
        try:
            out = bus.read_byte_data(address, reg)
            return out

        except OSError:
            self.disconnected = True

    def reset(self):
        return


def create_chip_dict(allvars={}):
    '''
    Add all sensors do dictionary with all chips,

    !! only import this dict in other modules

    if initialize is True, the sensor classes are initialized,
    else, the classes are just added to the dictionary
    '''
    chip_d = {}          # dict which contains all available sensors
    shared_vars = {}     # dict sensor name: shared table 
    for key, value in allvars.items():
        if not key.startswith('_'):
            chip = value
            if isinstance(chip, type):
                if hasattr(chip, 'address'):
                    if chip.address is not None:
                        shared_vars[chip.name] = SharedTable()
                        shared_vars[chip.name].from_dict(chip.name, chip.shv)
                        chip_d[chip.name] = chip(shared_vars[chip.name])
    return chip_d, shared_vars


chip_d, shared_vars = create_chip_dict(allvars=vars())
chip_d_short_name = {chip.short_name: chip for chip in chip_d.values()}


# datatypes:
datatypes = {'default': 'f4',
      'time': 'f8'}
[datatypes.update(chip[1].datatype) for chip in chip_d.items()]

