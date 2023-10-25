"""
Room control screen

NB: Kv String cannot contain \n -> must be \\n

"""

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import (BooleanProperty, ListProperty, 
                             StringProperty, NumericProperty)
from subs.gui.vars import *

from subs.gui.screens.scr import Scr

import numpy as np
import time

kv_str = """
#:kivy 1.10.1

<LabRoom@Label>:
    pos_hint: {'right': 0.25, 'top': 0.45} #relative sizes 0-1
    size_hint: 0.1, 0.1
    font_size: '15sp'
    valign: 'bottom'
    halign: 'right'

# ROOM SCREEN & BUTTONS
<RoomScreen>:
    on_enter:
        self.main()

    # on_leave:
    LabRoom:
        pos_hint: {'right': 0.25, 'top': 0.6} #relative sizes 0-1
        size_hint: 0.1, 0.1
        text: 'min:'
        color: root.text_color

    LabRoom:
        pos_hint: {'right': 0.25, 'top': 0.45} #relative sizes 0-1
        text: 'max:'
        size_hint: 0.1, 0.1
        color: root.text_color

    LabRoom:
        id: Temperature
        pos_hint: {'right': 0.4, 'top': 0.9} #relative sizes 0-1
        size_hint: 0.2, 0.1
        text: 'Temperature:'
        font_size: '15sp'
        color: root.text_color
        valign: 'bottom'

    Label:
        id: Temperature Externalvallast
        pos_hint: {'right': 0.4, 'top': 0.85} #relative sizes 0-1
        size_hint: 0.2, 0.2
        text: '[b]%.1f %sC[/b]' % (self.val, u'\\N{DEGREE SIGN}')
        font_size: '30sp'
        color: root.warning_color if not (root.data['Temperature External']['lim_min'] < self.val < root.data['Temperature External']['lim_max']) else root.text_color
        markup: True
        val: 0

    Label:
        id: Temperature Externalvalmax
        pos_hint: {'right': 0.4, 'top': 0.5} #relative sizes 0-1
        size_hint: 0.2, 0.2
        text: '%.1f %sC' % (self.val, u'\\N{DEGREE SIGN}')
        font_size: '30sp'
        color: root.warning_color if not (root.data['Temperature External']['lim_min'] < self.val < root.data['Temperature External']['lim_max']) else root.text_color
        val: 0

    Label:
        id: Temperature Externalvalmin
        pos_hint: {'right': 0.4, 'top': 0.65} #relative sizes 0-1
        size_hint: 0.2, 0.2
        text: '%.1f %sC' % (self.val, u'\\N{DEGREE SIGN}')
        font_size: '30sp'
        color: root.warning_color if not (root.data['Temperature External']['lim_min'] < self.val < root.data['Temperature External']['lim_max']) else root.text_color
        val: 0

    Label:
        id: Pressure Internal
        pos_hint: {'right': 0.6, 'top': 0.9} #relative sizes 0-1
        size_hint: 0.2, 0.1
        text: 'Room Pressure:'
        font_size: '15sp'
        color: root.text_color
        valign: 'bottom'

    Label:
        id: press_diff
        pos_hint: {'right': 0.6, 'top': 0.3} #relative sizes 0-1
        size_hint: 0.2, 0.1
        text: ''
        font_size: '20sp'
        valign: 'bottom'
        markup: True
        color: root.warning_color if self.text == '[b]POSITIVE[/b]' else ((0, 1, 0, 1) if root.day else root.text_color)

    Label:
        id: Pressure Internalvallast
        pos_hint: {'right': 0.6, 'top': 0.85} #relative sizes 0-1
        size_hint: 0.2, 0.2
        text: '[b]%.0f [size=15sp]mBar[/size][/b]' % (self.val)
        font_size: '30sp'
        color: root.warning_color if not (root.data['Pressure Internal']['lim_min'] < self.val < root.data['Pressure Internal']['lim_max']) else root.text_color
        halign: 'center'
        markup: True
        val: 0

    Label:
        id: Pressure Internalvalmax
        pos_hint: {'right': 0.6, 'top': 0.5} #relative sizes 0-1
        size_hint: 0.2, 0.2
        text: '%.0f [size=15sp]mBar[/size]' % (self.val)
        font_size: '30sp'
        color: root.warning_color if not (root.data['Pressure Internal']['lim_min'] < self.val < root.data['Pressure Internal']['lim_max']) else root.text_color
        markup: True
        val: 0

    Label:
        id: Pressure Internalvalmin
        pos_hint: {'right': 0.6, 'top': 0.65} #relative sizes 0-1
        size_hint: 0.2, 0.2
        text: '%.0f [size=15sp]mBar[/size]' % (self.val)
        font_size: '30sp'
        color: root.warning_color if not (root.data['Pressure Internal']['lim_min'] < self.val < root.data['Pressure Internal']['lim_max']) else root.text_color
        markup: True
        val: 0

    Label:
        id: Humidity
        pos_hint: {'right': 0.8, 'top': 0.9} #relative sizes 0-1
        size_hint: 0.2, 0.1
        text: 'Humidity:'
        font_size: '15sp'
        color: root.text_color
        valign: 'bottom'
        markup: True

    Label:
        id: Humidityvallast
        pos_hint: {'right': 0.8, 'top': 0.85} #relative sizes 0-1
        size_hint: 0.2, 0.2
        text: '[b]%.0f %%[/b]' % self.val
        font_size: '30sp'
        color: root.warning_color if not (root.data['Humidity']['lim_min'] < self.val < root.data['Humidity']['lim_max']) else root.text_color
        halign: 'center'
        valign: 'top'
        markup: True
        val: 0

    Label:
        id: Humidityvalmax
        pos_hint: {'right': 0.8, 'top': 0.5} #relative sizes 0-1
        size_hint: 0.2, 0.2
        text: '%.0f %%' % self.val
        font_size: '30sp'
        color: root.warning_color if not (root.data['Humidity']['lim_min'] < self.val < root.data['Humidity']['lim_max']) else root.text_color
        val: 0

    Label:
        id: Humidityvalmin
        pos_hint: {'right': 0.8, 'top': 0.65} #relative sizes 0-1
        size_hint: 0.2, 0.2
        text: '%.0f %%' % self.val
        font_size: '30sp'
        color: root.warning_color if not (root.data['Humidity']['lim_min'] < self.val < root.data['Humidity']['lim_max']) else root.text_color
        val: 0

    Label:
        id: lights
        pos_hint: {'right': 1, 'top': 0.9} #relative sizes 0-1
        size_hint: 0.2, 0.1
        text: 'Lights:'
        font_size: '15sp'
        color: root.text_color
        valign: 'bottom'
        halign: 'center'

    setLab:
        pos_hint: {'right': 0.9, 'top': 0.82}    # relative sizes 0-1
        text: 'ON:'
        color: root.text_color


    TIn:
        id: lightson
        pos_hint: {'right': 0.9, 'top': 0.77} #relative sizes 0-1
        text: str(root.lights['on'])
        # input_filter: 'float'
        size_hint: 0.1, 0.07
        foreground_color: root.text_color
        on_focus:
            self.focusaction(root.setonofftime, self.text, 'on')

    setLab:
        pos_hint: {'right': 1, 'top': 0.82}    # relative sizes 0-1
        text: 'OFF:'
        color: root.text_color

    TIn:
        id: lightsoff
        pos_hint: {'right': 1, 'top': 0.77} #relative sizes 0-1
        text: str(root.lights['off'])
        size_hint: 0.1, 0.07
        foreground_color: root.text_color
        on_focus:
            self.focusaction(root.setonofftime, self.text, 'off')

    # BRIGHTNESS
    setLab:
        pos_hint: {'right': 0.95, 'top': 0.68}    # relative sizes 0-1
        text: 'Brightness:'
        color: root.text_color

    setLab:
        pos_hint: {'right': 0.9, 'top': 0.6}    # relative sizes 0-1
        text: 'MIN:'
        color: root.text_color

    setLab:
        pos_hint: {'right': 1, 'top': 0.6}    # relative sizes 0-1
        text: 'MAX:'
        color: root.text_color

    TIn:
        id: min_brightness
        input_filter: 'float'
        text: str(int(root.lights['brightness_cyc'] * 100))
        pos_hint: {'right': 0.9, 'top': 0.55} #relative sizes 0-1
        foreground_color: root.text_color
        on_focus:
            self.focusaction(root.setbrightness, self.text, 'min')


    TIn:
        id: max_brightness
        input_filter: 'float'
        pos_hint: {'right': 1, 'top': 0.55} #relative sizes 0-1
        text: str(int(root.lights['brightness_max'] * 100))
        foreground_color: root.text_color
        on_focus:
            self.focusaction(root.setbrightness, self.text, 'max')

    PlusButton:
        id: min_bright_plus
        pos_hint: {'right': 0.9, 'top': 0.45} #relative sizes 0-1
        on_release:
            root.setbrightness((root.lights['brightness_cyc'] * 100) + 5, 'min')

    MinusButton:
        id: min_bright_min
        pos_hint: {'right': 0.9, 'top': 0.35} #relative sizes 0-1
        on_release:
            root.setbrightness((root.lights['brightness_cyc'] * 100) - 5, 'min')

    PlusButton:
        id: max_bright_plus
        pos_hint: {'right': 1, 'top': 0.45} #relative sizes 0-1
        on_release:
            root.setbrightness((root.lights['brightness_max'] * 100) + 5, 'max')

    MinusButton:
        id: max_bright_min
        pos_hint: {'right': 1, 'top': 0.35} #relative sizes 0-1
        on_release:
            root.setbrightness((root.lights['brightness_max'] * 100) - 5, 'max')

    StdButton:
        # LIGHTS ON OFF
        id: lightsbut
        pos_hint: {'x': 0.8, 'top': 0.2} #relative sizes 0-1
        size_hint:  (0.2, 0.2)
        color: root.text_color if root.light_status else MO
        background_color: root.menu_color if root.light_status else GREY
        text: '[b]LIGHTS %s[/b]' %('OFF' if root.light_status else 'ON')
        on_release: root.lightsonoff(mode='button')
        font_size: '25sp'

    StdButton:
        id: activatebut
        pos_hint: {'x': 0, 'top': 0.1} #relative sizes 0-1
        size_hint:  (0.2, 0.1)
        color: WHITE if app.IO.running else MO
        background_color: GREEN_OK if app.IO.running else GREY
        text: 'LOGGING' if app.IO.running else 'START\\nLOGGING'
        on_release: root.start()


    StdButton:
        text: 'Calibrate\\nPressure'
        pos_hint: {'x': 0.2 , 'top': 0.1}
        size_hint:  (0.2, 0.1)
        on_release:
            root.calibrate_pressure()


    Set:
        # Health screen
        STT:
            id: health
            size: root.size[0], 0.8 * root.size[1]
            pos: root.pos[0],  root.pos[1] + 1.1 * root.size[1]
            canvas.before:
                Color:
                    rgba: 0, 0, 0, 0.7
                Rectangle:
                    pos: self.pos
                    size: self.size


            TIn:
                id: no_dead
                pos_hint: {'x': 0, 'top': 0.6}
                size_hint: 0.1, 0.1
                hint_text: str(0)


            StdButton:
                id: check_dead
                activated: False
                pos_hint: {'x': 0, 'top': 0.5}
                text: 'Check'
                color: (WHITE if self.activated else MO)
                background_color: (GREEN_OK if self.activated else GREY)
                on_release:
                    self.activated = not self.activated

            setLab:
                pos_hint: {'x': 0, 'top': 0.7}
                text: 'Dead\\nAnimals:'

            TIn:
                id: no_inj
                pos_hint: {'x': 0.1, 'top': 0.6}
                size_hint: 0.1, 0.1
                hint_text: str(0)

            StdButton:
                id: check_inj
                activated: False
                pos_hint: {'x': 0.1, 'top': 0.5}
                text: 'Check'
                color: (WHITE if self.activated else MO)
                background_color: (GREEN_OK if self.activated else GREY)
                on_release:
                    self.activated = not self.activated


            setLab:
                pos_hint: {'x': 0.1, 'top': 0.7}
                text: 'Injured\\nAnimals:'

            TIn:
                id: no_sick
                pos_hint: {'x': 0.2, 'top': 0.6}
                size_hint: 0.1, 0.1
                hint_text: str(0)

            StdButton:
                id: check_sick
                activated: False
                pos_hint: {'x': 0.2, 'top': 0.5}
                text: 'Check'
                color: (WHITE if self.activated else MO)
                background_color: (GREEN_OK if self.activated else GREY)
                on_release:
                    self.activated = not self.activated

            setLab:
                pos_hint: {'x': 0.2, 'top': 0.7}
                text: 'Sick\\nAnimals:'

            setLab:
                pos_hint: {'x': 0.3, 'top': 0.7}
                text: 'Food:'

            StdButton:
                id: check_food
                activated: False
                pos_hint: {'x': 0.3, 'top': 0.5}
                text: 'Check'
                color: (WHITE if self.activated else MO)
                background_color: (GREEN_OK if self.activated else GREY)
                on_release:
                    self.activated = not self.activated

            setLab:
                pos_hint: {'x': 0.4, 'top': 0.7}
                text: 'Water:'

            StdButton:
                id: check_water
                activated: False
                pos_hint: {'x': 0.4, 'top': 0.5}
                text: 'Check'
                color: (WHITE if self.activated else MO)
                background_color: (GREEN_OK if self.activated else GREY)
                on_release:
                    self.activated = not self.activated

            setLab:
                pos_hint: {'x': 0.5, 'top': 0.7}
                text: 'Change\\nCages/Bottles:'

            StdButton:
                id: check_water
                activated: False
                pos_hint: {'x': 0.5, 'top': 0.5}
                text: 'Check'
                color: (WHITE if self.activated else MO)
                background_color: (GREEN_OK if self.activated else GREY)
                on_release:
                    self.activated = not self.activated


            StdButton:
                id: complete
                activated: False
                pos_hint: {'x': 0.6, 'top': 0.5}
                size_hint: 0.2, 0.1
                text: 'COMPLETE'
                color: (WHITE if self.activated else MO)
                background_color: (GREEN_OK if self.activated else GREY)
                on_release:
                    self.activated = not self.activated

            setLab:
                pos_hint: {'x': 0.8, 'top': 0.3}
                text: 'Last Check:'

            setLab:
                text: '%d d. %d h. %d m. ago\\nby: [b]Dmitri[/b]' % (0, 5, 20)
                pos_hint: {'x': 0.8, 'top': 0.2}
                markup: True

"""

