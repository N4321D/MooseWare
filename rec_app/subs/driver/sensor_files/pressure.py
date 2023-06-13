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
    log("Pressure Sensor not found, dummy driver loaded", "warning")
# del DUMMY


class PressSens(Sensor):
    '''
    LPS35HW
    to read pressure, first trigger reading with PressSens().start()
    '''

    # variables
    address = 0x5C
    name = 'Pressure Internal'
    short_name = 'P Int'                               # name used after importing
    reset_command = {'reg': 0x11, 'byte': 0x02}       # Reg and value for reset
    
    # dict with shared values name (key) and defaults (value) will be replaced with shared table on init:
    shv = {'status': 0,
           'reset_count': 0,
           't_last_reset': 0.0,
           }                                                                    
        

    def __init__(self, shared_vars):
        self.defaults = self.defaults.copy()
        self.defaults.update({'unit': 'mmHg',         # set conversion in mmHg
                              'mmHg': 1 / 5460.86912,  # conv. factor for mmhg
                              'mBar': 1 / 4096,        # conv. factor for mbar
                              'c': 1 / 100,            # convert temp to degrees c
                              })
        self.settings = self.defaults.copy()

        self.out_vars = {'Pressure ' + self.name[9:]: {'cmd': self.readPress,
                                                       'sel': False},
                         'Temperature External' + self.name[9:]: False, }
        
        # link to shared table
        self.shv = shared_vars


        # delete unused output vars:
        self.defaults['out_vars'] = self.out_vars.copy()
        self.out_vars = {key: self.out_vars[key] for key in
                         self.out_vars if self.out_vars[key]}
        
        

    def init(self):
        # set sample speed at 75 Hz
        self.rw_byte(reg=0x10, byte=0x50, mode='write')

    def start(self):
        # trigger one shot reading
        self.rw_byte(reg=0x11, byte=0x01, mode='write')

    def readPress(self):
        self.shv.set(2, 'status', 0)
        # NOTE: do not use rw_bytes to read multiple bytes at once, does not work for pressure sensor
        return self.byte2int([self.rw_byte(reg=i, mode="read") for i in (0x2A, 0x29, 0x28)])

    def readTemp(self):
        self.shv.set(2, 'status', 0)
        # NOTE: do not use rw_bytes to read multiple bytes at once, does not work for pressure sensor
        return self.byte2int([self.rw_byte(reg=i, mode="read") for i in (0x2C, 0x2B)])


    def conversion(self, data_in, var=None, **kwargs):
        # this funtion converts the data from bits to:
        # mmHg (or mBar depeding on settings['unit'])
        return data_in * self.settings[self.settings['unit']]

    def json_panel(self):
        """
        return json panel with properties for kivy intrenface 
        to change in settings panel
        """
        return [{# on off button
            "title": "Record",
                "type": "bool",
                "desc": "Record data from this chip",
                "section": self.name,
                "key": "recording",
            },
            {# pressure units
            "title": "Unit",
                "type": "options",
                "desc": "Unit to record pressure in\nWarning: check that internal and external pressure are in the same unit",
                "section": self.name,
                "key": "pressure_unit",
                "options": ['mmHg', "mBar"],
            }
            ]
    
    def return_default_options(self):
        """
        returns dict with default options for kivy settings panel
        """
        return {"recording": self.record,
                "pressure_unit": self.defaults['unit']}
    
    def do_config(self, par, value):
        """
        changes config based on input
        from settings panel
        """
        if par == 'pressure_unit':
            self.settings['unit'] = value
            self.defaults['unit'] = value

class PressExt(PressSens):
    address = 0x5D
    name = 'Pressure External'
    short_name = 'P Ext'


if __name__ == "__main__":
    class SVH(dict):
        def get(*args):
            return
        def set(*args):
            return
        
    p = PressSens(SVH())
    p.init()
    import time
    while True:
        print(p.readself())
        time.sleep(0.5)


# TODO: handle slower sample speed