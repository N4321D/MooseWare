"""
Popup Kivy widget

the "question" of the popup can be defined as title

popup.buttons contains all the button_names as keys and the methods and pars
as values (should be a callable, partial or lambda)
as pars you can pass all kivy button pars

example:
{'RED':{'color': (1, 0, 0, 1), 'do': partial(print, "this is red")}}
will create a button with red as red colored text. This button will print
"this is red" if pressed

defaults for the buttons can be set in butt_pars

if a button with "Enter" as text is created the popup will automatically be
a text_input

popup.textinput and popup.button can be overwritten with a custom button class
before init
"""

from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from functools import partial

class MyPopup(Popup):
    layout = GridLayout(rows=1)
    button = Button
    textinput = TextInput
    butt_pars = {}
    text_in_background_color = (0, 0, 0, 1)
    text_in_text_color = (1, 1, 1, 1)
    theme_color = (1, 1, 1, 1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto_dismiss = False

        # dict with Buttontext: action (as callable, partial or lambda):
        self.buttons = {}
        self.title = ''
        self.add_widget(self.layout)
        self.bind(on_open=self.create_popup)
        self.title_color = list(self.theme_color)

    def create_popup(self, *args):
        if "Enter" in self.buttons:
            self.create_textinput_popup()
        else:
            self.create_button_popup()

    def create_button_popup(self, *args):
        self.auto_dismiss = False
        self.layout.clear_widgets()
        self.layout.rows = int(len(self.buttons)/5) + 1

        for key in self.buttons:
            button = self.button(text=key)
            # set all vars:

            val = self.buttons[key]
            parameters = self.butt_pars.copy()
            parameters.update(val)
            [setattr(button, k, par) for k, par in parameters.items()]

            # bind command to button if there is a command defined in do
            if "do" in self.buttons[key]:
                button.on_release = partial(self.run_send,
                                            self.buttons[key]['do'])
            button.bind(on_release=self.dismiss)

            self.layout.add_widget(button)

    def create_textinput_popup(self, *args):
        self.auto_dismiss = True
        self.layout.clear_widgets()
        self.layout.rows = 1

        if "Enter" not in self.buttons:
            self.buttons['Enter'] = {'do': lambda x: x}

        self.text_in = self.textinput(background_color=self.text_in_background_color,
                                      foreground_color=self.text_in_text_color,
                                      cursor_color=self.theme_color,
                                      multiline=False,
                                      use_bubble=True,
                                      size_hint=(0.2, 0.5),
                                      )
        self.layout.add_widget(self.text_in)
        self.text_in.text_size = self.size
        self.text_in.focus = True
        button = self.button(text="Confirm")

        val = self.buttons["Enter"]
        parameters = self.butt_pars.copy()
        parameters.update(val)
        [setattr(button, k, par) for k, par in parameters.items()]
        self.layout.add_widget(button)
        button.on_release = partial(self.run_send, button.do, text=True)
        button.bind(on_release=self.dismiss)

    def run_send(self, inp, text=False):
        # send commands to network here
        # only accept partial functions as inp
        if text is True:
            # repack in partial if text input
            inp = partial(inp, self.text_in.text)

        try:
            cls = inp.func.__self__

            cls_name, func_name = inp.func.__qualname__.split(".")  # quallname gives class name.methodname
            args = inp.args
            kwargs = inp.keywords

            # send to network
            if cls.app.SERVER:
                cls.app.IO.send(('VAR', (cls.name, func_name, args, kwargs)))
                cls.app.IO.send(('VAR', ('app', 'popup.dismiss',(), {})))
        
        except:
            pass

        return inp()


if __name__ == "__main__":
    # Test Widget
    popup = MyPopup()
    popup.title = 'Blue pill or Red pill..\n ready to go down the rabbit hole?'
    popup.buttons = {'BLUE': {'background_color': (0.5, 0.5, 1, 1),
                              'do': partial(print, "Goodbye")},
                     'RED': {'background_color': (1, 0.5, 0.5, 1),
                             'do': partial(print,
                                           "Welcome to the real world")}
                     }
    popup.size_hint = (0.5, 0.5)
    popup.butt_pars = {'color': (0, 1, 0, 1)}

    class TestButton(Button):
        def on_release(self):
            popup.open(auto_dismiss=True)

    from kivy.app import App
    class MyApp(App):

        def build(self):
            return TestButton(text='Popup',
                              size_hint=(0.3, 0.3),
                              pos_hint={'x': 0.35, 'top': 0.65})

    MyApp().run()


# TODO: send text input
# TODO: handle sending kwargs (check set_vars in setIO)
