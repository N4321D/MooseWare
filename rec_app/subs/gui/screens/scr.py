"""
Screen Template

"""

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.clock import Clock


from functools import partial
from subs.gui.widgets.notes import Notes


Builder.load_string(
""" 
#:kivy 1.10.1

<Scr>:
    on_enter:
        app.scrsav_event()
        self.show_hide(self.server_widgets, app.SERVER)
        app.root.ids.MENU.text = self.manager.current

    on_touch_up: app.scrsav_event()
    
    FLT: # background

"""
)

# Define Screens:
class Scr(Screen):
    '''
    Default screen class

    includes save load function

    to save parameters their name must be as string in the savepars list
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server_widgets = [] # widget ids to show only when SERVER
        
        self.app = App.get_running_app()

    def show_hide(self, wid_id, hide_show):
        """
        this shows(True)/hides(false) widget by moving them out of the
        screen, the widget must have pos_hint defined as {'x': ...}

        #TODO: use remove/add widget instead?
        """
        if not isinstance(wid_id, (list, tuple)):      # test if list/tuple
            wid_id = (wid_id,)

        for w in wid_id:
            # move button back in screen:
            if (hide_show is True and self.ids[w].pos_hint['x'] > 1):
                self.ids[w].pos_hint['x'] -= 1
                self.ids[w].disabled = False
                self.do_layout()

            # move button out of screen:
            elif (hide_show is False and self.ids[w].pos_hint['x'] < 1):
                self.ids[w].pos_hint['x'] += 1
                self.ids[w].disabled = True
                self.do_layout()


