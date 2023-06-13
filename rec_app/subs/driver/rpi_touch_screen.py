"""
function to set raspberry pi touchscreen brightness

sudo sh -c 'echo "128" > /sys/class/backlight/rpi_backlight/brightness'
value can be 0 - 255

"""

from os import system as os_system
from platform import machine

class RpiTouchScreen():
    def __init__(self) -> None:
        self._brightness = 255
        self.dummy = True if machine() not in  {"armv7l", "aarch64"} else False

    @property
    def brightness(self):
        return self._brightness
    
    @brightness.setter
    def brightness(self, brightness):
        brightness = int(brightness)
        if brightness > 255:
            brightness = 255
        if brightness < 0:
            brightness = 0
        self._brightness = brightness

        if self.dummy:
            return

        cmd = ("sudo sh -c 'echo " 
               + f'"{brightness}"' 
               + "> /sys/class/backlight/rpi_backlight/brightness'")
        os_system(cmd)

    def set_brightness(self, brightness):
        self.brightness = brightness

if __name__ == "__main__":
    t = RpiTouchScreen()
    t.brightness = 1