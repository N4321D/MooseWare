#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
This class decodes raw H264 bytes with gstreamer

use H264Decoder.start() to start converting

Bytes are send with the H264Decoder.write function

NOTES:
Basic tutorial 12: Streaming
https://gstreamer.freedesktop.org/documentation/tutorials/basic/streaming.html


for output sinks see:
    https://gstreamer.freedesktop.org/documentation/tutorials/basic/platform-specific-elements.html?gi-language=c

"""

# create logger
try:
    from subs.log import create_logger
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None: 
                f = lambda *x: print("GSTREAMER DECODER: ", *x)  # change messenger in whatever script you are importing
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()

def log(message, level="info"):
    getattr(logger, level)("GSTREAMER DECODER: {}".format(message))  # change RECORDER SAVER IN CLASS NAME



import gi
import threading as tr

gi.require_version('Gst', '1.0')

from gi.repository import Gst, GLib



class CustomData:
    is_live = None
    pipeline = None
    main_loop = None


class H264Decoder:
    incoming = None               # alias for write so that it compatible with other decoders
    running = False               # decoder ready for data or not
    img = b''                     # decoded raw image in bytes
    fps = 25
    res = (640, 480)
    output_type = 'H264'         # specifies output type for widget
    tr = None                    # recording Thread 

    def start(self, *args):
        Gst.init(None)
        Gst.debug_set_active(True)
        Gst.debug_set_default_threshold(1)

        self.data = CustomData()
        cmd = ("appsrc name=source ! h264parse name=parser ! queue name=queue ! "  # rtpjitterbuffer mode=0 ! rtph264depay ! 
               "avdec_h264 ! videorate ! "
               "video/x-raw,maxrate=24/1, average-period=100, skip-to-first=true !"
               "autovideosink name=sink")   # NB SPACES BETWEEN !'
        self.data.pipeline = Gst.parse_launch(cmd)
        bus = self.data.pipeline.get_bus()

        # create hooks
        self.source = self.data.pipeline.get_by_name('source')
        self.parser = self.data.pipeline.get_by_name("parser")
        self.queue = self.data.pipeline.get_by_name('queue')
    
        # set properties:
        self.source.set_property('max-bytes', 10000000)
        self.source.set_property('stream-type', 'stream')  # https://gstreamer.freedesktop.org/documentation/app/appsrc.html?gi-language=python
        self.source.set_property('format', "GST_FORMAT_TIME")
        self.source.set_property('is-live', True)
        self.parser.set_property("config-interval",-1) 
        self.queue.set_property("max-size-time", int(1e9))  # max queue size in ns
        self.queue.set_property("leaky", 1)  # where to leak

        ret = self.data.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            log('Unable to set the pipeline to the playing state.', "error")

        elif ret == Gst.StateChangeReturn.NO_PREROLL:
            self.data.is_live = True

        self.data.main_loop = GLib.MainLoop.new(None, False)

        bus.add_signal_watch()
        bus.connect('message', self.cb_message, self.data)

        # start loop
        self.tr = tr.Thread(target=self.data.main_loop.run)
        self.tr.start()
        self.running = True
    
    def stop(self):
        self.running = False
        self.source.emit("end-of-stream")
        self.data.pipeline.set_state(Gst.State.NULL)
        self.data.main_loop.quit()
        self.tr.join()

    def read(self):
        return self.img
    
    def write(self, data: bytes):
        # Converts bytes to Gst.Buffer
        if data and self.running:
            self.source.emit("push-buffer", 
                             Gst.Buffer.new_wrapped(data))

    def cb_message(self, bus, msg, data):
        t = msg.type

        if t == Gst.MessageType.ERROR:
            err, debug = msg.parse_error()
            print("ERROR: ", err)
            return

        if t == Gst.MessageType.EOS:
            # end-of-stream
            self.data.pipeline.set_state(Gst.State.READY)
            self.data.main_loop.quit()
            return

        if t == Gst.MessageType.BUFFERING:
            persent = 0

            # If the stream is live, we do not care about buffering.
            if self.data.is_live:
                return

            persent = msg.parse_buffering()
            log('Buffering {0}%'.format(persent), "info")

            if persent < 100:
                self.data.pipeline.set_state(Gst.State.PAUSED)
            else:
                self.data.pipeline.set_state(Gst.State.PLAYING)
            return

        if t == Gst.MessageType.CLOCK_LOST:
            self.data.pipeline.set_state(Gst.State.PAUSED)
            self.data.pipeline.set_state(Gst.State.PLAYING)
            return

    # dummy functions to make decoder compatible with others
    def set_res_fps(self, *args):
        return
    
    def start_stop_preview(self, *args):
        return

if __name__ == "__main__":
    # read file
    import io

    vid = io.BytesIO()
    with open("../testing/out_SPS_SEI.h264", 'rb') as file:
        vid.write(file.read())

    vid.seek(0)

    from threading import Thread
    import time
    m = H264Decoder()
    m.start()

    print("writing data")
    for i in range(100000):
        buff = vid.read(1000)
        if i % 300 == 0:
            # simulate network issues
            # print("skipping package")
            time.sleep(0.1)
        else:
            m.write(buff)
