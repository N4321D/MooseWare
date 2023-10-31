from internal_bus_drivers.i2csensor import I2CSensor
import time

class OISSensor(I2CSensor):
    NAME = "Optical Intrinsic Signal"
    SHORT_NAME = "OIS"
    ADDRESS = 0x5B

    PARAMETER_NAMES = ("OIS Singal", "OIS Background", "OIS Stimulation mA", "OIS Green LED mA")
    PARAMETER_SHORT_NAMES = ("SIG", "BGR", "STIM", "PWR")

    control_str = [{"title": "Blue Light Stimulation",
                   "type": "stim",
                   "desc": "Create / Start / Stop Blue Light Stim. Protocol",
                   "key": "stim",
                   },
                   {"title": "Green Led Intensity",
                    "type": "plusmin",
                    "desc": "Green LED power in %",
                    "key": "amps",
                    "steps": [[0, 10, 1], [10, 20, 2], [30, 60, 5], [60, 200, 10]],
                    "limits": [0, 100],
                    "live_widget": True},
                   ]

    # Sensor specific:
    stim_end = 0                # stim end time in us
    stim_amp = 0                # stim amplitde
    green_amps = 5              # green LED amplitude 
    MAX_AMP = 63                # max amplitude in mA for all leds

    def init(self):
        self.set_mode(True)
        self.set_amps(self.green_amps)
    
    def trigger(self):
        self.writeI2C(self.ADDRESS, 0x47, 0x01) # trigger 1 shot reading
    
    def sample(self):
        self.check_stim()
        if self.readI2C(self.ADDRESS, 0x54, 4):
            self.error_count = 0
        else:
            self.error_count += 1

    # Chip specific Functions
    def set_mode(self, green=True):
        self.STATUS = 5 if green else 10
        self.writeI2C(self.ADDRESS, 0x41, 0x87 if green else 0x97)
    
    def set_amps(self, amp, green=True):
        if amp > self.MAX_AMP:
            amp = self.MAX_AMP
        
        if green:
            self.green_amps = amp
            out = (amp, amp)
        
        else:
            self.stim_amp = amp
            out = (0b10 << 6 | amp, 0b1<<7 | amp)

        self.writeI2C(self.ADDRESS, 0x42, out)

    def check_stim(self):
        if self.stim_amp:
            if (time.perf_counter_ns() // 1_000_000) >= self.stim_end:
                # stop stim
                self.stim_amp = 0
                self.set_amps(self.green_amps)
                self.set_mode(True)
    
    def start_stim(self, time_amps):

        self.stim_end = time.perf_counter_ns() // 1_000_000 + time_amps[0]
        
        amp = int((time_amps[1] / 100) * self.MAX_AMP)
        
        if amp:
            # Pulse on
            self.set_amps(amp, False)
            self.set_mode(False)
        else:
            # Pulse off
            self.set_amps(self.green_amps, True)
    
    def dataToJSON(self):
        self.dict_out['SIG'] = int.from_bytes(self.sampled_data[2:4], byteorder='little') / 0xFFFF
        self.dict_out['BGR'] = int.from_bytes(self.sampled_data[:2], byteorder='little') / 0xFFFF
        self.dict_out['STIM'] = self.stim_amp
        self.dict_out['PWR'] = self.green_amps
        return self.dict_out

    def procCmd(self, key, value):
        if key == "amps":
            self.set_amps((value / 100) * self.MAX_AMP, 
                          True)
        elif key == "stim":
            self.start_stim(value)
    
    def stop(self):
        # stop stim
        self.set_amps(self.green_amps, True)
        self.set_mode(True)