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
    log("Lightstrip not found, dummy driver loaded", "warning")
del DUMMY

import time


class LightStrip(Sensor):
    # class used to control Room illumination lightstrips:
    # lightstrips are neopixel connected through a arduino

    '''
    Command bit (list with commands includes command byte (1st number))

    Write
    0:   execute last settings,  two bytes -> [0,1]
    1:   clear whole strip,  two bytes -> [1,1]
    2:   set whole strip or section to color, 8 bytes [2, R, G, B, start pixel
         MSB, start pixel LSB, length MSB, length LSB], length=0 ->
         strip until end
    3:   set single pixel color, 6 bytes [3, R, G, B, pixel number MSB,
         pixel number LSB]
    4:   set brightness, two bytes [4,brightness]
    5:   set strip length three bytes [5, MSB, LSB], strip will be cleared i.e.
         goes off. AFTER GIVING THIS WRITE, LET RBPi wait for at least 100 ms.

    Read
    4:   read brightness, returns one byte [brightness] (data might not be set
         if write case 0 has not been executed)
    5:   strip length, returns two bytes [MSB, LSB]
    128: last write given, returns 8 bytes [command, data1, data2, data3,
         data4, data5, data6, data7] (data might not be set if write case 0 has
         not been executed)

    '''

    pixel_no = 0xFF
    whoisreg = 0x00
    address = 0x2A
    name = 'Ambient Light'
    resetpin = 17                                          # set GPIO reset pin
    short_name = 'Light'                                   # name used after importing
    do_init = True
    errorout = None

        # dict with shared values name (key) and defaults (value) will be replaced with shared table on init:
    shv = {'status': -1,
           'reset_count': 0,
           't_last_reset': 0.0,
           'amb_color': 0                                  # color of light
           }   

    def __init__(self, shared_vars):
        self.defaults = self.defaults.copy()
        self.datatype = {'Ambient Light': 'u4'}

        self.out_vars = {'Ambient Light': {'cmd': self.readlight,
                                           'sel': False}
                         }

        # link to shared table
        self.shv = shared_vars

        # delete unused output vars:
        self.defaults['out_vars'] = self.out_vars.copy()
        self.out_vars = {key: self.out_vars[key] for key in
                         self.out_vars if self.out_vars[key]}
        self.settings = self.defaults.copy()
        GPIO.setup(self.resetpin, GPIO.OUT)
        GPIO.output(self.resetpin, 1)                              # start high

    def init(self):
        self.shv.set(time.time(), 't_last_reset', 0)                         # time of last boot
        time.sleep(0.11)

    def fill(self, color=[0xFF, 0xFF, 0xFF]):
        # write color
        self.rw_byte(mode='write', reg=2, byte=[*color, 0, 0, 0, 0])
        self.shv.set(self.rgb2int(*color), 'amb_color', 0)
        # trigger change
        self.rw_byte(mode='write', reg=0, byte=1)

    def read_pixel_length(self):
        """
        DO NOT USE WITH DMA DRIVER ON ARDUINO!!
        """
        log('DO NOT USE WITH DMA DRIVER ON ARDUINO!!', 'warning')
        return self.byte2int(self.rw_byte(mode='read', reg=5, byte=2))

    def read_last_command(self):
        return self.rw_byte(mode='read', reg=128, byte=8)

    @staticmethod
    def int2_rgb(inp):
        # converts 24 bit int to seperate 8-bit RGB values
        return [(inp >> 16) & 0xFF, (inp >> 8) & 0xFF, inp & 0xFF]

    @staticmethod
    def rgb2int(r, g, b):
        # converts r, g, b to 24 bit int
        return (r << 16 | g << 8 | b)

    def readlight(self):
        if self.disconnected:
            return self.errorout
        else:
            return self.shv.get('amb_color', 0)

    def reset(self):
        # arduino needs ~15s to boot after reset:
        self.shv.set(0, 'status', 0)
        if time.time() - self.shv.get('t_last_reset', 0) > 30:
            for bit in [1, 0, 1]:
                GPIO.output(self.resetpin, bit)
                time.sleep(0.01)
        self.whois()

        self.shv.set(self.shv.get('reset_count', 0) + 1, 'reset_count', 0)
        self.shv.set(time.time(), 't_last_reset', 0)

if __name__ == "__main__":
    l = LightStrip()
    l.init()
    import time
    while True:
        print(l.readself())
        time.sleep(0.5)


