import sys
import time
import signal
import cv2
import numpy
import threading
from config import config
from . import util
from . import log

'''
@author maoyanwei
视频采集，只支持文件或者标准协议的视频流
'''
class video_capture:
    #构造
    def __init__(self, url, frame_interval = 0.0):
        self.__oVideoCapture = None #视频捕获
        self.__oVideoThread = None #视频线程
        self.url = url
        self.frame_interval = frame_interval
        self.callback = None
    #end def

    #析构
    def __del__(self):
        self.stop()
    #end def

    #打开视频流
    def open_video(self):
        self.close_video()
        try:
            self.__oVideoCapture = cv2.VideoCapture(self.url)
            if not self.__oVideoCapture.isOpened():
                self.close_video()
                raise Exception("not isOpened()")
            #end if
            log.info("open_video(%s) OK" % (self.url))
            return True
        except Exception as e:
            log.error("open_video(%s) failed, %s" % (self.url, e))
        #end try
        return False
    #end def

    #关闭视频流
    def close_video(self):
        if not (self.__oVideoCapture is None):
            try:
                self.__oVideoCapture.release()
            except Exception as e:
                log.error("close_video failed, %s" % (e))
            finally:
                self.__oVideoCapture = None
            #end try
        #end if
    #end def

    #读取一帧视频，失败返回None，可以单独调用
    def read_video(self):
        if self.__oVideoCapture is None:
            #没打开的情况重新打开
            if not self.open_video():
                #仍然没有打开摄像头，报告失败
                #log.error("read_video failed, video not opened")
                return None
            #end if
        #end if

        try:
            for i in range(30):
                #尝试多次
                ret, img = self.__oVideoCapture.read()
                if ret:
                    #成功了马上返回
                    return img
                #end if
                #等下次尝试
            #end for
            #到这里就是不成功，关闭，等待下次重新打开
            self.close_video()
            raise Exception("maybe camera has been disconnected")
            return None
        except Exception as e:
            log.error("read_video(%s) failed, %s" % (self.url, e))
            return None
        #end try
    #end def

    '''
    视频采集线程
    '''
    def __video_capture_main(self):
        log.info("__video_capture_main started")
        time.sleep(0.01)
        fLastTick = time.time()

        while not self.__oVideoThread is None:
            img = self.read_video()
            if img is None:
                #读不到了，等一会再试
                log.error("read_video(%s) None" % (self.url))
                time.sleep(1.0)
                continue
            #end if

            curTick = time.time() #先保存图片的获取时间戳
            #TODO: opencv拿不到帧的pts，这里处理不大好，以后改吧
            if curTick - fLastTick < self.frame_interval:
                #本帧与上一帧间隔过近，跳过
                continue
            #end if
            fLastTick = curTick
            try:
                #回调
                if not self.callback is None: self.callback(self, img)
            except Exception as e:
                log.error("__video_capture_main: callback failed, %s" % (e))
            #end try
        #end while
        log.info("__video_capture_main will exit")
    #end def

    '''
    启动视频线程
    '''
    def start(self, callback):
        self.callback = callback
        if self.__oVideoThread is None:
            self.__oVideoThread = threading.Thread(target = self.__video_capture_main,
                                                    name = "VideoThread")
            self.__oVideoThread.start()
        #end if
    #end def

    '''
    停止视频线程
    '''
    def stop(self):
        #停止视频捕获线程
        if not self.__oVideoThread is None:
            tmp = self.__oVideoThread
            self.__oVideoThread = None
            try:
                tmp.join()
            except Exception as e:
                strLog = "join VideoThread failed: %s" % (e)
                log.error(strLog)
                time.sleep(1)
            #end try
            del tmp
        #end if
        
        #再关视频cap
        self.close_video()
    #end def

#end class

