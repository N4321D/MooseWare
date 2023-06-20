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
    log("OIS Sensor not found, dummy driver loaded", "warning")
del DUMMY

import time

class LightSens(Sensor):
    '''

    BH1792GLC

    call with LightSens().whois()

    test lights with: LightSens().ledcontrol(mode,mA)
        mode can be: 'green', 'ir', 'pulse' or a vector with max [0b11, 0b1]
        mA is a vector with 0-63 in mA

    start by setting led control, then measurement mode
    (use single for 1 shot),
    then use start to trigger) next read value

    sensor.status indicates state of the sensor:
    0: N.C. / Error, sensor lost connection/ os error / ...
    1: Sensor connected, standby
    2: Green LED -> Recording
    3: Green LED -> in Stim prot
    4: Blue LED -> STIM PROT

    '''
    # variables
    address = 0x5B
    # limit for Leds in mA
    limitA = 65
    name = 'OIS'
    # name used after importing
    short_name = 'OIS'
    # Reg and value for reset
    reset_command = {'reg': 0x41, 'byte': 0x01}
    # trigger required for 1 shot reading
    trigger_required = True

    # indicates that stim is on
    stim_on = False
    # current stim amp
    current_stimamp = 0
    # stimulation protocol  [(on time, off time, mA), ...]
    stim_protocol = []

    stim_start = None

    # dict with shared values name (key) and defaults (value) will be replaced with shared table on init:
    shv = {'status': 0,
           'reset_count': 0,
           't_last_reset': 0.0,
           # number of completed stim (postition in protocol)
           'stim_count': 0,
           # power of last stim
           'last_stim_mA': 0,
           # duration of last stim (sec.)
           'last_stim_dur': 0.0,
           # power of green LEDS
           'amps': (5, 5),
           }

    def __init__(self, shared_vars):
        self.defaults = self.defaults.copy()
        self.defaults.update({'color': 'green',     # start color for recording
                              'mode': 'single',          # def mode for setmode
                              'color_mode': 'pulse',  # def mode for ledcontrol
                              })                  # default settings for sensor

        self.out_vars = {'OIS Background': {'cmd': True,
                                            'sel': 'background'},
                         'OIS Signal':  {'cmd': True,
                                         'sel': 'signal'},
                         "OIS LED Current": {"cmd": True,
                                             "sel": False},
                         "OIS Stimulation Current": {"cmd": True,
                                                     "sel": False}
                         }      # dict with output vars and function to read

        self.datatype = {"OIS Stimulation Current": 'u1',
                         "OIS LED Current": 'u1'}

        # link to shared table
        self.shv = shared_vars

        # delete unused output vars:
        self.defaults['out_vars'] = self.out_vars.copy()
        self.out_vars = {key: self.out_vars[key] for key in
                         self.out_vars if self.out_vars[key]}

        self.settings = self.defaults.copy()
        self.last_value = {k: float('NaN') for k in self.out_vars}

        self.init()

    def init(self):
        # set pulse mode to last mA
        self.ledcontrol(self.settings['color_mode'], self.shv.get('amps'))

        # set last light mode
        self.setmode(self.settings['mode'], self.settings['color'])

    def ledcontrol(self, mode, mA):
        if not hasattr(mA, "__iter__"):
            mA = (mA, mA)

        # set continuous led on or pulsing mode
        if mode == 'green':
            # green test mode (led continuously on)
            mode1 = 0b11
            mode2 = 0b0

        elif mode == 'ir':
            # ir test mode (led continuously on)
            mode1 = 0b10
            mode2 = 0b1

        elif mode == 'pulse':
            # Rec mode, (single pulse + backgr recording)
            self.shv.set(mA, 'amps')     # save amps if setting green light
            mode1 = 0b00
            mode2 = 0b0

        else:
            # see spec sheet chip for details
            mode1 = mode[0]
            # see spec sheet chip for details
            mode2 = mode[1]

        amp1, amp2 = mA                     # 0 - 63 in mA

        if amp1 > self.limitA:
            amp1 = self.limitA
        if amp2 > self.limitA:
            amp2 = self.limitA

        self.rw_byte(mode="write", reg=0x42, byte=[(mode1 << 6 | int(amp1)),
                                                   (mode2 << 7 | int(amp2))])

    def setmode(self, mode, color):
        # set color
        if mode == 'single':
            mode1 = 0b111
        else:
            mode1 = mode

        if color == 'green':
            c = 0b0
        elif color == 'ir':
            c = 0b1

        self.rw_byte(mode='write',
                     reg=0x41,
                     byte=(0b1 << 7 | c << 4 | mode1))

    def start(self):
        '''
        Trigger 1shot reading
        '''
        if self.settings['color_mode'] == 'pulse':
            self.rw_byte(mode='write', reg=0x47, byte=0x01)

    def readself(self):
        self.last_value["OIS Stimulation Current"] = self.stimulate()

        self.last_value['OIS LED Current'] = self.shv.get('amps', 0)

        if self.settings['color_mode'] == 'pulse':
            if self.settings['color'] == 'ir':
                _out = self.rw_byte(mode='read', reg=0x50, byte=4)

            elif self.settings['color'] == 'green':
                _out = self.rw_byte(mode='read', reg=0x54, byte=4)

            self.last_value["OIS Background"] = self.conversion(
                self.byte2int((_out[0], _out[1]), order="little"))
            self.last_value["OIS Signal"] = self.conversion(
                self.byte2int((_out[2], _out[3]), order="little"))

        # set last value if stimulating
        return self.last_value

    def conversion(self, data_in, var=None, **kwargs):
        # this function converts the data from bits to values from 0 - 1
        return (data_in / 0xFFFF)

    def set_stim_protocol(self, protocol):
        # reset stim:
        self.stim_start = None

        # set new protocol
        self.stim_protocol = protocol

    # STIMULATION
    def set_stim_protocol(self, protocol):
        """
        set a stim protocol here to start stim during recording
        """
        self.stim_protocol = protocol

    def stimulate(self, delay=0):
        """
        this method is called each cycle as long as stimulating

        delay: Use to plan stimulation start in next clockcycle
        (delay should be 1/F, or n/F where n is the amount of cycles to wait)

        stimulation returns 0 (stimulation amp) when there is no stim protocol.
        When there is a stim protocol, the stim protocol is executed and the stim 
        amp is returned
        """
        if not self.stim_protocol:
            self.shv.set(2, 'status', 0)
            return 0

        _t = time.time()

        # start time of stimulation (stim on times in protocol
        # are relative to start time):
        if self.stim_start is None:
            # Start new protocol
            self.stim_start = _t + delay
            self.shv.set(0, 'stim_count', 0)          # reset stim counter

        _start, _stop = self.stim_protocol[0][:2]

        _t -= self.stim_start

        if _stop == 0 or _stop <= _t and self.stim_on is True:
            self._stim_off()

        elif _start <= _t < _stop and self.stim_on is False:
            self._stim_on()

        return self.current_stimamp

    def _stim_on(self):
        """
        Turns stimulation ON.
        """
        # turn stim on
        self.ledcontrol('ir', (self.stim_protocol[0][2],
                               self.stim_protocol[0][2])
                        )
        self.settings['color_mode'] = 'ir'
        self.stim_on = True
        self.current_stimamp = int(self.stim_protocol[0][2])
        self.shv.set(4, 'status', 0)             # blue led on

    def _stim_off(self):
        # turn stim off return to single shot mode
        self.settings['color_mode'] = 'pulse'
        self.ledcontrol('pulse', self.shv.get('amps'))
        self.stim_on = False

        _start, _stop, _mA = self.stim_protocol.pop(0)

        # Return last stim to GUI
        if (_start, _stop, _mA) != (0, 0, 0):    # don't register stimstop
            self.shv.set(self.shv.get('stim_count', 0) + 1, 'stim_count', 0)
            self.shv.set(_mA, 'last_stim_mA', 0)
            self.shv.set(_stop - _start, 'last_stim_dur', 0)
            self.shv.set(3, 'status', 0)

        if not self.stim_protocol:
            # Stim ended
            self.stim_start = None
            self.shv.set(2, 'status', 0)

        self.current_stimamp = 0

    def _stop(self):
        # reset all stim pars
        self.settings['color_mode'] = 'pulse'

        self.shv.set(0, 'stim_count', 0)
        self.shv.set(0, 'last_stim_mA', 0)
        self.shv.set(0, 'last_stim_dur', 0)

        # Force green LEDS to 0 amps: NOTE do not use led control becuase that will erase last amp value
        self.rw_byte(mode="write", reg=0x42,
                     byte=[(0b00 << 6 | 0), (0b0 << 7 | 0)])

    def json_panel(self):
        """
        return json panel with properties for kivy interface 
        to change in settings panel
        """

        panel = [{"title": "Record",
                  "type": "bool",
                  "desc": "Record data from this chip",
                    "section": self.name,
                    "key": "record",
                  },
                 {"title": "Green Led Intensity",
                  "type": "plusminin",
                    "desc": "Power in mA of the green LEDs",
                    "section": "recording",
                    "key": "ois_ma",
                    # [min of range, max of range, step in range]
                    "steps": [[0, 10, 1], [10, 20, 2], [20, 100, 10]],
                    "limits": [0, 60],   # [min, max]
                    "live_widget": True
                  },
                 ]
        return panel


if __name__ == "__main__":
    l = LightSens()
    l.init()
    import time
    while True:
        l.start()
        print(l.readself())
        time.sleep(0.5)


# TODO: handle slower sample speed
