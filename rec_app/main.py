# -*- coding: utf-8 -*-
'''
Created on Tue Feb 5 23:32:39 2019
GUI For Recording
@author: Dmitri Yousef Yengej
'''

# IMPORTS
from platform import system, machine
from kivy.event import EventDispatcher

if system() == 'Linux' and machine() == 'armv7l':
    # RPI specific options:
    import os

    # enable starting via SSH
    os.system('export DISPLAY=":0.0"')

# setup Kivy
import kivy
from kivy.config import Config
# Test Kivy Version
kivy.require('2.0.0')

from subs.log import create_logger
logger = create_logger()
def log(message, level="info"):
    getattr(logger, level)(f"MAIN: {message}")  # change RECORDER SAVER IN CLASS NAME

# configure Kivy
Config.set('kivy', 'window_icon', 'Icons/M_App_Icon.png')  # Icon
Config.set('kivy', 'keyboard_mode',  'systemanddock')     # keyboard docked
Config.set('graphics', 'show_cursor', 1)

# if running on windows set window to pi res for testing
SERVER = False
sys_platform = system()
log(f"OS: {sys_platform} {machine()}", "info")

if machine() in {'armv7l', 'aarch64'} and sys_platform == 'Linux':
    # RASPBERRY PI SETTINGS
    log("Loading Raspberry Pi presets", "info")
    Config.set('graphics', 'fullscreen', 'auto')
    Config.set('graphics', 'show_cursor', 0)     # hide mouse
    Config.set('graphics', 'allow_screensaver', 1) 
    Config.set('kivy', 'exit_on_escape', 0)

else:
    # PC SETTINGS
    Config.set('graphics', 'fullscreen', 0)
    SERVER = True
    # for testing set same size as pi res:
    Config.set('graphics', 'height', 480)
    Config.set('graphics', 'width', 800)

    if sys_platform == 'Windows':       # windows stuff
        log("Loading Windows presets", "info")
    elif sys_platform == 'Darwin':   # OSX Stuff
        log("Loading OSX presets", "info")
    elif sys_platform == "Linux":   # linux server stuff
        log("Loading Linux presets", "info")
        # Config.set('graphics', 'multisamples', '0')   # kivy does not detect opengl2
        
log(f"{'SERVER' if SERVER else 'CLIENT'} MODE", "info")

# write kivy configs
Config.write()

# import subs
from subs.input_ouput import InputOutput, TESTING

from subs.verify import MACADDRESS, check_serial, Encryption  # import key verification

# Other Imports
import os
import asyncio

from datetime import datetime, timedelta

# KIVY Imports
from kivy.properties import (ListProperty, BooleanProperty, NumericProperty,
                             StringProperty, DictProperty,
                             BoundedNumericProperty, ConfigParserProperty)

from kivy.clock import Clock
from kivy.app import App
from kivy.uix.settings import SettingsPanel, SettingSpacer
from kivy.uix.label import Label

from subs.gui.widgets.custom_settings import (SettingsWithSidebar, 
    timestr_2_timedelta, val_type_loader,)
from subs.gui.misc.settings_panel import settings_panel


# Custom Widgets DO NOT REMOVE NEEDED FOR KV:
# TODO move to classes/ modules where used
from subs.gui.widgets.popup import MyPopup
from subs.gui.widgets.filemanager import FileManager
from subs.gui.widgets.wifi_manager import WifiWidget
from subs.gui.widgets.timezone_wid import TzWidget

# Screens DO NOT REMOVE NEEDED IN KV
from subs.gui.screens.root_layout import RootLayout

from subs.updater import Updater

# Other imports:
from subs.gui.misc.Stimulation import Stimulation
from subs.driver.button import LedButton
from subs.gui.widgets.messenger.kivy_messenger import Messenger                 # import sms alert system

# GLOBAL VARS & PARS
from subs.gui.vars import *
ADMIN = False

