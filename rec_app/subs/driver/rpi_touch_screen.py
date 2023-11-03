"""
function to set raspberry pi touchscreen brightness

sudo sh -c 'echo "128" > /sys/class/backlight/10-0045/brightness'
value can be 0 - 255

"""

import os
from pathlib import Path
from platform import machine

from subs.log import create_logger

logger = create_logger()

def log(message, level="info"):
    cls_name = "TOUCHSCREEN"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here



class RpiTouchScreen():
    TOUCH_SCREEN_NAME = ""
    def __init__(self) -> None:
        self._brightness = 255
        self.dummy = True if machine() not in  {"armv7l", "aarch64"} else False
        if not self.dummy:
            try:
                self.TOUCH_SCREEN_NAME = next(Path("/sys/class/backlight").glob("*")).name
            except StopIteration:
                log("No backlight dir found", "warning")
        


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
               + f"> /sys/class/backlight/{self.TOUCH_SCREEN_NAME}/brightness'")
        p = os.popen(cmd)
        result = p.read()
        if result != f"{brightness}\n":
            log(f"Error setting screen brightness: {result}", "warning")
        p.close()

    def set_brightness(self, brightness):
        self.brightness = brightness

if __name__ == "__main__":
    t = RpiTouchScreen()
    t.brightness = 1