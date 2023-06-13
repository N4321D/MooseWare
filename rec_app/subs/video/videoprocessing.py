"""
By Dmitri Yousef Yengej 2020-07-12

The VideoProcessing Class takes video and processes it

It checks automatically if the picamera package is available and uses 
that for image capturing/saving.

Capturing and recording are running in separate threads. The capture
loop signals to the recorder when an image is ready for post-processing 
and saving.

start_camera(): will start the capturing/recording of images
stop_camera(): stops capturing/recording

recording: Bool> if True the captured images will be saved
fps: Int> Frames per second for capturing/ recording
processing: Bool> if True the captured image will be sent to processing
                    add link to processing method in proc_save method

options: when using Picam as recording interface, annotate can
            be used to set annotations in the recording:
            see:https://picamera.readthedocs.io/en/release-1.13/api_camera.html

annotation_timestamp: set to True to annotate a timestamp

convert_h264_2_mp4(): converts recorded video to mp4 on RPi after recording
                        need gpac (sudo apt-get install gpac)
                        NOTE: very slow!! uncomment to use



RPi camera info 
(see: https://www.raspberrypi.org/documentation/hardware/camera/ and
https://picamera.readthedocs.io/en/release-1.12/fov.html)

The Pi’s camera has a discrete set of input modes. On the V1 camera these are as follows:
# 	Resolution 	Aspect Ratio 	Framerates 	Video 	Image 	FoV 	Binning
1 	1920x1080 	16:9 	        1-30fps 	        x 	  	Partial None
2 	2592x1944 	4:3 	        1-15fps 	        x 	x 	Full 	None
3 	2592x1944 	4:3 	        0.1666-1fps     	x 	x 	Full 	None
4 	1296x972 	4:3 	        1-42fps 	        x 	  	Full 	2x2
5 	1296x730 	16:9 	        1-49fps 	        x 	  	Full 	2x2
6 	640x480 	4:3 	        42.1-60fps 	        x 	  	Full 	4x4
7 	640x480 	4:3 	        60.1-90fps 	        x 	  	Full 	4x4

camera mode: 8Mpx
On the V2 camera, these are:
# 	Resolution 	Aspect Ratio 	Framerates 	Video 	Image 	FoV 	Binning
1 	1920x1080 	16:9 	        0.1-30fps 	x 	  	        Partial None
2 	3280x2464 	4:3 	        0.1-15fps 	x 	    x 	    Full 	None
3 	3280x2464 	4:3 	        0.1-15fps 	x 	    x 	    Full 	None
4 	1640x1232 	4:3 	        0.1-40fps 	x 	  	        Full 	2x2
5 	1640x922 	16:9 	        0.1-40fps 	x 	  	        Full 	2x2
6 	1280x720 	16:9 	        40-90fps 	x 	  	        Partial 2x2
7 	640x480 	4:3 	        40-90fps 	x 	  	        Partial 2x2
NOTE: Framerate takes precedence over resolution (so 800*600@60 -> 640*480@60)
"""

from threading import Thread, Event
import time 

from datetime import datetime

import os

def prnt(*text):
    print("<VIDEO_PROCESSING>: ", *text)

from picamera import PiCamera, Color
from picamera.array import PiRGBArray

class StreamingOutput():
    str_codec = 'h264'
    network = None      # placeholder for network class

    def __init__(self):
        self.frame = None
        self.condition = Event()

    def write(self, buf):
        if self.str_codec == 'MJPEG':
            if not buf.startswith(b'\xff\xd8'):
                return
        else:  
            # send over network:
            if self.network.sending is False or self.network.client is None:
                return
            self.network.send(buf, protocol="UDP")
        self.condition.set()
    
    def read(self):
        if self.condition.is_set():
            if self.str_codec == 'h264':
                pass
                # bytes_out = self.buffer.getvalue()
                # self.buffer.truncate(0)
                # self.buffer.seek(0)

            elif self.str_codec == 'MJPEG':
                bytes_out = self.frame

            self.condition.clear()
            return bytes_out
        


