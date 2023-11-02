"""
widget with connected chips and chip status

TO make settings item in the chip settings panel "live" (means you can
change it during recording) add live_widget: True to the json settings panel
(created in the chip file)

TODO: do more stuff async
"""


from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.lang import Builder

from subs.gui.widgets.custom_settings import MySettingsWithNoMenu
from kivy.config import ConfigParser


from kivy.properties import BooleanProperty

from kivy.clock import Clock

from subs.gui.vars import SENSOR_COLORS, CW_BUT_BGR_EN,CW_BUT_BGR_DIS, CW_BUT_BGR_RES, CW_BUT_BGR_LOST

import json

from ast import literal_eval
import asyncio


kv_str = """
#: import SENSOR_COLORS subs.gui.vars.SENSOR_COLORS
#: import SENSOR_COLORS subs.gui.vars.CW_BUT_BGR_DIS
#: import SENSOR_COLORS subs.gui.vars.CW_BUT_BGR_EN
#: import SENSOR_COLORS subs.gui.vars.CW_BUT_BGR_RES



<ChipLabel>:
    halign: 'center'
    valign: "center"
    markup: True

<ChipPanel>:
    contains_live_widgets: False
    canvas.before:
        Color:
            rgba: .2, .2, .2, 1
        Line:
            width: 2
            rectangle: self.x, self.y, self.width, self.height

    size_hint: (0.7, 0.6)
    pos_hint: {"x": 0.15, "y":0.2}

"""

class ChipLabel(Button):
    """
    Button with chip status and chip controls
    """
    chip = None
    chip_name = ""
    chip_enabled = BooleanProperty(True)

    def __init__(self, chip, short_name, app, box, **kwargs):
        super().__init__(**kwargs)
        self.box=box
        self.app = app

        config = ConfigParser().get_configparser("app_config")

        if isinstance(chip, dict):
            self.chip_name = chip['name']
            self.text = short_name
            self.chip_enabled = chip['record']
            default_opts = chip.get(default_opts, {'recording': True})

        else:
            self.chip = chip
            self.chip_name = chip.name
            self.text = chip.short_name
            self.chip_enabled = chip.record
            default_opts = chip.return_default_options()
        
        self.bind(chip_enabled=self._enable_disable_chip)
        
        config.adddefaultsection(self.chip_name)
        config.setdefaults(self.chip_name, default_opts)

        self.settings = ChipPanel(self, config)
        
        for opt in config.options(self.chip_name):
            # restore last saved options
            val = config.get(self.chip_name, opt)
            self.settings.on_config_change(config, self.chip_name, opt, val)

    def _enable_disable_chip(self, *args):
        self.chip.record = bool(int(self.chip_enabled))

        # update plotpars
        Clock.schedule_once(lambda dt:
            asyncio.run_coroutine_threadsafe(
                self.app.IO.update_plot_pars(), 
                asyncio.get_event_loop()
                ),
            0)
    
    def on_release(self):
        self.open_panel()

    def open_panel(self, *args):
        self.on_release = self.close_panel
        self.box.parent.add_widget(self.settings)
    
    def close_panel(self, *args):
        self.on_release = self.open_panel
        self.box.parent.remove_widget(self.settings)

class ChipWidget(BoxLayout):
    """
    Panel containing all the chip items
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.chip_labels = {}
        self.app = App.get_running_app()
        
        Builder.load_string(kv_str)
        self.create_buttons()
        self.app.IO.bind(sensors=self.create_buttons)
        Clock.schedule_interval(
            self.change_color, 0.25)

    def create_buttons(self, *args):
        self.clear_widgets()
        self.chip_labels.clear()
        self.chip_labels = {name: ChipLabel(self.app.IO.sensors[name], name, self.app, self) 
                                            for name in self.app.IO.sensors}

        # add widgets sorted on chip name
        for i, c in enumerate(sorted(self.chip_labels, 
                                     key=lambda x: 0 if x == "CTRL" else 1)[::-1]):
            self.add_widget(self.chip_labels[c], index=i)
        
        # add empty buttons if low number of buttons
        min_buttons = 8
        if len(self.chip_labels) < min_buttons:
            [self.add_widget(Button(background_color=CW_BUT_BGR_EN)) 
             for i in range(min_buttons - len(self.chip_labels))]
        
        self.change_color()

    def change_color(self, *args):
        for chip in self.chip_labels:
            _live_widget = self.chip_labels[chip].settings.contains_live_widgets

            # status color
            status_color = self.chip_labels[chip].chip.status

            if status_color < -1:
                status_color = -1
            
            if self.chip_labels[chip].color != SENSOR_COLORS[status_color]:
                self.chip_labels[chip].color = SENSOR_COLORS[status_color]

            # set bg color
            if self.app.IO.running and not _live_widget:
                    bg_col =  CW_BUT_BGR_DIS
            else:
                bg_col = CW_BUT_BGR_EN
            
            # Resets
            _resets = self.chip_labels[chip].chip.resets
            if _resets and self.app.IO.running:
                bg_col = (*CW_BUT_BGR_RES[:3], 0.3 if not _live_widget else 0.6)
            
            try:
                if (status_color < 0 and self.app.IO.running 
                    and self.chip_labels[chip].chip.connected):
                    bg_col = (*CW_BUT_BGR_LOST[:3], 0.3 if not _live_widget else 0.6)
            
            except Exception as e:
                raise e

            if self.chip_labels[chip].background_color != bg_col:
                self.chip_labels[chip].background_color = bg_col

class ChipPanel(MySettingsWithNoMenu):
    """
    Settings panel for each chip
    """
    def __init__(self, parent_button, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_button = parent_button
        self.chip = self.parent_button.chip
        self.config = config
        Clock.schedule_once(self._create_self, 0)

    def _create_self(self, *args):
        json_list = self.chip.json_panel()

        # create live settings (items that can be changed during recording)
        for item in json_list:
            # if chip setting has no live widget = True in json assume it is not a live widget
            if item.setdefault('live_widget', False) is True:
                self.contains_live_widgets = True    # prevents changing color when recording when containing live widgets
            
            # create values if not exisiting
            default_val = None
            if "default_value" in item:
                default_val = item.pop('default_value')
            else:
                default_val = (getattr(self.parent_button.chip, item['key']) 
                if hasattr(self.parent_button.chip, item['key']) else 0)

            if not self.config.has_section(item['section']):
                self.config.add_section(item['section'])
                
            self.config.setdefault(item['section'], item['key'], default_val)

        self.add_json_panel(self.chip.name, self.config, 
                            data=json.dumps(json_list))
    
        self.interface.container.chip = self.chip    # make chip accessible to settings items
        self.update_chip_val()
    
    def update_chip_val(self, *args):
        # send values to chip
        [self.on_config_change(self.config, item['section'], item['key'], 
                            self.config.get(item['section'], item['key']))
                            for item in self.chip.json_panel()]
                
    def on_config_change(self, config, section, option, value):
        # convert string to number
        try:
            value = literal_eval(value)
        except (ValueError, SyntaxError):
            # Value is string
            pass

        # convert to bool specifically for booleans
        # TODO: NOTE: not needed? test especially for serial devices!
        # if option == "record":
        #     # value = bool(value)  
        #     self.parent_button.chip_enabled = value

        # send to chip
        self.chip.do_config(option, value)
    
    def on_touch_down(self, touch):
        """
        Close Panel when clicking outside of panel
        """
        if self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        else:
            # clicked outside widget
            self.parent_button.close_panel()

            

if __name__ == "__main__":
    pass
