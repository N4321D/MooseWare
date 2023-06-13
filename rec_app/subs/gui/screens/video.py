"""
Video Screen

NB: Kv String cannot contain \n -> must be \\n

"""


from kivy.lang.builder import Builder
from subs.gui.screens.scr import Scr
from subs.gui.vars import *
from kivy.clock import Clock

kv_str = """
#:kivy 1.10.1

<VideoScreen>:
    on_enter:
        vid_play.plotting = True
        if vid_play.input_type == "camera": vid_play.start_stop_preview('start')
        vid_play.update_event()

    on_leave:
        vid_play.plotting = False
        if vid_play.input_type == "camera": vid_play.start_stop_preview('stop')
        vid_play.update_event.cancel()

    VideoDisplay:
        id: vid_play
        size_hint: 0.6, 0.6
        pos_hint: {'right': 0.8, 'top':0.8}
        text_size: self.size

    setLab:
        pos_hint: {'right': 0.15, 'top':0.8}
        size_hint: (0.1, 0.2)
        text: 'Mouse Location\\n x:{}, y:{}\\nconfidence: {}%'.format(8,29,88)
    
    setLab:
        pos_hint: {'right': 0.95, 'top':0.8}
        text: '{} x {} @ {}'.format(*vid_play.res_fps)
    


    DROPB:
        pos_hint: {'x': 0.8, 'y': 0.55}
        size_hint: (0.2, 0.1)
        text: 'Resolution'
        modes: {'640p': 'VGA', '720p': '720p', '1080p': '1080p'}
        disabled: True if vid_play.recording else False
        types: self.modes
        on_text: 
            vid_play.video_in.set_res_fps(self.modes[self.text])
    
    setLab:
        pos_hint: {'x': 0.8, 'y': 0.65}
        text: "FPS:"
        valign: 'middle'
        halign: 'right'

    TIn:
        pos_hint: {'x': 0.9, 'y': 0.65}
        input_filter: 'float'
        disabled: True if vid_play.recording else False
        on_focus:
            fps = float(self.text) if self.text else None
            vid_play.start_stop_preview('stop')
            self.focusaction(vid_play.video_in.set_res_fps, (None, None, fps))
            self.focusaction(vid_play.start_stop_preview, 'start')
        
    StdButton:
        id: startrec
        pos_hint: {'right': 1, 'top':0.1}
        size_hint: (0.2, 0.1)
        text: 'Start\\nRec.' if not vid_play.recording else 'Stop\\nRec.'
        on_release: vid_play.start() if not vid_play.recording else vid_play.stop()
        color: WHITE if vid_play.recording else MO
        background_color: MO_BGR if vid_play.recording else BUT_BGR
    
    StdButton:
        id: preview
        pos_hint: {'x': 0.8, 'top':0.2}
        size_hint: (0.2, 0.1)
        text: 'Open\\nPreview' if not vid_play.previewing else 'Close\\nPreview'
        on_release: vid_play.start_stop_preview("start") if not vid_play.previewing else vid_play.start_stop_preview("stop")
        color: WHITE if vid_play.previewing else MO
        background_color: MO_BGR if vid_play.previewing else BUT_BGR
        send_nw: False

"""


class VideoScreen(Scr):
    mouse_location = (0, 0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(kv_str)
        self.server_widgets.append('preview')