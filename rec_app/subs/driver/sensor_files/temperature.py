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
    log("Temperature Sensor not found, dummy driver loaded", "warning")
del DUMMY

class TempSens(Sensor):
    """
    driver for temperature sensor

    MAX31875
    General Description:
    The MAX31875 is a ±1°C-accurate local temperature
    sensor with I2C/SMBus interface. The combination of tiny
    package and excellent temperature measurement accuracy
    makes this product ideal for a variety of equipment.
    The I2C/SMBus-compatible serial interface accepts standard
    write byte, read byte, send byte, and receive byte commands
    to read the temperature data and configure the behavior
    of the sensor. Bus timeout resets the interface if the clock
    is low for more than 30ms (nominal). PEC helps to avoid
    communication errors when used with a master that supports
    this feature.
    The MAX31875 is available in a 4-bump, wafer-level
    package (WLP) and operates over the -50°C to +150°C
    temperature range.

    ● Tiny, 0.84mm x 0.84mm x 0.35mm WLP
    ● Excellent Temperature Accuracy:
        • ±1.75°C from -40°C to +145°C
        • ±1°C from -0°C to +70°C
    ● <10µA Average Power Supply Current
    ● Selectable Timeout Prevents Bus Lockup
      (Default Enabled)
    ● I2C and SMBus Support
    ● Selectable PEC for Reliable Communications
    ● Up to 1MHz Bus Speed
    ● +1.6V to +3.6V Power Supply Voltage

    """

    address = 0x4F
    name = "Temperature Sensor"
    short_name = "T Int"
    whoisreg = 0x01                                    # config reg 
    trigger_required = False                           # can be True to use oneshot mode
    reset_command = {'reg': None,
                    'byte': None}

    unit = {'C': 'c', 
            'F': 'f', 
            'K': 'k'}
    
    current_unit = 'C'
    
    # dict with shared values name (key) and defaults (value) will be replaced with shared table on init:
    shv = {'status': 0,
           'reset_count': 0,
           't_last_reset': 0.0,
           }                                                                    
    

    def __init__(self, shared_vars):
        self.defaults = self.defaults.copy()

        self.defaults.update({'range': 150,            # 150 or 128 (extended format, normat format)
                              "resolution": 10,        # resolution in bits (8, 9, 10, 12)      #
                              "conversion_rate": 8,    # Hz of automatic sampling (0.25, 1, 4, 8)
                              'unit': 'c',             # output unit (c, f, k)
                              }
                              )
        self.settings = self.defaults.copy()

        self.out_vars = {"Temperature Internal": {"cmd": self.read_temp, 
                                                  "sel": False}
                         }

        # link to shared table
        self.shv = shared_vars

        # delete unused output vars:
        self.defaults['out_vars'] = self.out_vars.copy()
        self.out_vars = {key: self.out_vars[key] for key in
                         self.out_vars if self.out_vars[key]}
    
    def init(self):
        self.conf_msb, self.conf_lsb = 0, 0
        
        # set range:
        self.conf_lsb += 1 << 7 if self.settings["range"] == 150 else 0

        # set resolution:
        self.conf_lsb += {8: 0, 9: 1, 10: 2, 12: 3}[self.settings["resolution"]] << 5

        # set conversion rate (auto sampling rate):
        self.conf_lsb += {0.25: 0, 1: 1, 4: 2, 8: 3}[self.settings["conversion_rate"]] << 1
    
        # enable / disable timeout:
        self.conf_lsb += 1 << 4   # 1 to disable 0 to enable

        # enable / disable crc8 error checking
        self.conf_lsb += 0 << 3  # 1 to enable

        # change fault queue length no. of faults before overtemp error
        self.conf_msb += {1: 0, 2: 1, 4: 2, 6: 3}[1] << 11

        # comparator / interruptor mode
        self.conf_msb += 0 << 9             # set to 1 for interruptor mode

        self.rw_byte(reg=0x01, byte=[self.conf_msb, self.conf_lsb], mode="write")
    
    def start(self):
        """
        trigger one shot reading
        (this sensor can do one-shot or automatic, depending on settings)
        chip returns to standby after reading
        """
        self.rw_byte(reg=0x01, 
                     byte=[self.conf_msb, self.conf_lsb | 1], 
                     mode="write")
    
    def shutdown(self):
        """
        puts chip in standby

        """
        self.rw_byte(reg=0x01, 
                     byte=[self.conf_msb | 1, 
                     self.conf_lsb], mode="write")


    def read_temp(self):
        out = self.rw_byte(reg=0x00, mode="read", byte=2)
        out = self.byte2int(out, signed=True) / 0xff

        # adjust range
        if self.settings["range"] > 128:
            out *= 2

        return out  # out is already degrees C

    def conversion(self, value, var=None, unit=None, **kwargs) -> float:
        # value is already in Celcius

        unit = unit or self.unit.get(self.current_unit, 'c')

        if unit == 'f':
            value = (value * (9/5)) + 32

        elif unit == "k":
            value += 273.15

        return value

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

        return {"record": self.record,
                "temp_unit": self.current_unit,
                }

    def do_config(self, par, value):
        if par == 'temp_unit':
            self.current_unit = value



if __name__ == "__main__":
    t = TempSens()
    t.init()
    import time
    while True:
        print(t.readself())
        time.sleep(0.5)


# TODO: handle slower sample speed