import sys
import time
import signal
import cv2
import numpy
import threading
from config import config
from . import util
from . import log
from . import video_capture

'''
@author maoyanwei
多个video_capture组成的视频采集组
'''
class video_capture_group:
    #构造
    def __init__(self, urls, callback, frame_interval = 0.0):
        self.oCapture = []
        self.callback = callback
        #逐个创建
        for i in range(len(urls)):
            oCapture = video_capture.video_capture(urls[i], frame_interval)
            oCapture.uid = i
            self.oCapture.append(oCapture)
        #end for
    #end def

    #析构
    def __del__(self):
        self.stop()
    #end def

    '''
    启动视频线程
    '''
    def start(self):
        for oCapture in self.oCapture:
            oCapture.start(self.callback)
        #end for
    #end def

    '''
    停止视频线程
    '''
    def stop(self):
        for oCapture in self.oCapture:
            oCapture.stop()
        #end for
    #end def

#end class

