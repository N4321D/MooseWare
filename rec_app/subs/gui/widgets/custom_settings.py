from logging import disable
from kivy import kivy_configure
from kivy.uix.gridlayout import GridLayout
from kivy.uix.settings import (SettingNumeric, SettingsWithSidebar, 
                               SettingString, SettingOptions, SettingSpacer, 
                               SettingsWithNoMenu, SettingItem)
from kivy.properties import StringProperty, ListProperty, DictProperty, BooleanProperty, NumericProperty, ObjectProperty
from kivy.lang.builder import Builder
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.widget import Widget

from kivy.clock import Clock

from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.app import App

from kivy.uix.screenmanager import Screen

from bisect import bisect

from datetime import timedelta, time as dt_time
import re
import ast
from ast import literal_eval

from subs.gui.misc.Stimulation import StimPanel

from cryptography.fernet import Fernet

KEY = b'il2MIYLxZx9WW1wAuFCVUqxqwAitiw9h6oINjqeCxMg='  # encryption keys for wifi passwords
fernet_enc = Fernet(KEY)

Builder.load_string(
"""
#: import MO subs.gui.vars.MO
#: import BUT_BGR subs.gui.vars.BUT_BGR
#: import MO_BGR subs.gui.vars.MO_BGR
#: import WHITE subs.gui.vars.WHITE
#: import PLUS_GREEN subs.gui.vars.PLUS_GREEN
#: import MINUS_RED subs.gui.vars.MINUS_RED

# change menu items layout
<SettingSidebarLabel>:
    # font_size: '15sp'
    canvas.before:
        Color:
            rgba: (*[i/2 for i in MO[:3]], int(self.selected))
        Rectangle:
            pos: self.pos
            size: self.size

# overwrite default switch
<Switch>:
    canvas:
        Color:
            rgba: MO if self.active else BUT_BGR
        Rectangle:
            source: './Icons/switch-background{}.png'.format('_disabled' if self.disabled else '')
            size: sp(83), sp(32)
            pos: int(self.center_x - sp(41)), int(self.center_y - sp(16))

# overwrite settingsitem
<SettingItem>:
    live_widget: True
    disabled: app.IO.running if self.live_widget is False else False  # disable chip during recording if not defined as live widget in json
    canvas:
        Color:
            rgba:  (*[i/2 for i in MO[:3]], int(self.selected_alpha) * 0.9)
        Rectangle:
            pos: self.x, self.y + 1
            size: self.size
    
    # color when disabled:
    canvas.after:
        Color:
            rgba: (0, 0, 0, self.disabled * 0.6)   
        Rectangle:
            pos: self.x, self.y + 1
            size: self.size

<Popup>:
    title_color: MO
    separator_color: MO

<SettingPassword>:
    PasswordLabel:
        text: "*" * len(root.value) #(lambda x: '*'*x)(len(root.value)) if root.value else ''
        #pos: root.pos
        #font_size: '15sp'

<SettingsToggle>:
    color: MO if self.state == "normal" else WHITE
    background_color: BUT_BGR if self.state == "normal" else MO_BGR
    background_down: 'atlas://data/images/defaulttheme/button' # default background

<SettingsButton>:
    color: WHITE
    background_color: MO_BGR

<StartStimButton@SettingsButton>:
    disabled: False if app.IO.running else True

<SettingInWithPlusMinus>:
    Button:
        id: min_button
        text: '[b]-[/b]'
        on_release: root.decrease()
        color: WHITE
        background_color: MINUS_RED
        markup: True
    
    Button:
        id: plus_button
        text: '[b]+[/b]'
        on_release: root.increase()
        color: WHITE
        background_color: PLUS_GREEN
        markup: True

"""
)

class SettingsToggle(ToggleButton):
    pass

class SettingsButton(Button):
    pass

class StartStimButton(SettingsButton):
    pass

def val_type_loader(inp):
    """
    use as val_type for config parser if using dict or list
    or other types which cannot be directly converted back
    from string
    """
    if isinstance(inp, str):
        # load from config
        return ast.literal_eval(inp)
    else:
        # save to config
        return inp

def timestr_2_timedelta(value, ):
    """
    convert input to readable 
    timedelta, format
    """
    if not value:
        return
    
    if isinstance(value, str):
        if "days," in value:
            days, value = value.split(" days, ")
            value = f"{days}:{value}"
        
        value = timedelta(**{key: float(val)
                            for val, key in zip(value.split(":")[::-1],
                                                ("seconds", "minutes", "hours", "days"))
                            })
        
    return value


