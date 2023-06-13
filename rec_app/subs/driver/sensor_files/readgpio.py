from os import stat
from random import randint


try:
    try:
        from sensor_template import Sensor, logger, GPIO

    except:
        from subs.driver.sensor_files.sensor_template import Sensor, logger, GPIO
    
    DUMMY = False
except:
    # import dummy sensor
    try:
        from dummy_sensor_template import Sensor, logger, GPIO

    except:
        from subs.driver.sensor_files.dummy_sensor_template import Sensor, logger, GPIO
    DUMMY = True

def log(message, level="info"):
    cls_name = "RECORDER"
    try:
        getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here
    except AttributeError:
        print(f"{cls_name} - {level}: {message}")

if DUMMY:
    log("GPIO not found, dummy driver loaded", "warning")
del DUMMY


class ReadGpio(Sensor):
    address = -1                      # cannot be None to include in recordings
    name = 'GPIO Interface'
    short_name = 'GPIO'
    out_vars = set()
    gpio_pins_in = {18, }              # number of pin
    gpio_pins_out = {}                 # number of pin and start state
    gpio_pins_out_saved = {6: False}   # number of pin and start state

    # dict with shared values name (key) and defaults (value) will be replaced with shared table on init:
    shv = {'status': 0,
           'reset_count': 0,
           't_last_reset': 0.0,
           }                                                                    
    

    def __init__(self, shared_vars):
        self.defaults = self.defaults.copy()
        self.settings = self.defaults.copy()
        # link to shared table
        self.shv = shared_vars
        self.defaults = {}
        self.init()
    
    def init(self):
        self._setup_read_pins()
        self._setup_write_pins()

    def select_read_pins(self, pins:set):
        # setup list of read numbers of pins
        assert isinstance(pins, set)
        self.gpio_pins_in = pins
        self._setup_read_pins()

    def _setup_read_pins(self):
        for pin in self.gpio_pins_in:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # activate pin with pull down
            self.datatype[f"GPIO {pin}"] = 'u1'
        self._create_out_vars()

    def select_write_pins(self, saved=set(), unsaved=set()):
        # setup list of pins out      
        # saved indicates if pin state is saved in data files
        assert isinstance(saved, set)
        assert isinstance(unsaved, set)

        self.gpio_pins_out = unsaved
        self.gpio_pins_out_saved = saved
        
        self._setup_write_pins()
    
    def _setup_write_pins(self):
        # set saved pins
        for pin, state in self.gpio_pins_out_saved.items():
            GPIO.setup(pin, GPIO.OUT)
            self.set_gpio_pin(pin, state)

        # set unsaved pins        
        for pin, state in self.gpio_pins_out.items():
            GPIO.setup(pin, GPIO.OUT)
            self.set_gpio_pin(pin, state)
        
        self._create_out_vars()

    def set_gpio_pin(self, pin, state):
        GPIO.output(pin, state)
        if pin in self.gpio_pins_out_saved:
            self.gpio_pins_out_saved[pin] = state
        else:
            self.gpio_pins_out[pin] = state

    def _create_out_vars(self):
        self.out_vars.clear()
        self.datatype.clear()
        for pin in (self.gpio_pins_in | 
                    self.gpio_pins_out_saved.keys()):
            self.out_vars.add(f"GPIO {pin}")
            self.datatype[f"GPIO {pin}"] = 'u1'

    def whois(self):
        self.disconnected = False
        self.shv.set(1, 'status', 0)
        return 0x01

    def readself(self):
        self.shv.set(2, 'status', 0)

        output = {}
        for pin in self.gpio_pins_in:
            output[f'GPIO {pin}'] = GPIO.input(pin)
        _status = 0 
        
        for pin, state in self.gpio_pins_out_saved.items():
            output[f'GPIO {pin}'] = GPIO.input(pin)
            _status += output[f'GPIO {pin}']
        
        if _status > 0:
            self.shv.set(4, 'status', 0)

        self.disconnected = False
        
        return output

    def reset(self):
        pass

    def rw_byte(self, *args, **kwargs):
        pass

    def json_panel(self):
        """
        return json panel with properties for kivy intrenface 
        to change in settings panel
        """
        # TODO: add on off switches for each gpio -> 
        #       figure out a way to save disabled in or out ports to reenable them later
        
        panel = [{# on off button
                  "title": "Record",
                  "type": "bool",
                  "desc": "Record data from GPIO ports",
                  "section": self.name,
                  "key": "recording",
                }] # + [
                #   {# gpio pins
                #    "title": f"GPIO {pin}: IN",
                #    "type": "bool",
                #    "desc": "record from this pin",
                #    "section": self.name,
                #    "key": str(pin),
                #    } for pin in self.gpio_pins_in] + [
                #   {# gpio pins
                #    "title": f"GPIO {pin}: OUT",
                #    "type": "bool",
                #    "desc": "record from this pin",
                #    "section": self.name,
                #    "key": str(pin),
                #    } for pin in self.gpio_pins_out_saved
                #    ] 
            
        return panel
    
    # def do_config(self, par, value):
    #     """
    #     changes config based on input
    #     from settings panel
    #     """
    #     print(par, value)
    #     if par in self.gpio_pins_in and value is 0:
    #         self.select_read_pins(self.gpio_pins_in.remove(par))
    #     if par in self.gpio_pins_in and value is 1:
    #         self.select_read_pins(self.gpio_pins_in.remove(par))


if __name__ == "__main__":
    s = ReadGpio()
    s.init()
    import time
    while True:
        print(s.readself())
        time.sleep(0.5)


# TODO: handle slower sample speed