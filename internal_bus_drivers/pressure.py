from i2csensor import I2CSensor


class PressureInt(I2CSensor):
    NAME = "Pressure Internal"
    SHORT_NAME = "PInt"
    ADDRESS = 0x5C
    PARAMETER_NAMES = ("Pressure", "Temperature")
    PARAMETER_SHORT_NAMES = ("PRS", "TMP")

    # Chip Specific

    def init(self):
        self.STATUS = 5
        self.writeI2C(self.ADDRESS, 0x10, 0x50)

    def sample(self):
        if self.readI2C(self.ADDRESS, 0x28, 5):
            self.error_count = 0
        else:
            self.error_count += 1

    def dataToJSON(self):
        self.dict_out["PRS"] = (
            int.from_bytes(self.sampled_data[:3], byteorder="little") / 5460.86912
        )
        self.dict_out["TMP"] = (
            int.from_bytes(self.sampled_data[3:], byteorder="little") / 100
        )


class PressureExt(PressureInt):
    NAME = "Pressure External"
    SHORT_NAME = "PExt"
    ADDRESS = 0x5d