def timestr_2_time(value, ):
    """
    convert input to readable 
    datetime.time format
    """
    if not value:
        return
    
    if isinstance(value, str):
        value = dt_time(**{key: int(val)
                for val, key in zip(value.split(":")[::-1],
                                    ("second", "minute", "hour"))
                })
    return value


class SettingPassword(SettingString):
    pass
'''
    # TODO: FINISH THIS CLASS
    def _create_popup(self, instance):
        super(SettingPassword, self)._create_popup(instance)
        self.textinput.password = True

    def _validate(self, instance):
        self._dismiss()
        value = self.textinput.text.replace(" ", "")  # remove spaces
        # self.value = value + "Encrypted" #Change this to your encryption
        self.value = fernet_enc.encrypt(value)
        print(self.value) #Just for debugging

    def add_widget(self, widget, *largs):
        if self.content is None:
            super(SettingString, self).add_widget(widget, *largs)

        if isinstance(widget, PasswordLabel):
            return self.content.add_widget(widget, *largs)
'''

class SettingTimeDelta(SettingString):
    """
    special class of Settings Numeric which returns and handles 
    datetime.timedelta objects
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time_in = timestr_2_timedelta
        self.bind(textinput=self.modify_textin)

    def modify_textin(self, *args):
        if self.textinput is not None:
            self.textinput.input_filter = lambda inp, * \
                _: re.sub(r"[^0-9:.]", "", inp)

    def _validate(self, instance):
        self._dismiss()
        value = self.textinput.text.replace(" ", "")
        value = ":".join([i for i in value.split(":") if i]
                         )  # remove extra columns
        value = self.time_in(value)

        if value is not None:
            self.value = str(value)

class SettingTime(SettingString):
    """
    special class of Settings Numeric which returns and handles 
    datetime.time objects
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time_in = timestr_2_time
        self.bind(textinput=self.modify_textin)

    def modify_textin(self, *args):
        if self.textinput is not None:
            self.textinput.input_filter = \
                lambda inp, *_: re.sub(r"[^0-9:.]", "", inp)

    def _validate(self, instance):
        self._dismiss()
        value = self.textinput.text.replace(" ", "")
        value = ":".join([i for i in value.split(":") if i])  # remove extra columns
        value = self.time_in(value)

        if value is not None:
            self.value = str(value)

class SettingInWithPlusMinus(SettingNumeric):
    """
    Modified settings class for numeric input which has a plus/
    minus button. Increase and decrease can be defined with steps or
    with 

    limits: (min, max)
        min:    limit minimum value to min. no limit if None
        max: limit maximum value to max. no limit if None
    
    steps: list with nested lists containing 
            [lower range, upper range, step]
        lower: lower part of range for which to use step
        upper: upper limit of range for which to use step
        step: step to use when value is within range
    """
    def __init__(self, steps={}, limits=(None, None), 
                  **kwargs):
        self.steps = steps
        self.limits = limits
        self.bind(disabled=self.do_disb)
        super().__init__(**kwargs)
    
    def do_disb(self, *args):
        print(*args)
           
    def on_panel(self, instance, value):
        super().on_panel(instance, value)
        self.funbind('on_release', self._create_popup)   # unbind creating popup when clicking on widget
        
    def on_touch_up(self, touch):
        if not (self.ids.min_button.collide_point(*touch.pos)
            or self.ids.plus_button.collide_point(*touch.pos)):
            self.on_release = lambda *_: self._create_popup(self)
        
        else:
            self.on_release = lambda *_: None

        return super().on_touch_up(touch)
    
    def increase(self, *args):
        self.plus_min("plus")

    def decrease(self, *args):
        self.plus_min("min")

    def plus_min(self, mode, step=1):
        _type = float if "." in self.value else int
        _val = _type(self.value)
        _lower, _upper = self.limits

        # find step size
        if self.steps:
            for _low, _high, step in self.steps:
                if ((_low <= _val < _high and mode == 'plus') or
                        (_low < _val <= _high and mode == 'min')):
                    step = step
                    break

        if "plus" in mode:
            _val = _val + step - (_val%step) # round to nearst multiple of step
        else:
            _val = _val - (_val%step or step) # round to nearst multiple of step
        
        if _lower is not None and _val < _lower:
            _val = _lower
        if _upper is not None and _val > _upper:
            _val = _upper

        _val = _type(_val)      # make sure type stays the same
        self.value = str(_val)
    