class RecVars(EventDispatcher):
    """
    Class which holds all the recording parameters and links them to the config files
    (rs.mv <-> app.config)
    """

    # TODO LINK PARS TO SAVER IN app.IO

    startrate = ConfigParserProperty(256, 'recording', "startrate", "app_config", val_type=int)
    data_length = ConfigParserProperty(3600, 'recording', "data_length", "app_config", val_type=int)                    # length of data in memory in sec.
    save_data = ConfigParserProperty(True, 'recording', "save_data", "app_config", val_type=val_type_loader)
    filename_prefix = ConfigParserProperty('data', 'recording', "filename_prefix", "app_config", val_type=str)
    max_file_size = ConfigParserProperty(100, 'recording', "max_file_size", "app_config", val_type=int)
    hdf_compression = ConfigParserProperty('gzip', 'recording', "hdf_compression", "app_config", val_type=str)
    hdf_compression_strenght = ConfigParserProperty(5, 'recording', "hdf_compression_strenght", "app_config", val_type=int)
    hdf_fletcher32 = ConfigParserProperty(True, 'recording', "hdf_fletcher32", "app_config", val_type=val_type_loader)
    hdf_shuffle = ConfigParserProperty(True, 'recording', "hdf_shuffle", "app_config", val_type=val_type_loader)
    ois_ma = ConfigParserProperty(5, 'recording', "ois_ma", "app_config", val_type=int)
    
    def __init__(self, val_dict, **kwargs):
        self.app = App.get_running_app()
        self.val_dict = val_dict

        self.bind(startrate=lambda inst, val: self.set_val('startrate', val))
        self.bind(save_data=lambda inst, val: self.set_val('save_data', val))
        self.bind(filename_prefix=lambda inst, val: self.set_val('filename_prefix', val))
        self.bind(max_file_size=lambda inst, val: self.set_val('max_file_size', val))
        self.bind(hdf_compression=lambda inst, val: self.set_val('hdf_compression', val))
        self.bind(hdf_compression_strenght=lambda inst, val: self.set_val('hdf_compression_strenght', val))
        self.bind(hdf_fletcher32=lambda inst, val: self.set_val('hdf_fletcher32', val))
        self.bind(hdf_shuffle=lambda inst, val: self.set_val('hdf_shuffle', val))
        self.bind(ois_ma=lambda inst, val: self.set_val('ois_ma', val))

        # FOR "LIVE" variables also add this:
        self.bind(ois_ma=self.change_ois)
    
    def change_ois(self, inst, val):
        """
        temporary solution for live vars:
        they need to be set in chip_d when not running and via RECORDER 
        when running. 
        TODO: find a better way to handle live vars (such as OIS mA)
        """
        if self.app:
            self.app.IO.chip_command('OIS', 'ledcontrol', 'pulse', (val, val))


    def set_val(self, key, val):
        """
        sets recording parameters in rs.mv
        """
        if key in self.val_dict and isinstance(self.val_dict[key], bool):
            # convert val to bool (is saved as 1 or 0 in settings)
            val = bool(val)

        # set value
        self.val_dict[key] = val
    

