"""
This is a kivy widget which can show frames grabbed with opencv
(numpy arrays, bgr format)
of from picam 
(by direcly dumping the GPU buffer on the screen,
so not really using kivy)
"""
# create logger
try:
    from subs.log import create_logger
    
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None: 
                f = lambda *x: print("VIDEO WIDGET: ", *x)  # change messenger in whatever script you are importing
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()

def log(message, level="info"):
    getattr(logger, level)("VIDEO WIDGET: {}".format(message))  # change RECORDER SAVER IN CLASS NAME


from platform import system, machine

SYS_MACH = (system(), machine())

from kivy.properties import BooleanProperty, ListProperty
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.image import Image


try:
    from subs.video.videoprocessing import VideoProcessing
except Exception as e:
    log('Unable to load camera: {}'.format(e), "warning")

try:
    from subs.video.gstreamerH264 import H264Decoder
except Exception as e:
    log('Cannot load H264 decoder, is Gstreamer installed? {}'.format(e), "warning")

TEXT_FMT = 'rgb' if SYS_MACH == ('Linux', 'armv7l') else 'bgr'
log("Texture used: {}".format(TEXT_FMT), "info")


class VideoDisplay(Widget):
    res_fps = ListProperty([1280, 720, 10])      # res & frame rate of video
    recording = BooleanProperty(False)      # indicates if playing or not
    previewing = BooleanProperty(False)      # indicates if previewing or not
    text_fmt = TEXT_FMT                   # texture format
    plotting = False
    video_in = None                     # placeholder for video processing
    player = None
    player_texture = None               # temporary texture for player
    img = None
    texture = None
    update_event = None                 # updates actual video settings
    input_type = 'camera'               # inputtype of video
    source_url = ''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = Image(source='./Icons/vid_play_bg.jpg',
                            size=self.size,
                            pos=self.pos)

        self.add_widget(self.player)
        self.bind(size=self._update_player_size)
        self.bind(pos=self._update_player_pos)

        self.texture_size = self.size
        if "VideoProcessing" in globals():
            self.video_in = VideoProcessing(parent=self)

        elif "H264Decoder" in globals():
            self.video_in = H264Decoder()

        try:
            self.input_type = self.video_in.output_type
        except AttributeError:
            self.input_type = None
        log("{} video input".format(self.input_type), "info")

        self.update_event = Clock.schedule_once(self.update, 1)
    
    def update(self, *args):
        if self.video_in:
            self.res_fps = (*self.video_in.res, self.video_in.fps)
            self.update_event.timeout = 1/self.res_fps[2]

        if self.plotting is True and self.input_type != 'camera':
            return self.update_event()
    
            
    def start(self, recording=True):
        if self.input_type == "camera":
            if recording is True:
                self.recording = True
                self.video_in.recording = True
            # set annotation
            _name = '{} - {}'.format(self.parent.app.setupname,
                                    self.parent.app.IO.recording_name)
            self.video_in.options['annotate_text'] = _name
            self.video_in.start()
            self.res_fps[2] = VideoProcessing.fps
            self.parent.app.IO.send(("VAR", ("vid", "ids.vid_play.recording", (True,), {})))

    def stop(self):
        if self.input_type == "camera":
            self.video_in.recording = False
            self.video_in.stop()
            self.recording = False
            if self.input_type == 'camera':
                self.video_in.camera.annotate_text = 'Preview'
            self.parent.app.IO.send(("VAR", ("vid", "ids.vid_play.recording", (False,), {})))


    def start_stop_preview(self, mode='start'): 
        self.previewing = True if mode == "start" else False

        if self.input_type == 'camera':
            # On RPI
            if mode == 'start':
                (self.video_in.camera
                .start_preview(window=[int(_i) for _i in 
                                        (*self.pos, *self.size)], 
                                fullscreen=False,)
                )

            else:
                self.video_in.camera.stop_preview()
        
        else:
            # On server
            if self.parent.app.IO.server.udp_sink is None:
                self.parent.app.IO.server.udp_sink = self.video_in.write

            if mode == "start":
                self.video_in.start(self.res_fps[:2])
                self.parent.app.IO.send(("VAR", ("vid", "ids.vid_play.video_in.start_nw_stream", (), {})))
            else:
                self.video_in.stop()
                self.parent.app.IO.send(("VAR", ("vid", "ids.vid_play.video_in.stop_nw_stream", (), {})))



    def _update_player_size(self, *args):
        self.player.size = self.size

    def _update_player_pos(self, *args):
        self.player.pos = self.pos
    
    def split_vid(self, new_name, split=True):
        if self.input_type == "camera":
            new_name = new_name.split("/")
            _dir = "/".join(new_name[:-1]) + "/"
            _filename = new_name[-1][:-3]

            new_file = self.video_in.split_vid(_filename, 
                                               new_dir=_dir,
                                               split=split)
            return new_file   # return file name of video (For sending in SIO)

if __name__ == '__main__':
    # for testing
    from kivy.app import App
    from videoprocessing import VideoProcessing

    if SYS_MACH == ('Linux', 'armv7l'):
        import os
        os.environ['KIVY_GL_BACKEND'] = 'gl'
        import kivy

    class Test(App):
        def build(self):
            return VideoDisplay()

    app = Test()
    app.run()

    """
    NOTES:
    RPI does not work with 'bgr' textures
    """