class RoomScreen(Scr):
    """
    Screen with room controls (controls lights, records pressure, humidity,
    temp)
    """
    LIGHT_TIMEOUT = 1800                    # timeout to turn lights of in sec
    save_pars = ('pressure_offset',)
    light_status = BooleanProperty(False)   # light turned on with button: True
    text_color = ListProperty(WHITE)        # text color (changes with lights)
    menu_color = ListProperty(MO_BGR)       # menu color (changes with lights)
    pressure_offset = NumericProperty(0)      # difference interal and ext press
    warning_color = YELLOW

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(kv_str)
        self.day = True                                      # is it day or not
        self.daynightswitch = 0                      # time.time of last switch
        self.lastadjustment = 0                  # last time cycle was adjusted
        self.lights = {'on': '01:00',
                       'off': '13:00',
                       'brightness_max': 1,     # brightness for all leds (0-1)
                       'brightness_cyc': 0.6,     # brightness during day cycle
                       'night': [0, 0, 0],            # RGB CODE FOR DARK CYCLE
                       'day': [0xFF, 0xFF, 0xAF],    # RGB CODE FOR LIGHT CYCLE
                       'red_color': [0xFF, 0, 0],      # RGB CODE FOR RED LIGHT
                       'cycle': [0, 0, 0],           # RGB CODE FOR cycle COLOR
                       'current_color': (0, 0, 0),       # current color in rgb
                       }

        # function for dimming (w = period, t1 is current time,
        # 2 * w --> only want to use half of the sinusoid
        self.c_f = lambda w, t: abs(np.sin(((2 * np.pi) / (2 * w)) * (t)))

        # convert string of time to time
        # self.gettime()
        self.data = {'Humidity': {'all': None, 'last': None,
                              'min': None, 'max': None,
                              'lim_min': 30, 'lim_max': 70,
                              'f': None, 'unit': ''},
                     'Pressure Internal': {'all': None, 'last': None,
                               'min': None, 'max': None,
                               'lim_min': 0, 'lim_max': 2000,
                               'f': None, 'unit': 'mBar'},
                    'Pressure External': {'all': None, 'last': None,
                               'min': None, 'max': None,
                               'lim_min': 0, 'lim_max': 2000,
                               'f': None, 'unit': 'mBar'},
                     'Temperature External': {'all': None, 'last': None,
                              'min': None, 'max': None,
                              'lim_min': 20, 'lim_max': 26.11,
                              'f': None, 'unit': 'c'}}
        
        if self.app.ROOM_CONTROL:
            self.event = Clock.schedule_once(self.main, 1)
            self.light_off_event = Clock.schedule_once(
                                        lambda *_x: self.lightsonoff(mode="off"), 
                                        self.LIGHT_TIMEOUT)
            self.light_off_event.cancel()

    def main(self, *args):
        switchnow = False   # bool to immediately switch on/off light

        # check time
        self.gettime()

        # test if day or night:
        day = self.daydetect(self.lights['on_time'],
                             self.lights['off_time'],
                             self.time)
        t = time.time()

        if day is None:
            # this happens when ontime == offtime (48h cycle)
            if t - self.daynightswitch >= 86400:
                # switch after 24h (=86400 sec)
                self.daynightswitch = t
                self.day = not self.day
                switchnow = True
        else:
            # set on or off depending on time of day and on/off time
            if day != self.day:
                switchnow = True     # indicate that lights have to be switched
            self.daynightswitch = t
            self.day = day

        if t - self.lastadjustment > 1 or switchnow:
            # changing the value in the if statement increases the time between
            # each adjustment of the lights
            self.lastadjustment = t
            self.clockcycle()

        if (self.app.IO.running
            and self.app.root.ids.scrman.current_screen.name == self.name):       # only get values if screen is in focus
                self.get_sens_values()

        return self.event()

    def get_sens_values(self):
        """
        Get sensor values for a given time interval, calculate the minimum, maximum, 
        and last values for each parameter,
        and check for alerts.

        The function retrieves data for the parameters defined in `self.data.keys()` 
        from the app's IO buffer and calculates 
        the minimum, maximum, and last values for each parameter. If a parameter is 
        outside of its limit, the parameter 
        name is added to the `alert` list. If "Pressure Internal" and 
        "Pressure External" parameters are present, the 
        function also calculates the difference between the internal and 
        external pressures and sets the text of 
        `self.ids['press_diff']` accordingly. If either "Pressure Internal" 
        or "Pressure External" is not present, the 
        text of `self.ids['press_diff']` is set to indicate that the respective 
        pressure sensor is not connected. If the 
        `alert` list is not empty, the `send_alert` function is called with the 
        `alert` list as an argument.
        """

        cycle = 24                       # time back in hours to check min/max
        alert = []                          # list with pars to send alert for

        # TODO fix -> get vals in app.IO

        seconds_back = cycle * 3600

        pars = set(self.data.keys()).intersection(self.app.IO.buffer['data'].dtype.fields)
        if "Pressure External" in self.app.IO.buffer['data'].dtype.fields: 
            pars.add("Pressure External")
        data = self.app.IO.get_time_back_data(seconds_back, [*pars])

        # define data windows:
        for key in pars:
            if data is not None:
                self.data[key]['last'] = data[key][-1]
                self.data[key]['min'], self.data[key]['max'] = np.nanmin(data[key]), np.nanmax(data[key])

                # get min, max and current value for pars in par_list:
                unit = self.data[key]['unit']
                
                # get and convert last, min and max values
                if key != "Pressure External":
                    for subp in ('last', 'min', 'max'):
                        self.ids[key + 'val' + subp].val = float(self.data[key][subp])         # float needed because kivy cannot handle numpy floats
        
                if not (self.data[key]['lim_min'] <= self.data[key]['last']
                        <= self.data[key]['lim_max']):
                    alert.append(key)

                # check positive or negative room pressure
                if (key == 'Pressure Internal'  
                    and 'Pressure External' in pars
                    ):
                    # int. pressure:
                    diff = self.data['Pressure Internal']['last'] - self.pressure_offset
                    # ext. pressure:
                    ext_press = data['Pressure External'][-1]
                    diff -= ext_press

                    if diff == diff:     # if not NaN
                        if diff >= 0:
                            self.ids['press_diff'].text = '[b]POSITIVE[/b]'
                            alert.append(key)
                        else:
                            self.ids['press_diff'].text = '[b]NEGATIVE[/b]'

        if 'Pressure Internal' not in pars:
            self.ids['press_diff'].text = 'Internal Pressure\nSensor N.C.'

        if 'Pressure External' not in pars:
            self.ids['press_diff'].text = 'External Pressure\nSensor N.C.'

        if alert:
            self.send_alert(alert)

    def send_alert(self, pars):
        # TODO: send message here
        ...

    def calibrate_pressure(self):
        pars = self.app.IO.rec_data.keys()
        self.pressure_offset = (self.app.IO.rec_data['Pressure Internal'][-1]
                                if 'Pressure Internal' in pars else None)
        if self.pressure_offset is not None:
            self.pressure_offset -= (self.app.IO.rec_data['Pressure External'][-1]
                                     if 'Pressure External' in pars else 0)

    def clockcycle(self, *args):
        '''
        this function determines if it is night or day and sets lights on or off
        '''
        if self.day:
            cycl = 1
            phase = 'day'
        else:
            cycl = 0
            phase = 'night'
        self.lights['cycle'] = [int(i * cycl)
                                for i in self.lights[phase]]
        self.setlight()

    def setlight(self, rgb=[]):
        if not rgb:
            if self.light_status:
                if self.day:
                    rgb = self.lights['day']
                else:
                    rgb = self.lights['red_color']
            else:
                rgb = self.lights['cycle']

        if self.light_status:
            brightness = self.lights['brightness_max']
        else:
            brightness = self.lights['brightness_cyc']

        # adjust rgb for brightness
        rgb = [int(x * brightness) for x in rgb]

        # set menu colors
        self.change_menu_color()

        # set lights
        self.lights['current_color'] = rgb
        self.app.IO.chip_command('Ambient Light', 'fill', color=rgb)

    def start(self):
        if not self.app.IO.running:
            self.app.IO.start_recording()
        else:
            self.app.IO.stop_recording()

    def setonofftime(self, t, onoff):
        try:
            time.strptime(t, '%H:%M')  # test if input has right format
            self.lights[onoff] = t
        except ValueError:
            return

    def setbrightness(self, brightness, minmax):
        try:
            brightness = float(brightness)

        except ValueError:
            return

        if brightness > 100:
            brightness = 100
        elif brightness < 0:
            brightness = 0

        if minmax == 'max':
            # set brightness when lights turned on by hand
            self.ids.max_brightness.text = str(int(brightness))
            self.lights['brightness_max'] = brightness / 100
            self.setlight()

        elif minmax == 'min':
            # set brightness during autmotic day night cycle
            self.ids.min_brightness.text = str(int(brightness))
            self.lights['brightness_cyc'] = brightness / 100
            self.setlight()

    def lightsonoff(self, *args, mode='off'):
        '''
        This function turn the daylight full on
        or the red light
        '''
        self.light_off_event.cancel()
        if mode == 'off':
            # always turn lights off if auto launched
            self.light_status = False

        else:
            # switch light status when method is triggered by button
            # (mode = 'button')
            self.light_status = not self.light_status

        _status = (('Night Cycle', 'Day Cycle'), 
                   ('Red On', 'Full On'))[self.light_status][self.day]
                   
        self.app.IO.add_note(f'Lights: {_status}') 

        # turn lights to max during day cycle
        self.setlight()

        # disable lights after 30min
        if mode == 'button' and self.light_status:
            return self.light_off_event()

    def change_menu_color(self, mode=None):
        if self.day:
            self.text_color = WHITE if self.light_status else WHITE
            self.menu_color = MO_BGR
        else:
            self.text_color = ((1, 0, 0, 0.8) if self.light_status
                               else (1, 0, 0, 0.4))
            self.menu_color = ((1, 0, 0, 0.8) if self.light_status
                               else (1, 0, 0, 0.4))
        if mode == 'showoff':
            # TODO DISCO MODE
            pass

    # MISC FUNCTIONS:
    def gettime(self):
        self.time = self.app.root.time.time()            # time in datetime

        str2time = self.app.root.str2time
        self.lights['on_time'] = str2time(self.lights['on'], form="%H:%M")
        self.lights['off_time'] = str2time(self.lights['off'], form="%H:%M")

    @staticmethod
    def daydetect(sunrise, sunset, currtime):
        '''
        this function classifies if it is day (True) or night(False) based on
        current time
        and returns None if sunrise and sunset are the same
        '''
        if (currtime >= sunrise > sunset
            or sunrise > sunset >= currtime
                or sunset > currtime >= sunrise):
            # day
            return True

        elif (currtime >= sunset > sunrise
              or sunset > sunrise >= currtime
              or sunrise > currtime >= sunset):
            # night
            return False



# TODO: use datetime to calc timedifferences in stead of time.time