class SettingStim(SettingItem):
    def __init__(self, live_widget=None, **kwargs):
        self.stim_panel = None
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.config = self.panel.config
        self.buttons = {
            'create': SettingsButton(text='Create\nStim', 
                                     on_release=self.create_stim),
            'startstop': StartStimButton(text='Start\nStim', 
                                        on_release=self.start_stop_stim,
                                        ),
            'reset': SettingsButton(text='Reset\nStim', 
                                    on_release=self.reset_stim),

        }

        [self.add_widget(b) for b in self.buttons.values()]
        Clock.schedule_once(self.add_chip, 0)

    def add_chip(self, *args):
        self.chip = self.panel.parent.chip
        self.stim_control = self.chip.stim_control[self.key]
        try:
            saved_val = literal_eval(self.value)
            self.stim_control.stim_pars.update(saved_val)  # loaded saved values
        except (ValueError, TypeError):
            pass
        self.stim_control.bind(run=self.change_start_stop_button)
        self.stim_control.bind(stim_pars=lambda *_:self.on_value(None, 
            self.stim_control.stim_pars)) #  save stimpars in config
    
        self.current_screen = self.get_current_screen()

    def change_start_stop_button(self, *args):
        self.buttons['startstop'].text = ("Stop\nStim" if self.stim_control.run 
                                          else "Start\nStim")

    def create_stim(self, button):
        if self.stim_panel is None:
            self.stim_panel = self.stim_control.get_panel()
        # self.get_parent_window()
        self.get_current_screen().add_widget(self.stim_panel)

    def start_stop_stim(self, button):
        if self.stim_control.run:
            self.stim_control.stop_stim()
        else:
            self.stim_control.start_stim()
    
    def reset_stim(self, button):
        self.stim_control.reset_stim()

    def on_value(self, instance, value):
        # do stuff here
        super().on_value(instance, value)        
    
    def get_current_screen(self, *args):
        """
        Returns the current screen instance for this widget.
        """
        for screen in self.walk_reverse():
            if isinstance(screen, Screen):
                return screen

class MySettingsWithNoMenu(SettingsWithNoMenu):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # register new class to settings
        self.register_type("timedelta", SettingTimeDelta)
        self.register_type("time", SettingTime)
        self.register_type("options", SettingOptions_Scrollview)
        self.register_type("plusminin", SettingInWithPlusMinus)
        self.register_type("stim", SettingStim)

class SettingsWithSidebar(SettingsWithSidebar):
    _type_list = {bool: "bool",
                  float: "numeric",
                  int: "numeric",
                  str: "string",
                  list: "options",
                  timedelta: "timedelta",
                  }
    
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # register new class to settings
        self.register_type("timedelta", SettingTimeDelta)
        self.register_type("time", SettingTime)
        self.register_type("options", SettingOptions_Scrollview)
        self.register_type('password', SettingPassword)
        self.register_type("plusminin", SettingInWithPlusMinus)
        self.register_type("stim", SettingStim)

    
    def convert_type(self, var):
        """
        takes a var and returns the type for the widget
        returns string if type not in list
        """
        _type = self._type_list.get(type(var), "string")
        return _type

class SettingOptions_Scrollview(SettingOptions):
    '''
    Custom settings options with scroll view popup

    '''

    def _create_popup(self, instance):
        # create the popup
        popup_content = BoxLayout(orientation='vertical', spacing='5dp')
        window = ScrollView(size_hint=(1, 0.8),
                            scroll_type=['bars', 'content'],
                            )
        

        content = GridLayout(cols=1, spacing='5dp')
        window.add_widget(content)
        popup_content.add_widget(window)
      

        popup_width = min(0.95 * Window.width, 0.95 * Window.height)
        # add all the options
        content.add_widget(Widget(size_hint_y=None, height=1))
        uid = str(self.uid)
        for option in self.options:
            state = 'down' if option == self.value else 'normal'
            btn = SettingsToggle(text=option, state=state, group=uid,
                               size_hint_y=None, height='40sp')
            btn.bind(on_release=self._set_option)
            content.add_widget(btn)
            content.size_hint_y += 0.16
        # finally, add a cancel button to return on the previous panel
        popup_content.add_widget(SettingSpacer())
        btn = SettingsButton(text='Cancel', size_hint=(1, 0.2), height=dp(50))
        
       
        self.popup = popup = Popup(
            content=popup_content, title=self.title, size_hint=(None, None),
            size=(popup_width, '400sp'))
        popup.height = '300sp'# len(self.options) * dp(55) + dp(150)
        btn.bind(on_release=popup.dismiss)
        popup_content.add_widget(btn)
        # and open the popup !
        popup.open()