class guiApp(App):
    rec_vars = RecVars({}, section="recording")  # TODO: use share memory for recvar dict? 

    # Saved settings
    screensaver_timeout = ConfigParserProperty(timedelta(minutes=15), "main", 
                                               "screensaver_timeout", "app_config", 
                                               val_type=timestr_2_timedelta)
    setupname = ConfigParserProperty("", "main", "setupname", "app_config", 
                                     val_type=str)                              # name of the device
    log_level = ConfigParserProperty("WARNING", "other", "log_level", 
                                     "app_config", val_type=str)   

    led_status = NumericProperty(0)
    prev_screen = 'Home'                                                        # name of previous screen so screensaver can go back
    menu_text = ''                                                              # text for menu button

    # TODO Move gloabl vars below to settings
    SERVER = BooleanProperty(SERVER)                                            # If True, app acts as server
    ADMIN = ADMIN
    MACADDRESS = MACADDRESS
    ROOM_CONTROL = BooleanProperty(True)
    TESTING = TESTING

    Button = LedButton()

    use_kivy_settings = False   # disable kivy settings in options

    GPIO = None
    msg = None                                                                  # placeholder for messaging app TODO: to IO?

    def __init__(self, **kwargs):
        self.loop = asyncio.get_event_loop()
        super().__init__(**kwargs)
        # NOTE: set init stuff in build to run on start
        
    def build(self):
        self.logger = logger

        # define settings class
        self.settings_cls = SettingsWithSidebar

        self.updater = Updater(app_version=['app_version'])

        self.bind(log_level=lambda *_: self.logger.setLevel(self.log_level))
        
        self.msg = Messenger(self)

        # input output class
        self.IO = InputOutput()
        self.IO.bind(running=self.change_led_status)
        self.bind(led_status=self.change_led_status)
        Clock.schedule_once(self.change_led_status, 0)

        self.config.read("settings.ini")
        self.config.name = "app_config"

        # popup
        Popup.theme_color = MO
        self.popup = Popup()

        # file manager
        FileManager.path = "./data/"
        FileManager.rootpath = "./data/"
        def confirmation(cls, txt, action):
            cls.popup.load_defaults()
            cls.popup.title = txt
            cls.popup.buttons = {"Yes": {"do": action},
                                 "No": {"do": lambda *x: None}}
            cls.popup.pos_hint = {'top': 0.85}
            cls.popup.size_hint = (0.4, 0.3)
            cls.popup.open()
        FileManager.popup = self.popup
        FileManager.confirmation = confirmation
        FileManager.update_func = self.updater._update
        FileManager.UPDATE_NAME = self.updater.UPDATE_PACK_NAME

        # app variables
        self.title = f"{SETTINGS_VAR['Main']['title']}{SETTINGS_VAR['Main']['app_logo']:>25}"
        self.stim = Stimulation()

        self.scrsav_event = Clock.schedule_once(self.screen_saver,
                                                self.screensaver_timeout.total_seconds())

        self.bind(screensaver_timeout=lambda *_: setattr(self.scrsav_event, "timeout", 
                                                 self.screensaver_timeout.total_seconds()))

        # popup name popup if setup has no name    
        self.bind(setupname=self.setup_name_popup)
        Clock.schedule_once(self.setup_name_popup, 0)
        return RootLayout()

    def open_settings(self, *args):
        self.destroy_settings()                                                 # clear settings
        return super().open_settings(*args)

    def build_settings(self, settings):
        """
        create settings panel

        """   
        for section, json_panel in settings_panel.items():
            settings.add_json_panel(section, self.config, data=json_panel)
        
         # Modify button layout
        _button = settings.interface.menu.close_button
        _button.background_color = MO_BGR
        _button.color = WHITE

        self.settings = settings

        # add wifi and timezone widgets if not server
        if self.SERVER is False:
            pann = SettingsPanel(title="Network & Timezone")
            self.settings.interface.add_panel(pann, "Network & Timezone", 93)
            pann.add_widget(WifiWidget(size_hint_y=None, height='200sp'))
            pann.add_widget(SettingSpacer())
            pann.add_widget(TzWidget(size_hint_y=None, height='55sp'))

    def screen_saver(self, *args):
        # self.root.ids.scrman is the manager manager
        if self.root.ids.scrman.current != 'scrsav':
            self.prev_screen = self.root.ids.scrman.current
            self.root.ids.scrman.current = 'scrsav'
            self.root.ids.menubar.size_hint = (1, 0)

    def setup_name_popup(self, *args):
        if not self.setupname:
            self.popup.load_defaults()
            self.popup.title = 'Setup has no name,\nPlease enter setup name:'
            self.popup.buttons = {"Enter":
                                  {'do': lambda x: setattr(self,
                                                           "setupname", x)}}
            self.popup.pos_hint = {'top': 0.85}
            self.popup.size_hint = (0.4, 0.3)
            self.popup.open()
            
    def change_setup_name(self, name):
        self.setupname = name

    def reset_settings(self, *args):
        # this function resets all values to defaults (default.ini)
        # use button to set text on button
        print("TODO: main app reset settings")

    def stop(self, *args, **kwargs):
        log("Shutting Down... ", "info")
        self.IO.exit()
        return super().stop(*args, **kwargs)
        
    def change_led_status(self, *args, f=None, dc=None):
        if f is None and dc is None:
            options = ((100, 1), (100, 1), (1, 0.1), (5, 0.2), (10, 0.2))       # idle, running, stimulating
            self.Button.led_f_dc(*options[(self.led_status 
                                           or self.IO.running)])  
        else:
            self.Button.led_f(f) if f is not None else None
            self.Button.led_dc(dc) if dc is not None else None

    def start(self):
        self.loop.run_until_complete(app.base())
        self.loop.close()

