from sensor_template import Sensor

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)

except:
    from math import sin
    import time
    class GPIO():
        IN = True
        OUT = True
        PUD_DOWN = True
        DUMMY_GPIO = True
        def setup(self, *args, **kwargs):
            return
        def output(self, *args, **kwargs):
            return
        def input(self, *args, **kwargs):
            return bool(round(sin(time.time())))
        
    DUMMY = True

class GpioRecorder(Sensor):
    """
    pin 6 out
    pin18 input
    """
    NAME = "GPIO Pins"
    SHORT_NAME = "GPIO"
    PARAMETER_NAMES = ("GPIO 6", "GPIO 18")
    PARAMETER_SHORT_NAMES = ("6", "18")

    def __init__(self) -> None:
        if hasattr(GPIO, "DUMMY_GPIO"):
            self._TESTING = True
        self._setup_read_pins()
        self._setup_write_pins()

    def init(self):
        self.STATUS = 5

    def dataToJSON(self):
        self.dict_out["6"] = GPIO.input(6)
        self.dict_out["18"] = GPIO.input(18)
        self.STATUS = 10 if self.dict_out["18"] else 5

    def procCmd(self, key, value):
        GPIO.output(key, value)
    
    def stop(self):
        GPIO.output(6, False)
        self.STATUS = 0

    def _setup_read_pins(self):
        GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    def _setup_write_pins(self):
        GPIO.setup(6, GPIO.OUT)
        GPIO.output(6, False)
    