if __name__ == "__main__":
    from subs.gui.buttons.Server_Button import Server_Button
    from subs.gui.buttons.DropDownB import DropDownB    
    import json

    class MyApp(App):
        use_kivy_settings = False
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.settings_cls = SettingsWithSidebar
            print("Press f1 to open settings")

        def build(self):
            return Builder.load_string(
r"""
#:set STIM_PAR_HEIGHT 0.9  # height of stimpar buttons
#:set MO (1,1,1,1)

<DROPB@DropDownB>: # general DropDown, set types to change (types: ['1','2'])
    id: selplot
    pos_hint: {'x': 0.2, 'top': 0.8}
    text: 'Menu'
    size_hint: 0.1, 0.05
    halign: 'center'

<StdButton@Server_Button>:                                                             # settings for all buttons
    font_size: '15sp'
    size_hint: 0.1, 0.1  # relative size
    halign: 'center'
    valign: 'center'
    markup: True
    idName: None   # save id name in here for triggering later
    send_nw: False  # can be set to false to disable sending for specific buttons

<TIn>:
    size_hint: (.1, .07)
    text_size: self.size
    multiline: False
    foreground_color: 1,1,1,1
    background_color: 0.2,0.2,0.2,0.9
    font_size: '15sp'
    base_direction: 'rtl'
    halign: 'right'
    valign: 'middle'
    use_bubble: True

<setLab@Label>:
    # labels for stimulation and settings
    pos_hint: {'right': 0.8, 'top': 0.62} #relative sizes 0-1
    halign: 'right'
    size_hint: 0.1, 0.05
    text: 'LABEL'
    font_size: '15sp'
    color: (1,1,1,1)

Button:
    text: "Open settings"
    on_release: 
        app.open_settings()
"""
)

        def build_config(self, config):
            config.adddefaultsection("test")
            config.setdefault('test', "str", "test 1234")
            config.setdefault('test', "bool", False)
            config.setdefault('test', "num", 15.54)
            config.setdefault('test', "opts", "choice 0")
            config.setdefault('test', "timedelta", timedelta(days=2, 
                                                             hours=4, 
                                                             minutes=9, 
                                                             seconds=23, 
                                                             microseconds=42))
            config.setdefault('test', "time", dt_time(hour=1, 
                                                   minute=2, 
                                                   second=34, 
                                                   ))
            config.setdefault('test', "numplusmin", 25.8)
            config.setdefault('test', "stim", 25.8)


            return super().build_config(config)
        


        def build_settings(self, settings):
            panel=[
            {"title": "testpanel",
                "type": "title"
            },
            {"title": "String Setting",
                "type": "string",
                "desc": "String Setting Widget",
                "section": "test",
                "key": "str",
            },
            {"title": "Bool Setting",
                "type": "bool",
                "desc": "Bool Setting Widget",
                "section": "test",
                "key": "bool",
            },
            {"title": "Numeric Setting",
                "type": "numeric",
                "desc": "Numeric Setting Widget",
                "section": "test",
                "key": "num",
            },
            {"title": "Options Setting",
                "type": "options",
                "desc": "Options Setting Widget",
                "section": "test",
                "key": "opts",
                "options": [f"choice {i}" for i in range(10)]
            },
            {"title": "Time Delta Setting",
                "type": "timedelta",
                "desc": "Time Delta Setting Widget",
                "section": "test",
                "key": "timedelta",
            },
            {"title": "Time Setting",
                "type": "time",
                "desc": "Time Setting Widget",
                "section": "test",
                "key": "time",
            },
            {"title": "SettingInWithPlusMinus",
                "type": "plusminin",
                "desc": "Numeric Setting with plus minus buttons",
                "section": "test",
                "key": "numplusmin",
                "steps": [[0, 10, 1], [10, 20, 2], [20, 100, 10]],  # [low range, high range, step]
                "limits": [0, 65],   # [min, max]
            },
            {"title": "SettingStim",
                "type": "stim",
                "desc": "Stim settings button",
                "section": "test",
                "key": "stim",
            }
            
            ]
            settings.add_json_panel("Test", self.config, data=json.dumps(panel))

    app = MyApp()
    app.run()
