"""
MAIN MENU dropdown button to switch between screens

types contains the names in the drop down menu as keys
and screens as values


kv file:
<MenuButt@StdButton>:
    size_hint: 0.2,0.1

<MENU@MenuBut>:
    id: MENU
    pos_hint: {'x': 0, 'top': 1}
    color: 1,1,1,1
    background_color: MO_BGR
    text: 'MENU'
    size_hint: 0.2, 0.1
    on_text: app.root.current = self.command
    halign: 'center'

"""

from kivy.uix.button import Button
from kivy.properties import StringProperty
from kivy.uix.dropdown import DropDown
from kivy.app import App
from kivy.clock import Clock

import subs.gui.buttons.network_functions as nf


class MenuBut(Button):
    text = StringProperty('')
    types = {}
    roomcontrol = False
    idName = None
    scr = None
    drop_list = None
    del_vars = ["Menu", "scrsav",]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        Clock.schedule_once(self.get_screens, 0)

    def get_screens(self, *args):
        # get screen names from screen manager
        self.types = {i:i for i in self.app.root.ids.scrman.screen_names}
        self.create_list()
        self.text = self.app.root.ids.scrman.current_screen.name

    def create_list(self, *args):
        if not self.drop_list:
            self.drop_list = DropDown()

            # add & remove custom/hidden screens
            self.types.update({"EXIT": "EXIT"})
            for v in self.del_vars:
                del self.types[v]

            if not self.roomcontrol:
                del self.types['Ambient']

            self.drop_list.clear_widgets()
            for i in self.types:
                btn = Button(text=i,
                            size_hint_y=None,
                            height='48sp',
                            font_size='20sp',
                            background_color=(0.5, 0.5, 0.5, 0.9),
                            halign='center')
                btn.bind(on_release=lambda btn: self.drop_list.select(btn.text))
                self.drop_list.add_widget(btn)

            self.bind(on_release=self.drop_list.open)
            self.drop_list.bind(on_select=lambda instance,
                                x: setattr(self, 'text', x))

    def do(self, *args, txt=None):
        if txt is None:
            txt = self.text

        if txt in self.types:
            if txt == "EXIT":
                self.text = "MENU"
                self.app.popup.load_defaults()
                self.app.popup.buttons = {"YES": {'do':self.app.stop},
                                     "NO": {}}
                self.app.popup.title = 'Exit?'
                self.app.popup.pos_hint = {'top': 0.8}
                self.app.popup.open()
            else:
                nf.send_interaction(self, nf.cr_cmd('text', txt))
                self.app.root.ids.scrman.current = self.types[txt]
