"""
Wifi manager for kivy
works with linux/rpi

"""
# create logger
try:
    from subs.log import create_logger
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None: 
                f = lambda *x: print("WIFIMANAGER: ", *x)  # change messenger in whatever script you are importing
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()

def log(message, level="info"):
    getattr(logger, level)("WIFIMANAGER: {}".format(message))  # change RECORDER SAVER IN CLASS NAME


from subs.gui.vars import BUT_BGR, MO, MO_BGR
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.lang.builder import Builder

from subs.gui.buttons.DropDownB import DropDownB
from subs.gui.vars import WHITE, MO, BUT_BGR, MO_BGR
from subs.gui.buttons.TextIn import TIn

from subs.driver.wifi import RpiWifi

import threading as tr

builder_str= """
# Kivy Builder String. 
# Contains kivy settings in kv language, 
# later imported in builder


#: import Clock kivy.clock.Clock

<WifiWidget>:    # <> is very important: defines class properties without initiating them
    MyButton:
        text: "Connect"
        pos_hint: {"x": 0.5, "y": 0.75}
        on_release:
            root.connect(nw_ddbut.text, passwd_in.text)
    
    MyButton:
        text: "Forget"
        pos_hint: {"x": 0.5, "y": 0.5}
    
    WifiDropDownB:
        id: nw_ddbut
        text: "Network"
        pos_hint: {"x": 0, "y": 0.75}
        size_hint: 0.5, 0.25
        on_release:
            self.types = ["Scanning..."]
            root.scan()
    
    WifiTIn:
        id: passwd_in
        halign: "left"
        hint_text: "Password"
        pos_hint: {"x": 0, "y": 0.5}
        size_hint: 0.5, 0.25
        #password: True

    Label:
        pos_hint: {"x": 0, "y": 0}
        halign: "left"
        valign: "top"
        size_hint: 0.3, 0.5
        stats: "-"
        ip: "-"
        ssid: "-"
        text: "Status:\\nNetwork:\\nIP:\\nMAC:"
        text_size: self.size

    Label:
        id: st_txt
        pos_hint: {"x": 0.3, "y": 0}
        halign: "left"
        valign: "top"
        size_hint: 0.7, 0.5
        stats: ""
        ip: ""
        ssid: "-"
        text: "{}\\n{}\\n{}\\n{}".format(self.stats, self.ssid, self.ip, app.MACADDRESS)
        text_size: self.size
"""

class MyButton(Button):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.font_size = '15sp'
        self.color = MO
        self.background_color = BUT_BGR
        self.halign = "center"
        self.valign = "center"
        self.markup = True
        self.size_hint = 0.5, 0.25
    
class WifiDropDownB(DropDownB):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.font_size = '15sp'
        self.color = WHITE
        self.background_color = MO_BGR
        self.drop_but_size = "50sp"
        Clock.schedule_once(self.__kv__init__, 0)

    def __kv__init__(self, dt):
        setattr(self.drop_list, "on_dismiss", self.parent.stop_scan)
        

class WifiTIn(TIn):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.halign = 'right'
        self.valign = 'middle'
        self.size_hint = (.1, .07)
        self.text_size = self.size
        self.multiline = False
        self.foreground_color = WHITE
        self.background_color = 0.2, 0.2, 0.2, 0.9
        self.font_size = '15sp'
        self.hint_text_color = MO

class WifiWidget(FloatLayout):
    def __init__(self, **kwargs) -> None:
        Builder.load_string(builder_str)
        super().__init__(**kwargs)
        self.wifi = RpiWifi()
        self.scan_event = Clock.schedule_interval(self._scan, 2)
        self.scan_event.cancel()
        self.stat_event = Clock.schedule_interval(self.update, 1)
    
    def connect(self, ssid, passwd):
        log(f"connect to wifi: {ssid}:******", "debug")
        self.ids.passwd_in.text = ''
        self.wifi.connect(ssid, passwd)
        Clock.schedule_once(self.update, 1)

    def forget(self, ssid):
        self.wifi.remove_known_ssid(ssid)
        self.ids.passwd_in.text = ''
        self.ids.nw_ddbut.text = "Network"

    def scan(self):
        # return tr.Thread(target=self._scan).start()
        self.scan_event()
        
    def stop_scan(self):
        self.scan_event.cancel()

    def _scan(self, *args):
        if not self.disabled:
            res = self.wifi.scan()
            if res:
                self.ids.nw_ddbut.types = list(res)
    
    def update(self, *args):
        if not self.disabled:
            self.wifi.check_connection()
            status = self.wifi.status.get("wpa_state")
            self.ids.st_txt.ip = self.wifi.ip
            self.ids.st_txt.stats = status if status else "-"
            self.ids.st_txt.ssid = self.wifi.status.get("ssid", "-")


if __name__ == "__main__":
    # Test Widget
    from kivy.app import App
    
    class MyApp(App):
        MACADDRESS = "00:00:00:00:00"
        def build(self):
            return WifiWidget()

    app = MyApp()
    app.run()