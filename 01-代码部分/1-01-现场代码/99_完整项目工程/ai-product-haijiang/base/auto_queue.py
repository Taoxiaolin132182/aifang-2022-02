import sys
import time
import queue
from config import config
from . import util
from . import log

'''
@author maoyanwei
能根据负载自动确定maxsize大小的队列
'''
class auto_queue:
    #构造
    def __init__(self, astrName, auInitSize = config.INIT_AUTO_QUEUE_SIZE):
        self.__name = "" if astrName is None else astrName
        self.__queue = queue.Queue(maxsize = auInitSize)
        self.__fLastTick = 0
        self.__uLastFrames = 0
        self.__totalProcess = 0
    #end def

    #析构
    def __del__(self):
        pass
    #end def

    '''
    基本同Queue.put_nowait
    @return 成功放入返回True
    '''
    def put_nowait(self, item):
        return self.put(item, block=False)
    #end def

    '''
    基本同Queue.put
    @return 成功放入返回True
    '''
    def put(self, item, block=True, timeout=None):
        try:
            self.__queue.put(item, block, timeout)
            return True
        except queue.Full as ef:
            #log.debug("auto_queue %s put full" % (self.__name))
            return False
        except Exception as e:
            log.error("auto_queue %s put failed: %s" % (self.__name, e))
            return False
        #end try
    #end def

    #同Queue.get
    def get(self, block=True, timeout=None):
        #先尝试立即获取，以便统计处理性能
        result = self.__get(block = False)
        if not result is None:
            #取到不再继续
            return result
        #end if

        #取不到就按要求再次尝试
        return self.__get(block, timeout)
    #end if

    #同Queue.get
    def __get(self, block=True, timeout=None):
        try:
            if block:
                #阻塞获取，认为之前连续获得的情况不存在了，强制调整大小
                self.__auto_resize(True)
            #end if

            rt = self.__queue.get(block, timeout)
            self.__totalProcess += 1
            if block:
                #阻塞获取不能统计处理性能
                return rt
            #end if

            #非阻塞，统计处理能力
            if self.__fLastTick == 0:
                #这是第一次非阻塞，我们以此作为开始
                self.__fLastTick = time.time()
                self.__uLastFrames = 0
                return rt
            #end if

            #非阻塞，非第一次，计算性能
            self.__uLastFrames += 1
            #调整大小
            self.__auto_resize(False)
            return rt
        except queue.Empty as ee:
            #log.debug("auto_queue %s get empty" % (self.__name))
            return None
        except Exception as e:
            log.error("auto_queue %s get failed: %s" % (self.__name, e))
            return None
        #end try
    #end def

    #设置队列本次最大maxsize
    def set_maxsize(self, maxsize):
        if self.__queue.maxsize < maxsize:
            self.__queue.maxsize = maxsize
        #end if
    #end def

    #统计处理性能，调整大小
    def __auto_resize(self, abForce):
        if abForce:
            #要求强制调整
            iNewMaxSize = self.__uLastFrames + 2
            if self.__queue.maxsize < iNewMaxSize:
                self.__queue.maxsize = iNewMaxSize
                log.info("auto_queue %s force set new maxsize %s" % (self.__name, iNewMaxSize))
            #end if
            # 原有统计信息清掉重来
            self.__fLastTick = 0
        else:
            fTicks = time.time() - self.__fLastTick
            if fTicks < 1.0:
                #统计时间未到
                return
            #end if

            #看看这段时间内处理了多少帧数据，认为这是我们的最大处理能力
            iNewMaxSize = int(self.__uLastFrames / fTicks) + 1
            self.__queue.maxsize = iNewMaxSize
            if (self.__totalProcess >= (self.__uLastFrames * 10)):
                #每10秒左右，打印一次队列最大长度
                log.info("auto_queue %s set new maxsize %s" % (self.__name, iNewMaxSize))
                self.__totalProcess = 0
            #end if

            #for next
            self.__uLastFrames = 0
            self.__fLastTick = time.time()
        #end if
    #end def
#end class
