try:
    try:
        from sensor_template import Sensor, logger

    except:
        from subs.driver.sensor_files.sensor_template import Sensor, logger
    
    DUMMY = False
except:
    # import dummy sensor
    try:
        from dummy_sensor_template import Sensor, logger

    except:
        from subs.driver.sensor_files.dummy_sensor_template import Sensor, logger
    DUMMY = True

def log(message, level="info"):
    cls_name = "RECORDER"
    try:
        getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here
    except AttributeError:
        print(f"{cls_name} - {level}: {message}")

if DUMMY:
    log("Humidity Sensor not found, dummy driver loaded", "warning")
del DUMMY

import time

class HumidityTemperature(Sensor):
    '''
     SHT85 (sensirion) humidity and temperature sensor

    Sensor sends or receives in 1 or more blocks of 3 bytes: MSB, LSB and CRC

    Calc crc with crc8 function and send it after MSB and LSB
    crc is calculated from MSB and LSB
    if you dont send CRC sensor will not respond!!

    Sensor needs time (at least 1 ms plus sample time)
    between sending single measurement and reading output
    otherwise it will produce an error (see specsheet)
    This is measured by checking time.time vs last_command_time and saving
    time.perf_counter as last last_command_time.

    max sample rate depends on the reproducability setting:
     _______________________________________________________________________
    |                                                                       |
    |reproducability:        min:        typical:       LSB read_command:   |
    |-----------------------------------------------------------------------|
    |low                     222 Hz.     400 Hz.        0x16                |
    |med:                    153 Hz.     222 Hz.        0x0B                |
    |high:                   64 Hz.      80 Hz.         0x00                |
    |_______________________________________________________________________|

    '''

    # vars
    address = 0x44
    last_command_time = 0                        # time of last issued command (see notes)
    name = 'Humidity Temperature'
    short_name = 'H/T'                           # name used after importing
    trigger_required = True                      # True if sensor needs trigger to measure
    reset_command = {'reg': 0x30, 'byte': 0xA2}
    sample = False                               # indicates if last value was rec
    unit = {'C': 'c', 
            'F': 'f', 
            'K': 'k'}
    
    current_unit = u'\N{DEGREE SIGN} C'


    # dict with shared values name (key) and defaults (value) will be replaced with shared table on init:
    shv = {'status': 0,
           'reset_count': 0,
           't_last_reset': 0.0,
           }        

    def __init__(self, shared_vars):
        # the sensor return humidity and temp together this list saves both
        # so the other can be extracted if one par is read already
        self.defaults = self.defaults.copy()
        self.defaults.update({'maxrate': 10,                     # Max samplerate in Hz of this sensor
                              'read_command': (0x24, 0x00),      # command for 1 shot reading
                                  })                             # copy to prevent unintended shareing between sensors

        self.data = [None, None]    # hum, temp
        self.out_vars = {'Humidity': {'cmd': self.readvars,
                                      'sel': 'hum'},
                         'Temperature External': {'cmd': self.readvars,
                                         'sel': 'tmp'}, }

        # link to shared table
        self.shv = shared_vars
        
        # delete unused output vars:
        self.defaults['out_vars'] = self.out_vars.copy()
        self.settings = self.defaults.copy()            # copy default settings
        self.out_vars = {key: self.out_vars[key] for key in
                         self.out_vars if self.out_vars[key]}

    def whois(self):
        # function to test connection, returns unique serial no
        self.rw_byte(mode='write', reg=0x36, byte=0x82)
        return self.byte2int(self.rw_byte(mode='read', reg=0, byte=6))

    def start(self):
        self.data = [None, None]        # reset self.data
        # placeholder for trigger function
        msb = self.settings['read_command'][0]
        lsb = self.settings['read_command'][1]
        crc = self.crc8(self.settings['read_command'])
        self.sample = True
        return self.rw_byte(mode='write', reg=msb, byte=[lsb, crc])

    def readvars(self, par):
        if self.data == [None, None]:
            # read data:
            # chip returns:
            # [temp MSB, temp LSB, crc, humidity MSB, humidity LSB, crc]
            out = self.rw_byte(mode='read', reg=0, byte=6)

            if isinstance(out, (list, tuple)):
                self.data = [self.byte2int((out[0], out[1])),
                             self.byte2int((out[3], out[4]))]

        if par == 'tmp':
            return self.data[0]
        elif par == 'hum':
            return self.data[1]

    def heat(self, on=False):
        # turns internal heater on or off (for testing)
        self.rw_byte(mode='write', reg=0x30, byte=(0x6D if on else 0x66))

    def status_from_chip(self, clear=False):
        # checks or clears status from chip
        if not clear:
            # read status register see spec sheet for details
            self.rw_byte(mode='write', reg=0xf3, byte=0x2d)
            return self.byte2int(self.rw_byte(mode='read', reg=0, byte=3))
        else:
            # clear status
            self.rw_byte(mode='write', reg=0x30, byte=0x41)

    def waitforlast(self, sample=False):
        # this function waits the minimum time between commands
        if sample:
            # wait for sensor to finish sampeling
            t = time.time() - self.last_command_time

            target_time = 1 / self.settings['maxrate']
            if t < target_time:
                # wait for sensor to finish measurement
                time.sleep(target_time - t)
        else:
            # wait 20 ms between commands
            time.sleep(0.1)

    def rw_byte(self, reg=None, byte=None, mode='read', sample=None):
        # write custom byte to address set mode to read or write
        self.waitforlast(sample=self.sample)   # wait for sensor to be ready
        self.sample = False               # reset sample indicator
        out = super().rw_byte(mode=mode, reg=reg, byte=byte)  # get data
        self.last_command_time = time.time()        # set last interaction time
        return out

    def conversion(self, value, var=None, unit=None, **kwargs):
        unit = unit or self.unit.get(self.current_unit, "c")
        value = value / 0xFFFF
        if var == 'tmp':
            if unit == 'c':
                # return Celsius
                value = -45 + 175 * value

            elif unit == "f":
                # return Fahrenheit
                value = -49 + 315 * value

            elif unit == "k":
                # return Kelvin
                value = (-45 + 175 * value) + 273.15
        else:
            # return humidity
            value *= 100

        return value

    @staticmethod
    def crc8(bytes_data):
        # CRC_POLYNOMIAL = 0x131 --> P(x) = x^8 + x^5 + x^4 + 1 = 100110001
        # calculates CRC for list bytes_data [MSB, LSB]
        crc = 0xFF
        for bt in bytes_data:
            crc ^= bt
            for bit in range(8, 0, -1):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x131
                else:
                    crc = (crc << 1)
        return crc
    
    def json_panel(self):
        """
        return json panel with properties for kivy intrenface 
        to change in settings panel
        """

        panel = [{"title": "Record",
                "type": "bool",
                "desc": "Record data from this chip",
                "section": self.name,
                "key": "record",
                },
                {"title": "Unit",
                "type": "options",
                "desc": "Unit to record temperature in",
                "section": self.name,
                "key": "temp_unit",
                "options": list(self.unit),
                },
        ]
        return panel

    def return_default_options(self):
        """
        returns dict with default options for kivy settings panel
        """

        return {"recording": self.record,
                "temp_unit": self.current_unit,
                }

    def do_config(self, par, value):
        if par == 'temp_unit':
            self.current_unit = value


if __name__ == "__main__":
    s = HumidityTemperature()
    s.init()
    import time
    while True:      
        s.start()
        time.sleep(0.5)
        print(s.readself())

# TODO: handle slower sample speed