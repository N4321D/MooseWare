"""
This button class creaetes buttons that automatically send their
id to the server.
"""

from kivy.uix.button import Button

import subs.gui.buttons.network_functions as nf


class Server_Button(Button):
    idName = None
    scr = None
    send_nw = True       # set to false to disable sending

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(on_release=self.send_press)
        self.app = None

    def send_press(self, *args):
        if self.last_touch and self.send_nw:
            touch_duration = (self.last_touch.time_end
                              - self.last_touch.time_start)

            nf.send_interaction(self,
                                nf.cr_cmd('trigger_action',
                                          kwa={'duration': touch_duration}))
