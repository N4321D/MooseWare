"""
Screen Manager

NB: Kv String cannot contain \n -> must be \\n

"""


from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import StringProperty, BooleanProperty, ConfigParserProperty
from subs.gui.widgets.custom_settings import val_type_loader

from kivy.clock import Clock
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

from subs.gui.vars import *
from subs.gui.widgets.notes import Notes

# imports for builder do not delete
import subs.gui.screens.kv_other.imports_vars
import subs.gui.screens.kv_other.cust_buttons
import subs.gui.screens.kv_other.cust_widgets

# screens for builder do not delete!!!
from subs.gui.screens.rec import RecScreen
from subs.gui.screens.environment import EnvScreen
from subs.gui.screens.about import AboutScreen
from subs.gui.screens.splash import SplashScreen
from subs.gui.screens.sett_scr import SetScreen
from subs.gui.screens.help import HelpScreen
from subs.gui.screens.screensaver import ScreenSaver

from subs.gui.widgets.notes import Notes


from datetime import datetime


Builder.load_string(
"""
#:kivy 2.0.0
<RootLayout>:
    orientation: "vertical"

    FloatLayout:
        id: menubar
        size_hint: 1, 0.1
        # height: "48sp"
        # default screen
        MW:         # Top menu bar
    
        MENU:       # menu button to switch screens
            id: MENU
    
        MENULABEL:
            id: title
            pos_hint: {'x': 0.3, 'top': 1}
            size_hint: 0.4, 1
            text: "[ref=rec_name]{}[i]{}[/i][/ref]".format(app.setupname + " - " if app.IO.client else "", app.IO.recording_name)
            on_ref_press:
                # REC NAME POPUP
                app.popup.load_defaults()
                app.popup.buttons = {"Enter": {'do':scrman.get_screen('Record').change_rec_name}}
                app.popup.title = "Enter Recording Name"
                app.popup.pos_hint = {'top': 0.85}
                if not app.IO.running: app.popup.open()

        DROPB:
            id: client_select
            text: ""
            pos_hint: {'x': 0.15, 'top': 1}
            size_hint: (0.15, 1)
            disabled: False if self.types else True
            drop_but_size: '48sp'
            types: app.IO.client_ip_list
            on_text:
                app.IO.switch_client(self.text)
            Image:
                source: "./Icons/moose_network.png" 
                pos: self.parent.x + 0.05 * self.parent.size[0], self.parent.y + 0.05 * self.parent.size[1]
                size: [0.9 * i for i in self.parent.size]
                allow_stretch: False #True
                color: (1,1,1,0.8) if not client_select.text else (0,0,0,0)

        FEEDBACK:
            # feedback console
            id: feedback
            pos_hint: {'x': 0.7, 'top': .98}
            size_hint: 0.195, 1
            text: ""
            on_ref_press: 
                root.add_notes()
        
        TogBut:
            id: clock
            pos_hint: {'x': 0.9, 'top': 1}
            size_hint: (0.1, 1)
            font_size: '14sp'
            on_release: root.change_tz()
            group: 'time'
            state: "normal" if root.UTC is True else "down"
            markup: True


    # KV FILES ARE SORTED ON name, make sure this file is imported last!!
    ScreenManagement:
        id: scrman
        transition: NoTransition()					# DONT USE OTHER TRANSITION: ON RPI WILL CRASH (unless you increase vid mem?)        
        SplashScreen:
            name: 'Menu'
        SetScreen:
            name: 'Settings'
        RecScreen:
            name: 'Record'
        EnvScreen:
            name: 'Envr.'
        HelpScreen:
            name: 'Help'
        AboutScreen:
            name: 'About'
        ScreenSaver:
            name: 'scrsav'

"""
)


class ScreenManagement(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
    

class RootLayout(BoxLayout):
    """
    Root Widget
    This widget determines the main layout of the app
    it includes the menu bar 
    and the screen manager
    """
    TIME_FORMAT = "[i][size=12sp]%x[/size][/i]\n%X"
    UTC = ConfigParserProperty(False, 'menubar', "utc", "app_config", val_type=val_type_loader)
    name = "RootWidget"
    server_widgets = ("client_select", )
    time_str = StringProperty(datetime.now().strftime(TIME_FORMAT))
    time = datetime.now()
    clock_event = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.notes = Notes(self.app)
        Clock.schedule_once(self.__kv_init__, 0)
    
    def __kv_init__(self, dt):
        self.change_tz(1)
        self.del_server_wid()
        self.clock_event = Clock.schedule_interval(self.gettime, 1)

    
    def del_server_wid(self, *args):
        if not self.app.SERVER:
            for w in self.server_widgets:
                (self.ids.menubar
                 .remove_widget(self.app
                                .root.ids[w])
                 )

    def add_notes(self):
        # adds note to screen
        if self.notes.parent:
            # prevent widget from opening when open
            pass

        else:
            self.ids.scrman.current_screen.add_widget(self.notes)
    
    # MISC FUNCTIONS:
    def gettime(self, *_):
        if self.UTC:
            self.time = datetime.utcnow()
        else:
            self.time = datetime.now()        # current time
        
        self.time_str = self.time.strftime(self.TIME_FORMAT)
        self.ids['clock'].text = self.time_str
        
        self.clock_event.timeout = 1 - (self.time.microsecond/1e6)
    
    def str2time(self, t_str, form=TIME_FORMAT):
        return datetime.strptime(t_str, form).time()
    
    def change_tz(self, timeout=1, *_):
        self.UTC = not(self.ids['clock'].state == 'down')
        if self.UTC is True:
            txt = 'UTC'
        else:
            txt = 'local\ntime'
        self.ids['clock'].text = txt
        return Clock.schedule_once(lambda *x: setattr(self.ids['clock'], "text", 
                                               self.time_str), timeout)
