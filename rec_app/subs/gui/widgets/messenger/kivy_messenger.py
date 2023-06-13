import datetime
from subs.gui.widgets.messenger.messenger import Messenger as Msg
from kivy.properties import ConfigParserProperty
from kivy.event import EventDispatcher
from datetime import timedelta, datetime
from subs.gui.widgets.custom_settings import timestr_2_timedelta, val_type_loader


class Messenger(EventDispatcher):
    msg = Msg()
    
    number = ConfigParserProperty('', 'other', 'alert_phone_no', 'app_config', val_type=str)
    alert_message = ConfigParserProperty('', 'other', "alert_message", "app_config", val_type=str)
    alert_interval = ConfigParserProperty(timedelta(hours=3), "other", 
                                          "alert_interval", "app_config", val_type=timestr_2_timedelta)
    alert_enable = ConfigParserProperty(True, "other", "alert_enable", "app_config", val_type=val_type_loader)

    last_alert = datetime(1,1,1)

    app = None

    def __init__(self, app) -> None:
        self.app = app
        self.bind(number=lambda *_: setattr(self.msg, 'to_no', [self.number]))

    def send_alert(self, message, immediately=False):
        """
        send alert to sms numbers
        
        immediately: ignore alert interval and send message
        """
        if ((datetime.now() - self.last_alert < self.alert_interval)
            and immediately is False):
            return
        
        _name = ('TESTING' if self.app.TESTING else self.app.setupname)
        message = f"From: {_name}\n{self.alert_message}\n{message}"

        self.msg.send_alert(message)
        if not immediately:
            self.alert_last_t = datetime.now()
    
        if not self.app.TESTING:
            self.msg.send_alert(message)

        else:
            print(self.msg.base_text + message)
