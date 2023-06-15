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
        # change CLASSNAME here
        getattr(logger, level)(f"{cls_name}: {message}")
    except AttributeError:
        print(f"{cls_name} - {level}: {message}")


if DUMMY:
    log("Motion Sensor not found, dummy driver loaded", "warning")
del DUMMY


class GasSens(Sensor):
    '''

    '''
    # variables
    address = 0x77
    whoisreg = 0x55
    name = 'VOC Gas Sensor'
    short_name = 'Gas'                               # name used after importing

    reset_command = {'reg': 0x12, 'byte': 0x01}       # Reg and value for reset

    # dict with shared values name (key) and defaults (value) will be replaced with shared table on init:
    shv = {'status': 0,
           'reset_count': 0,
           't_last_reset': 0.0,
           }

    def __init__(self, shared_vars):
        self.defaults = self.defaults.copy()
        # self.defaults.update({})

        self.out_vars = {"ppm. Gas": {'cmd': True,
                                      'sel': False},
                         }     # dict with output vars and function to read

        # link to shared table
        self.shv = shared_vars

        # delete unused output vars:
        self.defaults['out_vars'] = self.out_vars.copy()
        self.settings = self.defaults.copy()

    def init(self):
        pass

    def readself(self):
        self.shv.set(2, 'status', 0)
        _read = self.rw_byte(mode="read", reg=0x22, byte=12)
        output = {}
        for ax, lsb, msb in zip(self.out_vars, _read[::2], _read[1::2]):
            output[ax] = self.conversion(
                self.byte2int((msb, lsb), signed=True), ax)
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
                #  {"title": "Angular Sensitivity",
                #  "type": "options",
                #   "desc": "Sensitivity of the angular movement sensor",
                #   "section": self.name,
                #   "key": "ang_sensitivity",
                #   "options": list(self.ang_sens_mode),
                #   },
                #  {"title": "Linear Sensitivity",
                #  "type": "options",
                #   "desc": "Sensitivity of the linear movement sensor",
                #   "section": self.name,
                #   "key": "lin_sensitivity",
                #   "options": list(self.lin_sens_mode),
                #   },
                 ]
        return panel


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
