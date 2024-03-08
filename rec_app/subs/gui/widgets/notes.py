"""
Notes widget

This widget is a popup to write notes

It has 4 quicknote buttons defined in the cust_widgets.kv file
if you want to add more you have to manually adjust the lenght of the
quick_note_text list and the button_no in the kv file
"""

from datetime import datetime
from types import new_class
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder

kv_str = """
<NOTEBUT@LongPress>:
    size_hint: 0.1, 0.2
    color: WHITE
    background_color: 0, 1, 0, 1
    font_size: '12sp'

<Notes>:
    # Notes widget
    pos_hint: {'x': 0.05, 'top': 1}
    size_hint: 0.9, 0.45
    id: notes

    canvas.before:
        Color:
            rgba: (0.1, 0.2, 0.1, 0.9)
        Rectangle:
            pos: self.pos
            size: self.size
        Line:
            width: 2
            rectangle: self.x, self.y, self.width, self.height

    ScrollView:
        id: notes_scroll
        # see API for more options
        do_scroll_x: False
        do_scroll_y: True
        pos_hint: {'x':0, 'top': 1}
        size_hint: 0.8, 0.7
        bar_color: 1, 1, 1, 1
        bar_inactive_color: .7, .7, .7, .5
        bar_width: 4
        scroll_type: ['bars', 'content']
        scroll_wheel_disctance: notes_text.size[1]/25   # scroll speed, here based on size of total text
        smooth_scroll_end: 10                           # acceleration and decelleration of scrolling

        Label:
            id: notes_text
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width, None
            padding: 10, 10

    TIn:
        id: notes_tin
        pos_hint: {'x':0, 'top': 0.2}
        size_hint: 1, 0.2
        base_direction: 'ltr'
        halign: 'left'
        valign: 'top'
        on_text: root.add_text(self.text)

    NOTEBUT:
        # SAVE BUTTON
        pos_hint:{'x': 0.9, 'top': 0.2}
        text: 'save'
        on_release:
            root.save()

    NOTEBUT:
        pos_hint: {'x': 0.9, 'top': 0.4}

    NOTEBUT:
        pos_hint: {'x': 0.9, 'top': 0.6}

    NOTEBUT:
        # QUICK NOTE
        pos_hint:{'x': 0.8, 'top': 0.4}
        text: root.quick_note_text[0]
        short_press: partial(root.get_quick_note, notes_tin, self)
        long_press: partial(root.set_quick_note, self, 0)


    NOTEBUT:
        # QUICK NOTE
        pos_hint:{'x': 0.8, 'top': 0.6}
        text: root.quick_note_text[1]
        short_press: partial(root.get_quick_note, notes_tin, self)
        long_press: partial(root.set_quick_note, self, 1)

    NOTEBUT:
        # QUICK NOTE
        pos_hint:{'x': 0.8, 'top': 0.8}
        text: root.quick_note_text[2]
        short_press: partial(root.get_quick_note, notes_tin, self)
        long_press: partial(root.set_quick_note, self, 2)

    NOTEBUT:
        # QUICK NOTE
        pos_hint:{'x': 0.8, 'top': 1}
        text: root.quick_note_text[3]
        short_press: partial(root.get_quick_note, notes_tin, self)
        long_press: partial(root.set_quick_note, self, 3)


    NOTEBUT:
        pos_hint:{'x': 0.9, 'top': 0.6}

    NOTEBUT:
        # CLEAR BUTTON
        pos_hint:{'x': 0.9, 'top': 0.8}
        text: 'clear'
        on_release: notes_tin.text = ""

    NOTEBUT:
        # CLOSE BUTTON
        pos_hint:{'x': 0.9, 'top': 1}
        text: 'close'
        on_release:
            root.close()

"""


class Notes(FloatLayout):
    """
    Notes widget
    """
    quick_note_text = ["quick note\n[i][color=FFFFFF7F]"
                       "hold to set[/i][/color]"] * 4
    steps_back = 0          # current steps back to show from last note (limited by max_lines)
    max_lines = 200         # maximun number of lines to display (to prevent label not showing text)

    def __init__(self,  app, **kwargs):
        Builder.load_string(kv_str)
        super().__init__(**kwargs)
        self.app = app

        self.text = ''             # all the text to display
        self.new_text = ''          # new input text
        self.bind(parent=self.show_hide)

    def _change_displayed_text(self):
        """
        updates the displayed notes in the widgets
        number of lines displayed is limited to the last self.max_lines
        """

        _end = self.app.IO.data_structure.get('added', 'notes')                 # idx of last note

        if self.steps_back < self.max_lines:
            self.steps_back = min(_end, self.max_lines) # or 1                  # add to steps back (to prevent looping in buffer if just started) return at least 1 item

        notes = self.app.IO.get_buf('notes', n_items=self.steps_back, subpar='note')
        t = self.app.IO.get_buf('notes', n_items=self.steps_back, subpar='time')

        # covert timestamp to readable format zip notes and timestamps & limit charaters per line
        if self.app.root.UTC:
            _dt_f = datetime.utcfromtimestamp
        else:
            _dt_f = datetime.fromtimestamp
        _text = map(lambda _t, n: f"{_dt_f(_t).strftime('%x %X')}: {n.decode()}"[:self.max_lines], 
                    t, notes)

        self.ids['notes_text'].text = "\n".join(_text)

    def save(self, *args):
        self.app.IO.add_note(self.new_text)
        self._change_displayed_text()

    def add_text(self, txt):
        # this function accepts the input text
        self.new_text = txt

    def show_hide(self, instance, parent):
        if parent is not None:
            self.ids['notes_scroll'].scroll_y = 0
            # update text
            self._change_displayed_text()

    def set_quick_note(self, button, button_no):
        button.text = self.new_text
        Notes.quick_note_text[button_no] = self.new_text
        button.text_size = button.size

    def close(self, *args):
        self.parent.remove_widget(self)

    def on_touch_down(self, touch):
        """
        close widget when pressed outside
        """
        if not self.collide_point(*touch.pos):
            self.close()
        
        else: 
            return super().on_touch_down(touch)

    @staticmethod
    def get_quick_note(textinput, button):
        if button.text != ("quick note\n[i][color=FFFFFF7F]"
                          "hold to set[/i][/color]"):
            textinput.text = textinput.text + ' ' + button.text