# ==========================================
#           BUTTONS and WIDGETS
# ==========================================
class Popup(MyPopup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_defaults()

    def load_defaults(self):
        # set defaults
        self.size_hint = (0.4, 0.25)
        self.title_size = '20sp'
        self.title_color = WHITE
        self.separator_color = MO

        # set button defaults:
        self.butt_pars = {'background_color': MO_BGR,
                          'foreground_color': WHITE,
                          'font_size': '18sp',
                          'size_hint': (0.1, 0.2)}




# Main code to start app:
# if not SERVER:
#     # catch ctrl + c
#     import signal
#     signal.signal(signal.SIGINT, lambda *x: print("   nice try ;), but NO ctrl-c"))

sys = system()

if (sys == 'Linux'
    or (__name__ == "__main__")):     # needed for multiprocessing to not spawn multiple windows on mac & win (or start from run.py)
    try:
        # check certificates and serial
        pem = f"./keys/{'server' if SERVER else 'client'}.pem"
        cert_check = Encryption()
        cert_check.load_all(pem, "./keys/ca.cer")
        cert_check.check_certificates()


        if not SERVER:
            # check rpi serial
            check_serial() 
            pass            

        async def mainCoro():
            global app  
            # start GUI
            guiApp.TESTING = False
            app = guiApp()        
            await app.async_run()

        asyncio.run(mainCoro())

        # shutdown on exit
        if not SERVER:
            # os.system("sudo shutdown -h now")
            pass


    # NOTE: enable for real version (prevents hard crash)
    except Exception as e:
        import time
        log(f"{type(e).__name__}: {e}", "exception")
        
        from kivy.core.window import Window
        if not SERVER:
            time.sleep(3)
            app.stop()
            Window.close()
            
            # os.system("sudo reboot")

        else:
            # reset all chips just in case
            from subs.driver.sensors import chip_d
            for chip in chip_d.values():
                chip.reset()
                chip.init()

            # print("REBOOT")
            app.stop()
            Window.close()



# CRITICAL
# TODO: NOTES does not show last entry
# TODO: plotting full  has looped data in it.
# TODO: not plotting mystery:
#   - somehow data is not created in shared buffer, only notes
#   - the rec data_structure is not linked to the sav and IO datastructure
#   - data is recorded in buffer (autostim can find it, but not plotted) -> async start issue in IO ?
#   - issue with kivy clock calls on startup: need to wait till all are finished? solved no with a splash screen
#   - app.IO._plotdata does not show errors, fix this -> asyncio.gather does not print output, fixed now?!!


# HIGH
# TODO: update logger to print/save a certain level of exceptions with traceback when the exception is 
#       inputted instead of a string, use trackback.format_exception (see app.IO)
# TODO: when zooming out up to 3:40:15 ish, data is not plotted on rpi 
#       (maybe only if incrementing in steps of 1 sec) -> check now, does it work not that tbs are printed?
# TODO: do autostim in utc time if app.root.UTC is True, (e.g. replace datetime.now for datetime.utcnow  or  datetime.utcfromtimestamp(dtime.timestamp()))
#       or pull time from central clock

# TODO: central settings class with all settings and readouts (from chips recorder etc)
# TODO: can you disable chips now or not with new setup
# TODO: Why does autostim not stimulate?
# TODO: move slice when plotting so that decimation always selects same points with new data?
# TODO: subclass sensors so that not all other get the subclass parameters (class variables), e.g. OIS has pixel_no par from Lightstrip
# TODO: Stop keep awake (sometimes keeps going, maybe when pressing stop before stop autostim)
# TODO: Deal with live parameters of sensors: how to track and change them (e.g. OIS). 
#       Now they have to be separate set in rs.chip_d if not running or sent to recorder when running
# TODO: Reset button for autostim, autostim has method already, just need to add button and test

# NORMAL
# TODO: test if using generator to get items/values from dict in for loops etc is faster for functions here or (*map(f, iter),)
# TODO: make sure exit is clean, when pressing exit when running: it is clean after stopping rec, but not if stopping when no recording was started at all
# TODO: Fix network stuff in IO
# TODO: NETWORK FILE MANAGER (push/ pull files)
# TODO: Broadcasting values to all units (e.g. room control values)

# TODO: rewrite saver using asyncio

# TODO: reduce mem with slots https://bas.codes/posts/python-dict-slots (FOR Classes which do not make new attributes)
# TODO: use shared memory manager to track all shared lists and memory blocks
# TODO: Settings for hardware button
# TODO: use map instead of creating list and appending to it
# TODO: settings: reset to defaults button delete settings.ini or parts of settings.ini?

# TODO: Build Test Script (check output of all functions if changed?) -> ptyhon tests
# TODO: Check todos inline/inscript (search for # TODO)

# LOW PRIORITY
# TODO: multiple sms no for alerts (funcitonality is there but needs input from
#       gui)

# Notes
# NOTE: for configparserproperty: dont use capitals for value!! 
#       (also but not sure: Value Name should the same as the name of the variable)
# NOTE: asyncio.gather does not return/raise exceptions by default!! 
#           use return_exception=True kwarg catch output, then print/log expcetions
# NOTE: to call async def functions from kivy clock use: Clock.schedule_once(lambda dt: asyncio.run_coroutine_threadsafe(some_task(), loop), 5) 
#       TODO: make app.async_clock_call function for this?

'''
NOTES TO SELF:

to set property in other screen:
in this example set bluebutt color on recscreen from other screen
self.parent.get_screen('Record').ids['bluebutt'].color = MO_BGR
or
gui.root.ids.scrman.get_screen('Record').ids.bluebutt.color = MO_BGR

structure:

\app (guiApp):
    \root 
        \ menubar
        \screenmanager
            \RecScreen
            \SetScreen
            \RoomScreen
            \...
    \SIO (settingsIO)  -> handles dataIO, networkIO and settingsIO


Read and implement:

Observe using ‘on_<propname>’¶

If you defined the class yourself, you can use the ‘on_<propname>’ callback:

class MyClass(EventDispatcher):
    a = NumericProperty(1)

    def on_a(self, instance, value):
        print('My property a changed to', value)

Warning:
Be careful with ‘on_<propname>’. If you are creating such a 
callback on a property you are inheriting, 
you must not forget to call the superclass function too.


- BLACK BOXES LABELS:
    issue is that text is too large for the texture size: 
    self.texture_size might help, or try changing text length or text_size parameter
'''
