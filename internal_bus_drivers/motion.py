from sensor_template import I2CSensor


class MOTSensor(I2CSensor):
    NAME = "Motion Sensor"
    SHORT_NAME = "MOT"
    ADDRESS = 0x6B
    PARAMETER_NAMES = (
        "Motion Ang. X",
        "Motion Ang. Y",
        "Motion Ang. Z",
        "Motion Lin. X",
        "Motion Lin. Y",
        "Motion Lin. Z",
    )
    PARAMETER_SHORT_NAMES = ("AX", "AY", "AZ", "LX", "LY", "LZ")

    # Chip Specific
    ang_sens_bytes = (0b10000010, 0b10000000, 0b10000100, 0b10001000, 0b10001100)
    ang_sens_val = (2.18, 4.36, 8.73, 17.45, 34.91)
    ang_sens_unit = "rad/s"
    lin_sens_bytes = (0b10010000, 0b10011000, 0b10011100, 0b10010100)
    lin_sens_val = (2, 4, 8, 16)
    lin_sens_unit = "g"
    ang_sensitivity = 2
    lin_sensitivity = 0
    control_str = [
        {
            "title": "Angular Sensitivity",
            "type": "options",
            "desc": f"Sensitivity of the angular movement sensor in {ang_sens_unit}",
            "key": "asens",
            "options": ang_sens_val,
            "default_value": 8.73,
        },
        {
            "title": "Linear Sensitivity",
            "type": "options",
            "desc": f"Sensitivity of the linear movement sensor in {lin_sens_unit}",
            "key": "lsens",
            "options": lin_sens_val,
            "default_value": 2,
        },
    ]

    def init(self):
        [
            self.writeI2C(self.ADDRESS, r, 0x00)
            for r in (
                0x01,
                0x04,
                0x06,
                0x07,
                0x08,
                0x09,
                0x0A,
                0x0B,
                0x13,
                0x14,
                0x15,
                0x16,
                0x17,
                0x1A,
            )
        ]
        [
            self.writeI2C(self.ADDRESS, r, data)
            for r, data in {
                0x0D: [0b01000000, 0b00000011], # set intial data ready & FIFO bits
                # 0x0E: 0b00000011, # set initial data ready bits
                0x12: 0b00000100, # set to i2c mode
                0x18: [0b00111000] * 2, # enable X Y and Z axis on linear /ang sensor 
                # 0x19: 0b00111000, # enable X Y and Z axis on angular sensor
            }.items()
        ]
        self.set_lin_sensitivity()
        self.set_ang_sensitivity()
        self.STATUS = 5
    
    def sample(self):
        if self.readI2C(self.ADDRESS, 0x22, 12):
            self.error_count = 0
        else:
            self.error_count += 1
    
    # Chip Specific functions
    def set_ang_sensitivity(self, sensitivity=0):
        if sensitivity:
            self.ang_sensitivity = self.ang_sens_val.index(sensitivity)
        self.writeI2C(self.ADDRESS, 0x11, self.ang_sens_bytes[self.ang_sensitivity])
    
    def set_lin_sensitivity(self, sensitivity=0):
        if sensitivity:
            self.lin_sensitivity = self.lin_sens_val.index(sensitivity)
        self.writeI2C(self.ADDRESS, 0x10, self.lin_sens_bytes[self.lin_sensitivity])

    def reset_procedure(self):
        self.writeI2C(self.ADDRESS, 0x12, 0x01)
    
    def dataToJSON(self):
        for i, (par, lsb, msb) in enumerate(zip(self.PARAMETER_SHORT_NAMES, 
                                self.sampled_data[::2], 
                                self.sampled_data[1::2])):
            if i < 3:
                mp = self.ang_sens_val[self.ang_sensitivity]  
            else:  
                mp = self.lin_sens_val[self.lin_sensitivity]        
            self.dict_out[par] = (int.from_bytes((msb, lsb), byteorder='little', signed=True) / 0x7FFF) * mp
        return self.dict_out
        
    def procCmd(self, key, value):
        if key == "asens":
            self.set_ang_sensitivity(value)
        elif key == "lsens":
            self.set_lin_sensitivity(value)



