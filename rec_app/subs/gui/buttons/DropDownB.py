"""

CLASSIC DropDown, define types in kivy language (or python)

execute with on_text:
self.command has the proccessed selection

size of the font and buttons in the dropdown can be changed by changing
drop_but_size and drop_but_font_size. NB: if you do this in the .kv file do it
before settings types or text (otherwise the buttons are already created)
see example

3 kv-file examples:
<SPLOT@DropDownB>:      # select data to plot in graphs button
    id: selplot
    # types:  ['Light', 'Motion', 'Int Press', 'Ext Press', 'Pressure', 'Off']
    pos_hint: {'x': 0.2, 'top': 0.8}
    color: 1,1,1,1
    background_color: MO_BGR
    text: 'Source'
    size_hint: 0.2, 0.06
    on_text: print(self.command)
    halign: 'center'

<DROPB@DropDownB>: # general DropDown, set types to change (types: ['1','2'])
    id: selplot
    pos_hint: {'x': 0.2, 'top': 0.8}
    color: 1,1,1,1
    background_color: MO_BGR
    text: 'Menu'
    size_hint: 0.1, 0.05
    on_text: print(self.command)
    halign: 'center'

<SAVELOAD@DROPB>:       # save load button
    pos_hint: {'x': 0.2, 'top': 1}
    size_hint: 0.07, 0.1
    drop_but_size: '48sp'               # must be before types and text
    drop_but_font_size: '20sp'          # must be before types and text
    types: ['SAVE', 'LOAD', 'RESET']
    text: 'Save\nLoad'
    on_text:
        if self.text != 'Save\nLoad': root.parent.savemenu(self.text); self.text = 'Save\nLoad'

"""
from kivy.uix.button import Button
from kivy.properties import StringProperty, ListProperty
from kivy.uix.dropdown import DropDown

try:
    import subs.gui.buttons.network_functions as nf
except:
    print("dropdown button cannot import network")
    nf = None


class DropDownB(Button):
    text = StringProperty('')
    types = ListProperty([])        # list with items
    screens = ListProperty([])
    drop_but_size = '32sp'         # size of drop down buttons 
    drop_but_font_size = '15sp'    # font size of drop down buttons 
    idName = None
    scr = None
    changetext = True  # indicates if choosing choice changes text
    send_nw = False  # set to True to send interaction over network

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drop_list = None
        self.drop_list = DropDown()
        self.bind(types=self.update)

    def update(self, *args):
        self.bind(text=self.do)

        self.drop_list.clear_widgets()
        for i in self.types:
            btn = Button(text=i,
                         size_hint_y=None,
                         height=self.drop_but_size,
                         font_size=self.drop_but_font_size,
                         background_color=(0.5, 0.5, 0.5, 0.9),
                         halign='center')
               
            btn.bind(on_release=lambda btn: self.drop_list.select(btn.text))
            self.drop_list.add_widget(btn)


        self.bind(on_release=self.drop_list.open)

        if self.changetext:
            self.drop_list.bind(on_select=lambda instance,
                                x: setattr(self, 'text', x))

    def do(self, *args, txt=None):
        if txt is None:
            txt = self.text
        if txt in self.types:
            if nf and self.send_nw:
                nf.send_interaction(self, nf.cr_cmd('text', txt))
            setattr(self, 'command', txt)
