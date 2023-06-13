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
    log("Motion Sensor not found, dummy driver loaded", "warning")
del DUMMY

from math import pi


class MoSens(Sensor):
    '''
    LMS6DS3

    '''
    # variables
    address = 0x6B
    whoisreg = 0x0F
    name = 'Motion'
    short_name = 'Motion'                               # name used after importing
    motionaxes = {'Ang. X': (0x23, 0x22),
                  'Ang. Y': (0x25, 0x24),
                  'Ang. Z': (0x27, 0x26),
                  'Lin. X': (0x29, 0x28),
                  'Lin. Y': (0x2B, 0x2A),
                  'Lin. Z': (0x2D, 0x2C)}

    reset_command = {'reg': 0x12, 'byte': 0x01}       # Reg and value for reset

    ang_sens_mode = {"2.18 rad./s": (0x11, 0b10000010), "4.36 rad./s":(0x11, 0b10000000), 
                     "8.73 rad./s": (0x11, 0b10000100), "17.45 rad./s": (0x11, 0b10001000), 
                     "34.91 rad./s":(0x11, 0b10001100)}
    current_ang_sens = "8.73 rad./s"
    lin_sens_mode = {"2 g": (0x10, 0b10010000), "4 g": (0x10, 0b10011000), 
                     "8 g": (0x10, 0b10011100), "16 g":(0x10, 0b10010100)}
    current_lin_sens = "2 g"

    # dict with shared values name (key) and defaults (value) will be replaced with shared table on init:
    shv = {'status': 0,
           'reset_count': 0,
           't_last_reset': 0.0,
           }   

    def __init__(self, shared_vars):
        self.defaults = self.defaults.copy()
        self.defaults.update({'ang_sensitivity': {"2.18 rad./s": 2.18, "4.36 rad./s": 4.36, 
                                                  "8.73 rad./s": 8.73, "17.45 rad./s": 17.45,
                                                  "34.91 rad./s": 34.91},      # ang rad/s
                              'lin_sensitivity': {"2 g": 2, "4 g": 4, "8 g": 8, "16 g": 16}, # max lin movement g/s
                              })

        self.out_vars = {self.name + ' Ang. X': {'cmd': True,
                                                 'sel': 'Ang. X'},
                         self.name + ' Ang. Y':  {'cmd': True,
                                                  'sel': 'Ang. Y'},
                         self.name + ' Ang. Z': {'cmd': True,
                                                 'sel': 'Ang. Z'},
                         self.name + ' Lin. X': {'cmd': True,
                                                 'sel': 'Lin. X'},
                         self.name + ' Lin. Y': {'cmd': True,
                                                 'sel': 'Lin. Y'},
                         self.name + ' Lin. Z': {'cmd': True,
                                                 'sel': 'Lin. Z'},
                         }     # dict with output vars and function to read
        
        # link to shared table
        self.shv = shared_vars

        # delete unused output vars:
        self.defaults['out_vars'] = self.out_vars.copy()
        # self.out_vars = {key: self.out_vars[key] for key in
        #                  self.out_vars if self.out_vars[key]}
        self.settings = self.defaults.copy()

    def init(self):
        # set zero
        reglist = [0x01, 0x04, 0x06, 0x07, 0x08, 0x09,
                   0x0A, 0x0B, 0x13, 0x14, 0x15, 0x16,
                   0x17, 0x1A]
        for reg in reglist:
            self.rw_byte(mode='write', reg=reg, byte=0x00)

        # set defaults
        b_d = {0x0D: 0b01000000,  # set intial data ready & FIFO bits
               0x0E: 0b00000011,  # set initial data ready bits
            #    0x10: 0b10010000,  # 0b01010010,  # set sample linear speed and filter
            #    0x11: 0b10000100,  # 0b01010100,  # set sample angular speed
               0x12: 0b00000100,  # set register in i2c mode
               0x18: 0b00111000,  # enable X Y and Z axis on linear sensor
               0x19: 0b00111000,  # enable X Y and Z axis on angular sensor
               }
        [self.rw_byte(mode='write', reg=reg, byte=byte) for reg, byte in b_d.items()]
        
        self.set_ang_sensitivity()
        self.set_lin_sensitivity()

    def setspeedlin(self, samplespeed=0b0101, acc_scale=0b00, aafilter=0b10):
        # use to change linear sensitivity
        self.rw_byte(mode='write', reg=0x10,
                     byte=(samplespeed << 4 | acc_scale << 2 | aafilter))

    def setspeedang(self, samplespeed=0b0101, gyr_scale=0b00, fs125=0b00):
        # use to change angular sensitivity
        self.rw_byte(mode='write', reg=0x11,
                     byte=(samplespeed << 4 | gyr_scale << 3 | fs125 | 0b0))
    
    def set_ang_sensitivity(self):
        reg, byte = self.ang_sens_mode[self.current_ang_sens]
        self.rw_byte(mode="write", reg=reg, byte=byte)

    def set_lin_sensitivity(self):
        reg, byte = self.lin_sens_mode[self.current_lin_sens]
        self.rw_byte(mode="write", reg=reg, byte=byte)

    # def sample(self, axis):
    #     output = [self.rw_byte(mode='read', reg=reg)
    #               for reg in self.motionaxes[axis]]
    #     output = self.byte2int(output, signed=True)
        
    def readself(self):
        self.shv.set(2, 'status', 0)
        _read = self.rw_byte(mode="read", reg=0x22, byte=12)
        output = {}
        for ax, lsb, msb in zip(self.out_vars, _read[::2], _read[1::2]):
            output[ax] = self.conversion(self.byte2int((msb, lsb), signed=True), ax)
        return output
        

    def conversion(self, data_in, var=None, **kwargs):
        # this funtion converts the data from bits to:
        # rads / sec
        if 'Ang' in var:
            return ((data_in / 0x7FFF) 
                    * self.settings['ang_sensitivity'][self.current_ang_sens])

        else:
            return ((data_in / 0x7FFF) 
                    * self.settings['lin_sensitivity'][self.current_lin_sens] * 2)
    
    def json_panel(self):
        """
        return json panel with properties for kivy intrenface 
        to change in settings panel
        """

        panel = [{"title": "Record",
                "type": "bool",
                "desc": "Record data from this chip",
                "section": self.name,
                "key": "recording",
                },
                {"title": "Angular Sensitivity",
                "type": "options",
                "desc": "Sensitivity of the angular movement sensor",
                "section": self.name,
                "key": "ang_sensitivity",
                "options": list(self.ang_sens_mode),
                },
                {"title": "Linear Sensitivity",
                "type": "options",
                "desc": "Sensitivity of the linear movement sensor",
                "section": self.name,
                "key": "lin_sensitivity",
                "options": list(self.lin_sens_mode),
                },
        ]
        return panel

    def return_default_options(self):
        """
        returns dict with default options for kivy settings panel
        """

        return {"recording": self.record,
                "ang_sensitivity": self.current_ang_sens,
                "lin_sensitivity": self.current_lin_sens,
        }

    def do_config(self, par, value):
        if par == 'ang_sensitivity':
            self.current_ang_sens = value
            self.set_ang_sensitivity()
        elif par == 'lin_sensitivity':
            self.current_lin_sens = value
            self.set_lin_sensitivity()
        else:
            print(f"Motion Sensor: config not found: {par}:{value}")

if __name__ == "__main__":
    m = MoSens()
    m.init()
    import time
    while True:
        print(m.readself())
        time.sleep(0.5)


# TODO: handle slower sample speed