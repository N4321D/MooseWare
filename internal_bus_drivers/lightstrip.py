from sensor_template import I2CSensor

import time

class LightStrip(I2CSensor):
    """
    driver for i2c lightstrip

    """

    NAME = "Ambient Light"
    SHORT_NAME = "Light"
    ADDRESS = 0x55

    PARAMETER_NAMES = ("Light Color (RGB)",)
    PARAMETER_SHORT_NAMES = ("RGB",)

    # sensor specific
    current_color = [0, 0, 0]

    def sample(self):
        if self.readI2C(self.ADDRESS, 0x00, 0):
            self.error_count = 0
        else:
            self.error_count += 1
    
    def dataToJSON(self):
        self.dict_out["RGB"] = self.rgb2int(*self.current_color)
    
    def procCmd(self, key, value):
        if key == "fill":
            self.fill(value)

    def fill(self, color=[0xFF] * 3):
        """
        Fill Lightstrip with specified color (R, G, B)

        Args:
            color (list, optional): Color. Defaults to [0xFF]*3.
        """
        # write color:
        if (self.writeI2C(self.ADDRESS, 2, color + [0] * 4)  # change color
            and self.writeI2C(self.ADDRESS, 0, 1)        # trigger change
            ):
            self.error_count = 0
            
            self.current_color = color  # save current color

        else:
            self.error_count += 1

    @staticmethod
    def rgb2int(*color):
        """
        convert R, G, B values in to int

        Returns:
            int: color value
        """
        return int.from_bytes(color, byteorder="big")
