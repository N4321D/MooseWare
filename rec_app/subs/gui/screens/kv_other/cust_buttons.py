from kivy.lang import Builder

# Custom Buttons DO NOT REMOVE NEEDED FOR KV:
from subs.gui.buttons.Server_Button import Server_Button
from subs.gui.buttons.DropDownB import DropDownB
from subs.gui.buttons.MenuBut import MenuBut
from subs.gui.buttons.TextIn import TIn



Builder.load_string(
"""
#:kivy 1.10.1
# Custom BUTTONS
<StdButton@Server_Button>:                                                             # settings for all buttons
    font_size: '15sp'
    color: MO
    background_color: BUT_BGR
    size_hint: 0.1, 0.1  # relative size
    halign: 'center'
    valign: 'center'
    markup: True
    idName: None   # save id name in here for triggering later
    send_nw: True  # can be set to false to disable sending for specific buttons

<LongPress@StdButton>:
    # a button with long press function
    # threshold is defined in sec by press_threshold
    # long_press action defines action on long_press; short_press for short press:
    #   must be lambda e.g.: lambda: setattr(self, 'background_color', (1,1,0,1))
    #   actions can be list with multiple actions
    press_threshold: 0.3  # threshold between short and long press in sec
    short_press: lambda: None
    long_press: lambda: None
    on_release:
        dur =  self.last_touch.time_end - self.last_touch.time_start
        self.short_press() if dur < self.press_threshold else self.long_press()

<PlusButton@StdButton>:                                                            # plus button
    font_size: '40sp'
    color: MO
    background_color: PLUS_GREEN
    color: 1, 1, 1, 0.6
    size_hint: 0.1, 0.1  # relative size
    halign: 'center'
    valign: 'center'
    text: '+'
    bold: True

<MinusButton@PlusButton>:                                                            # Minus button
    font_size: '60sp'
    background_color: MINUS_RED
    text: '-'

<MENU@MenuBut>:
    roomcontrol: app.ROOM_CONTROL
    pos_hint: {'x': 0, 'top': 1}
    color: WHITE
    background_color: MO_BGR
    size_hint: 0.15, 1
    font_size: '21sp'
    halign: 'center'
    on_text:
        self.do()

<SPLOT@DropDownB>:      # select data to plot in graphs button
    id: selplot
    pos_hint: {'x': 0.2, 'top': 0.8}
    drop_but_size: "42sp"
    # drop_but_font_size: '20sp'          # must be before types and text
    color: WHITE
    background_color: MO_BGR
    text: 'Source'
    size_hint: 0.2, 0.06
    halign: 'center'


<DROPB@DropDownB>: # general DropDown, set types to change (types: ['1','2'])
    id: selplot
    pos_hint: {'x': 0.2, 'top': 0.8}
    color: WHITE
    background_color: MO_BGR
    text: 'Menu'
    size_hint: 0.1, 0.05
    halign: 'center'

<SLID@Slider>:
    size_hint: 0.1, 0.38
    value_track_color: SLIDER_ORANGE
    range: 0, 100
    cursor_image: 'Icons/MooseIcon_Head_S.png'
    cursor_size: '50sp', '50sp'
    value: 50
    value_track: True
    orientation: 'vertical'

<MENULABEL@Label>:    # menu label
    texture_size: self.size
    text_size: self.size
    font_size: '22sp'
    valign: 'center'
    halign: 'center'
    color: MO
    markup: True
    markup: True


<FEEDBACK@Label>:    # menu label
    texture_size: self.size
    text_size: self.size
    font_size: '10sp'
    valign: 'top'
    halign: 'right'
    color: 0.7, 0.7, 0.7, 0.7
    markup: True

<setLab@Label>:
    # labels for stimulation and settings
    pos_hint: {'right': 0.8, 'top': 0.62} #relative sizes 0-1
    halign: 'right'
    size_hint: 0.1, 0.05
    text: 'LABEL'
    font_size: '15sp'
    color: WHITE

<MW@Widget>:
    # top menu bar
    pos_hint: {'x': 0, 'top': 1}
    size_hint: 1, .97
    canvas.before:
        Color:
            rgba: GRAPH_BACKGROUND
        Rectangle:
            pos: self.pos
            size: self.size

<TIn>:
    size_hint: (.1, .07)
    text_size: self.size
    multiline: False
    foreground_color: 1,1,1,1
    background_color: 0.2,0.2,0.2,0.9
    font_size: '15sp'
    hint_text_color: MO
    base_direction: 'rtl'
    halign: 'right'
    valign: 'middle'
    use_bubble: True

<TogBut@ToggleButton>:
    # buttons on bottom of set screen
    # toggle button has group and only one button can be down (=pressed)
    color: WHITE if self.state == 'down' else MO
    background_color: MO_BGR if self.state == 'down' else BUT_BGR
    background_down: 'atlas://data/images/defaulttheme/button' # default background
    font_size: '20sp'
    size_hint: 0.2, 0.1
    halign: 'center'

"""
)