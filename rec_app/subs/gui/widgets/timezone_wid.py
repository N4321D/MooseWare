"""
Set timezone on rpi/linux
can also be used to set time (not implemented yet)
"""

# create logger
try:
    from subs.log import create_logger
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None: 
                f = lambda *x: print("TIMEZONE: ", *x)  # change messenger in whatever script you are importing
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()

def log(message, level="info"):
    getattr(logger, level)("TIMEZONE: {}".format(message))  # change RECORDER SAVER IN CLASS NAME


from subs.gui.vars import BUT_BGR, MO, MO_BGR
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.lang.builder import Builder

from subs.gui.buttons.DropDownB import DropDownB
from subs.gui.vars import WHITE, MO, BUT_BGR, MO_BGR

from subs.driver.timezone import TimeZone

builder_str= """
# Kivy Builder String. 
# Contains kivy settings in kv language, 
# later imported in builder


#: import Clock kivy.clock.Clock

<TzWidget>:    # <> is very important: defines class properties without initiating them
    MyDropDownB:
        id: continent
        text: "Network"
        pos_hint: {"x": 0, "y": 0}
        size_hint: 0.5, 1
        on_text:
            root.change_continent(self.text)

    MyDropDownB:
        id: region
        text: "Network"
        pos_hint: {"x": 0.5, "y": 0}
        size_hint: 0.5, 1
        on_text:
            root.change_tz(self.text)
"""

   
class MyDropDownB(DropDownB):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.font_size = '15sp'
        self.color = WHITE
        self.background_color = MO_BGR
        self.drop_but_size = "50sp"
        

class TzWidget(FloatLayout):
    continent = ""
    region = ""

    new_continent = ""
    new_region = ""

    def __init__(self, **kwargs) -> None:
        Builder.load_string(builder_str)

        super().__init__(**kwargs)
        self.tz = TimeZone()
        self.continent, self.region = self.tz.continent, self.tz.region

        Clock.schedule_once(self.__kv__init__, 0)
        self.update_event = Clock.schedule_once(self.update_current, 30)
        self.update_event.cancel()
    
    def __kv__init__(self, dt):
        self.set_continents()

        
    def set_continents(self, *args):
        self.ids.continent.types = list(self.tz.timezones)
        self.update_current()
    
    def change_continent(self, continent):
        self.new_continent = continent
        if continent in self.tz.timezones:
            self.ids.region.types = self.tz.timezones[continent]
            self.ids.region.text = "Select Region"
        self.update_event()

    def update_current(self, *args):
        self.ids.continent.text = str(self.continent)
        self.ids.region.text = str(self.region)
    
    def change_tz(self, region):
        if not self.disabled:
            self.new_region = region
            
            # only set if different region or continent
            _do = self.new_region != self.region
            
            if self.new_continent in self.tz.timezones and _do:
                if self.new_region in self.tz.timezones[self.new_continent]:
                    self.continent, self.region = self.tz.set_timezone(self.new_continent, self.new_region)
                    log(f"changed timezone {self.continent} {self.region}", "info")



if __name__ == "__main__":
    # Test Widget
    from kivy.app import App
    
    class MyApp(App):
        def build(self):
            return TzWidget()

    app = MyApp()
    app.run()