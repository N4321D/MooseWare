from kivy.lang import Builder

Builder.load_string(
"""
#:kivy 1.10.1

# Keyboard Settings
<VKeyBoard>:
    key_background_color: MO  # keyboard color
    background: './Icons/Black.png'
    background_color: 0,0,0,1

# LAYOUT
<FLT@FloatLayout>:   # Default Lay-out for pages
    size_hint: 1, 1
    canvas.before:
        Rectangle:
            pos: self.pos
            size: self.size
            source: 'Icons/MooseBackgr.png'
        Color:
            rgba: 0,0,0,0.6
        Rectangle:
            pos: self.pos
            size: self.size
"""
)