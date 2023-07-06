"""
Custom Kivy TextInput Widget:

Automatically validates text if unfocssed, e.g.
when clicking somewhere else

has a function to convert input to time and vice versa

use focusaction method to execute function after text input


NB this is the kv file part:
<TIn@TextInput>:
    size_hint: (.1, .07)
    text_size: self.size
    multiline: False
    foreground_color: 1,1,1,1
    background_color: 0.2,0.2,0.2,0.9
    font_size: '15sp'
    hint_text_color: MO
    background_color: 0.2,0.2,0.2,0.9
    base_direction: 'rtl'
    halign: 'right'
    valign: 'middle'
    use_bubble: True

"""

# IMPORTS
from kivy.uix.textinput import TextInput
from datetime import timedelta

try:
    import subs.gui.buttons.network_functions as nf
except:
    print("Textinput widget cannot import network functions")
    nf= None
from functools import partial


class TIn(TextInput):
    '''
    Automatically validates text if unfocussed
    '''
    idName = None
    scr = None
    send_nw = True    # set to false to not send interaction over network

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.suffix = ''                    # set unit
        self.prefix = ''                    # set unit
        if nf and self.send_nw:
            self.bind(text=lambda *_: nf.send_interaction(self, nf.cr_cmd('text', self.text)))

    def focusaction(self, *action):
        """
        excecute functions and pars
        e.g: self.focusaction(root.plusminbut, 'time', self.text)
        or: self.focusaction(setattr, self.parent,'text', self.text)
        or: self.focusaction(exec,'self.parent.text = self.text')
        """
        if self.focused:
            # clear text
            self.text = ""
        else:
            self.send_interaction()
            return partial(*action)()
    

    def send_interaction(self, *args):
        if nf and self.send_nw:
            nf.send_interaction(self, nf.cr_cmd('focus', True))
            nf.send_interaction(self, nf.cr_cmd('text', self.text))
            nf.send_interaction(self, nf.cr_cmd('focus', False))


    @staticmethod
    def time_IO(inp, option='sec'):
        """
        This method processes time input in the text input box.
        If ':' is found in the input it will be processed as time stamp
        if it is a number it will be processed as defined in option
        """
        if isinstance(inp, str):
            # convert time string to seconds (float)
            try:
                in_sp = [float(i) for i in inp.split(':')]
            except ValueError:
                return

            factor = (1, 60, 3600, 24 * 3600)  # multipl. fact. (s, m, h, day)
            sec = 0
            for i, t in enumerate(in_sp[::-1]):
                sec += t * factor[i]
            return sec

        else:
            # covert float sec to string (just seconds if 60s or smaller,
            # else in min sec etc)
            try:
                inp = float(inp)
            except (ValueError, TypeError):
                return ""
            #if not isinstance(inp, (int, float)):
            #    return

            if option == 'sec':
                if inp >= 60:
                    return '{:.10}'.format(str(timedelta(0, inp)))
                else:
                    tempstr = str(inp).split('.')
                    if len(tempstr) == 2:
                        maxdec = 3                            # max decimals
                        no_dec = len(tempstr[1])  # current decimals
                        dec = min(maxdec, no_dec)
                    else:
                        dec = 1
                    return '{:0.{prec}f} s.'.format(inp, prec=dec)
