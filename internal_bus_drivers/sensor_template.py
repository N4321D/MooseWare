"""
Template for sensor drivers
"""
import time
from typing import final

try:
    import smbus

    bus = smbus.SMBus(1)  # i2c bus


except:
    from random import randint
    from math import sin, tan

    class DummyBus:
        DUMMY_BUS = True
        def SMBus(self, *args):
            return self

        def read_byte(self, *args):
            return 0xFF
        
        def read_byte_data(self, *args):
            return 0xFF

        def read_i2c_block_data(self, address, reg, numbytes):
            return [self._generate_value() for i in range(numbytes)]

        def write_i2c_block_data(self, *args):
            pass

        def write_byte_data(self, *args):
            pass

        def _generate_value(
            self,
        ):
            return int((0.2 + (sin(time.time()) * tan(0.1 * time.time()) / 13)) * 0xFF)

    bus = DummyBus().SMBus(1)  # dummy bus


class Sensor():
    NAME = "NAME"  # Full name of the sensor
    SHORT_NAME = "SHORT_NAME"  # Short name of the sensor
    PARAMETER_NAMES = []  # name of the recorded parameter
    PARAMETER_SHORT_NAMES = []  # short name of the recorded parameter
    
    error_count = 0  # number of read / write errors
    STATUS = 0  # current status
    SENT_STATUS = 0  # status that was last reported
    connected = True  # indicate if sensor is disconnected or not
    record = True  # indicate if sensor needs to be recorded or not
    control_str = []  # list with dictionaries with gui objects for sensor

    dict_out = {}  # dictionary with parameter shortname as key and data as value'
    _TESTING = False  # indicates that dummy bus is loaded for testing

    def __init__(self) -> None:
        """
        Python Init, specific for python drivers
        """
        pass

    def init(self) -> None:
        """
        called on first connection to sensor from controller class
        """
        pass

    def check_and_trigger(self):
        """
        checks if sensor needs to be resetted and triggers sensor
        """
        pass

    def dataToJSON(self) -> None:
        """
        put sampled data in self.dict_out here
        """
        pass

    def procCmd(self, key, value):
        """
        Custom incoming commands, overwrite in subclass
        """
        pass

    def reset_procedure(self):
        """
        define reset procudure here if sensor needs it
        """
        pass

    def sample(self) -> None:
        """
        sample sensor here. Does not return data
        """
        pass

    def stop(self):
        """
        define stop here if needed

        Returns:
            _type_: _description_
        """    
        pass

    def test_connection(self):
        """
        Test connection for specific sensor and bus
        """
        self.STATUS = 0
        self.connected = True

    def trigger(self):
        """
        called at the start of each recording loop, can be used to trigger 
        sample point in sensor
        """
        pass

    # final methods:
    @final
    def getSampledData(self) -> dict:
        """
        called to return sampled data in dictionary
        also checks for any status changes and returns them if any were found

        Returns:
            dict: sampled data with parameters as key and data as value
        """
        # called from recorder to get data
        self.dict_out = {}
        if (self.STATUS != self.SENT_STATUS) or (self.STATUS < 0):
            self.dict_out["#ST"] = self.STATUS
            self.SENT_STATUS = self.STATUS
        self.dataToJSON()
        return self.dict_out
    
    @final
    def getInfo(self) -> dict:
        """
        return sensor information in idle loop

        Returns:
            dict: sensor information
        """
        self.SENT_STATUS = self.STATUS

        return {
            "name": self.NAME,
            "control_str": self.control_str,
            "#ST": self.STATUS,
            "record": self.record,
            "parameter_names": self.PARAMETER_NAMES,
            "parameter_short_names": self.PARAMETER_SHORT_NAMES,
        }

    @final
    def doCmd(self, key, value):
        # called to process incoming commands
        if key == "record":
            self.record = value

        else:
            self.procCmd(key, value)
    
    @final
    def reset(self):
        """
        Called to reset sensor when needed
        """
        self.STATUS = 0
        self.zero_count = 0
        self.error_count = 0
        self.reset_procedure()
        self.init()



class I2CSensor(Sensor):
    ADDRESS = 0x00  # i2c address
    
    zero_count = 0  # count zeros -> if multiple zeroes in a row, reset
    zeros_threshold = 0xFD  # set to 0 to not reset, else sensor is resetted if zero_count > zeros_theshold

    sampled_data = []  # array with sampled data
    
    bus = bus

    def __init__(self) -> None:
        if hasattr(self.bus, "DUMMY_BUS"):
            self._TESTING = True

    def init(self):
        # init of sensor, overwrite in subclass
        pass

    @final
    def check_and_trigger(self):
        """
        checks if sensor needs to be resetted and triggers sensor
        """
        if self.error_count or (
            self.zeros_threshold and (self.zero_count > self.zeros_threshold)
        ):
            self.reset()
        self.trigger()

    def sample(self):
        # overwrite in subclass, make sure it adds to errorcount with unsuccesful reads
        if self.readI2C(self.ADDRESS, 0x00, 0x00):
            self.error_count = 0
        else:
            self.error_count += 1

    def dataToJSON(self):
        # add sampled data to dict out, overwrite in subclass to compose sampled data
        self.dict_out.update(
            {k: v for k, v in zip(self.PARAMETER_SHORT_NAMES, self.sampled_data)}
        )
        return self.dict_out

    @final
    def test_connection(self):
        try:
            self.bus.read_byte(self.ADDRESS)
            self.STATUS = 0
            self.connected = True
            
        except OSError:
            self.STATUS = -5
            self.connected = False

    @final
    def readI2C(self, address, reg, numBytes, reverse=False):
        """
        Read bytes from an I2C sensor

        Args:
            address (int): address of the chip
            reg (int): register of the chip
            numBytes (int): number of sequential bytes to read
            data (dict): data block to store the bytes in
            reverse (bool, optional): read bytes in reverse order. Defaults to False.
        """
        try:
            if not reverse:
                self.sampled_data = self.bus.read_i2c_block_data(address, reg, numBytes)
            else:
                self.sampled_data = self.bus.read_i2c_block_data(address, reg, numBytes)[::-1]

            if not any(self.sampled_data):
                self.zero_count += 1

            if self.STATUS < 0:
                self.STATUS = 0  # reset status on succesful read

            return True

        except OSError:
            # Read error
            self.STATUS = -5
            return False

    @final
    def writeI2C(self, 
                 address: int, 
                 reg: int, 
                 data: (list, int)):
        """
        write an array of data to a register of the i2c sensor

        Args:
            address (int): address to write to
            reg (int): register to write to
            data (list, int): data to write, can be list for multiple bytes
        """
        try:
            if isinstance(data, list):
                # write list
                self.bus.write_i2c_block_data(address, reg, data)
            else:
                # write one byte
                self.bus.write_byte_data(address, reg, data)

            if self.STATUS < 0:
                self.STATUS = 0  # reset status on succesful read
            return True

        except OSError:
            self.STATUS = -5