class VideoProcessing():
    img = None                   # last captured image
    img_buffer = []              # buffer to store images for processing/saving
    xy_data = ()                 # last coordinates of animal
    camera = None                # camera hook
    recording = True             # bool if saving or not
    processing = False           # Processess img
    res = (1280, 720)            # dimension in pix of output image SEE NOTES
    fps = 25                     # FPS of sampling
    output_type = 'camera'       # Specifies the video class for the widget
    parent = None                # The widget controlling the recorder
    file_out = 'video'           # fileout name
    file_out_i = 0               # counts fileout
    init_t = 0                   # timer for camera startup
    cam_type = None              # String with camera type
    stream_out = None            # Buffer IO for network streaming
    stream_format = 'h264'

    # picam pars
    options = {'annotate_background': '#000000',  # or None for no background
                  'annotate_foreground': '#ffffff',
                  'annotate_frame_num': False,
                  'annotate_text': 'Preview',
                  'annotate_text_size': 32
                    }
    annotation_timestamp = True
    rec_opts = {'quality': 25,       # (10: best, 40 worst, 20-25 optimal)
                'bitrate': 0, # 800000, # (0 - 25000000 (65e6 for level 4.2)) 0 indicates no bitrate control
                'profile': 'high',   # ("high", "main", "baseline", "constrained") h264 profile
                'level': '4',      # ('4', '4.1', '4.2') h264 level
                }

    def __init__(self, parent=None):
        self.stop_cap_loop = Event()              # capture loop flag
        self.stop_proc_loop = Event()        # save/process loop flag
        self.img_ready_flag = Event()    # image ready for processing 
        self.parent = parent
        self.init_cam()

    def init_cam(self):
        self.init_t = time.time()
        try:
            self.camera = PiCamera()
            self.cam_type = self.check_cam_type()
            self.set_res_fps((*self.res, self.fps))
            for key in self.options:
                if key[-6:] == 'ground':
                    setattr(self.camera, key, 
                            Color(self.options[key]))
                else:
                    setattr(self.camera, key, self.options[key])

            self.stream_out = StreamingOutput()
        except:
            prnt("Picamera not connected")
            self.output_type = "no cam"
                           

    
    def check_cam_type(self):
        # check hardware version
        if self.camera.MAX_RESOLUTION == (2592, 1944):
            return 'V1'
        elif self.camera.MAX_RESOLUTION == (3280, 2464):
            return 'V2'

    def set_res_fps(self, res_fps):
        """
        checks what the best hardware native resolution and FPS is
        (closest to the preferred settings)

        """
        if isinstance(res_fps, str):
            self.camera.resolution = res_fps

        else:
            res_fps = [new or old for new, old
                        in zip(res_fps, (*self.res, self.fps))]
            if res_fps[2] is None:
                res_fps = (*res_fps[:2], self.fps)
            if res_fps[0] is None:
                res_fps = (*self.res, res_fps[2])
                
            if self.cam_type is None:
                *self.res, self.fps = res_fps
                return
            if  (0 < res_fps[0] <=self.camera.MAX_RESOLUTION[0] 
                    and 0 < res_fps[1] <=self.camera.MAX_RESOLUTION[1]
                    and 0 < res_fps[2] <=self.camera.MAX_FRAMERATE):
                self.camera.resolution = res_fps[:2]
                self.camera.framerate =  res_fps[2]

        self.fps = self.camera.framerate[0]
        self.res = self.camera.resolution
        prnt('Resolution: {}  fps:{}'.format(self.res, self.fps))

    def start(self):
        # wait for cam to be ready:
        if (time.time() - self.init_t) < 2:
            time.sleep(2 - (time() - self.init_t))
        # create buffer for captured image:
        self.temp_img = PiRGBArray(self.camera, size=self.res)
        
        # create stream object for OpenCV/ tensorflow output etc:
        self.stream = self.camera.capture_continuous(self.temp_img, 
                                                     format='bgr', 
                                                     use_video_port=True,
                                                     resize=self.res,   # change to resize output
                                                     splitter_port=3)
        # create recorder:
        if self.recording is True:
            path = './temp/'
            os.makedirs(path, exist_ok=True)
            self.camera.start_recording('{}{}_{}.h264'.format(path,
                                                              self.file_out,
                                                              self.file_out_i),
                                        format='h264',
                                        sps_timing=True, # import to have correct FPS with conversion
                                        splitter_port=1, # use port 2 to stream
                                        **self.rec_opts
                                        )
            
        self.stop_cap_loop.clear()
        self.stop_proc_loop.clear()
        self.tr_cap = Thread(target=self.picam_cap_loop)
        self.tr_proc = Thread(target=self.proc_loop)
        self.tr_cap.start()
        self.tr_proc.start()

    
    def stop(self):
        self.stop_cap_loop.set()
        self.stop_proc_loop.set()
        try:
            self.tr_cap.join()
        except AttributeError:
            pass
        try:
            self.tr_proc.join()
        except AttributeError:
            pass

        if self.camera:
            try:
                self.stream.close()
                self.temp_img.close()
                self.camera.stop_recording(splitter_port=1)
                self.camera.stop_recording(splitter_port=3)

            except Exception as e:
                prnt("Error stopping camera", e)


    def start_nw_stream(self):
        # Start Network Stream
        if self.parent:          
            # only run network if there is a parent app with network
            if self.res[1] / self.res[0] < 0.75:
                # 16:9 aspect ration
                _dim = (640, 360)
            else:
                # 4:3 aspect ratio
                _dim = (640, 480)
            self.stream_out.network = self.parent.parent.app.SIO
            if self.stream_format == 'h264':
                self.camera.start_recording(self.stream_out,
                            format='h264',
                            resize=_dim,
                            sps_timing=True, # import to have correct FPS with conversion
                            sei=True,
                            splitter_port=2, 
                            quality=25,       # (10: best, 40 worst, 20-25 optimal)
                            bitrate=0, # (0 - 25000000 (65M for level 4.2)) 0 indicates no bitrate control
                            profile='baseline',   #  DONT CHANGE: BASE LINE IS BETTER FOR STEAMING LATENCY ("high", "main", "baseline", "constrained") h264 profile
                            )
            else:
                self.camera.start_recording(self.stream_out,
                                            format='mjpeg',
                                            resize=_dim,
                                            splitter_port=2,
                                            quality=50)
    
    def stop_nw_stream(self):
        self.camera.stop_recording(splitter_port=2)

    def split_vid(self, new_name, new_dir = None, split=True):
        if not 1 in self.camera._encoders:
            # not recording
            return
        # location and name of last recorded temp file
        path = "./temp/"
        os.makedirs(path, exist_ok=True)
        old_file = '{}{}_{}.h264'.format(path,
                                         self.file_out,
                                         self.file_out_i)
        # location and name of new recorded temp file
        self.file_out_i += 1
        new_file = '{}{}_{}.h264'.format(path,
                                         self.file_out,
                                         self.file_out_i)
        
        # split file:
        try:
            if split:
                self.camera.split_recording(new_file, splitter_port=1)
            # rename and move last recorded temp file:
            if new_dir:
                os.makedirs(new_dir, exist_ok=True)
                new_name = new_dir + new_name + ".h264"
            os.rename(old_file, new_name)
            return new_name
                    
        except Exception as e:
            prnt("Cannot split video: ", e)
        

    def picam_cap_loop(self):
        # TODO: Only use last img ?
        for img in self.stream:
            if self.stop_cap_loop.is_set():
                prnt("Stop Capture Loop")
                return
            # live annotations
            if self.annotation_timestamp is True:
                t = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                self.camera.annotate_text = '{}: {}'.format(t,
                                                            self.options['annotate_text'])
            self.img_buffer.append(img.array)
            # limit buffer size:
            if len(self.img_buffer) > 10:
                del self.img_buffer[0]
                prnt('Image processing buffer full, deleting oldest image')
            
            self.temp_img.truncate(0)
            self.img_ready_flag.set()

    def process_save(self, img, frame_no):
        """
        This method processes and saves the image.
        if a parent class is defined it will push the image
        to the parent class (e.g. for displaying)

        """
        if img is None:
            return
        
        # process
        if self.processing:
            img = self.process_img(img)

    def proc_loop(self):
        frame_no = 0      # counts frame number use to decimate etc

        while not self.stop_proc_loop.is_set(): 
            # wait for new img
            self.img_ready_flag.wait(timeout=1)
            if self.img_ready_flag.is_set():
                self.img_ready_flag.clear()
            
            # process images
            frame_no += 1
            while self.img_buffer:
                self.process_save(self.img_buffer.pop(0), frame_no)

    def process_img(self, img):
        # do processing here
        # to resize use hardware picam resize 
        return img

    def convert_h264_2_mp4(self):
        # coverts h264 to mp4 but is slow
        # system("MP4Box -add {}.h264 out.mp4".format(self.file_out))
        return

    def set_texture(self, *args):
        pass


"""
NOTES:
For streaming see picam doc: write to a bytes object (on unused splitter port)
"""

# TODO: for hardware encoding of existing data see: https://picamera.readthedocs.io/en/release-1.13/api_mmalobj.html
# TODO: use rgba for output to location detection (is faster with resize, see: https://picamera.readthedocs.io/en/release-1.13/fov.html#camera-modes (encondings))