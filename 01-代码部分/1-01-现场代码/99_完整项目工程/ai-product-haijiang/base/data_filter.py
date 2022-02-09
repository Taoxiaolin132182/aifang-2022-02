import sys
import time
import threading
from config import config
from . import util
from . import log
from .auto_queue import auto_queue

s_oLock = threading.RLock() #如需要全局同步时使用

'''
@author maoyanwei
能并行处理数据的流水线，创建例子：
self.__filter = ocr_data_filter().set_next(
                    ai_data_filter().set_next(
                        save_disk_filter().set_next(
                            save_db_filter().set_next(
                                None #标志db是最后一个
                            )
                        )
                    )
                )
'''
class data_filter:
    #构造
    def __init__(self, astrName):
        self.__strName = astrName
        self.__oNext = None #下一个处理过滤对象
        self.__oDoneQueue = auto_queue(astrName) #处理完成后的队列
        self.set_maxsize = self.__oDoneQueue.set_maxsize #设置队列本次最大maxsize
        #处理完成队列线程
        self.__oDoneThread = None
    #end def

    #析构
    def __del__(self):
        self.stop()
    #end def

    @property
    def name(self):
        return self.__strName
    #end def

    '''
    完成队列处理
    '''
    def __processDoneQueueMain(self):
        log.info("thread %s started" % self.__strName)
        time.sleep(0.01)

        while not self.__oDoneThread is None:
            context = self.__oDoneQueue.get(block = True, timeout = 1)
            if context is None:
                #没有等待处理的数据
                continue
            #end if

            try:
                #总是需要交给下一个处理
                if not self.__oNext.run(context):
                    #TODO: 处理失败与我有关吗？
                    pass
                #end if
            except Exception as e:
                strLog = "%s self.__oNext.run failed: %s" % (self.__strName, e)
                log.error(strLog)
                context.log = strLog
            #end try

        #end while

        log.info("thread %s will exit" % self.__strName)
    #end def

    #执行，成功处理返回True
    def run(self, aoContext):
        if aoContext is None:
            log.error("%s filter run failed: aoContext is None" %  self.__strName)
            return False
        #end def
        strResultField = "%s_result" % self.__strName
        aoContext.__dict__[strResultField] = False
        fBegin = time.time()
        aoContext.__dict__["begin_%s_time" % self.__strName] = fBegin
        try:
            #记录成功失败
            aoContext.__dict__[strResultField] = self.filter(aoContext)
            fEnd = time.time()
        except Exception as e:
            fEnd = time.time()
            strLog = "filter %s run failed: %s" % (self.__strName, e)
            log.error(strLog)
            if len(aoContext.log) > 0: aoContext.log += "; " + strLog
            else: aoContext.log = strLog
        #end try

        #记录时间
        aoContext.__dict__["end_%s_time" % self.__strName] = fEnd
        #看看这个步骤花了多少时间
        if config.LOG_FILTER_TIME:
            log.info("filter %s use time %ssec" % (self.__strName, fEnd - fBegin))
        #end if

        #若有后继，则放入本次处理完队列
        if not self.__oNext is None:
            while not self.__oDoneQueue.put(aoContext, block = True, timeout = 1):
                if self.__oDoneThread is None:
                    #若要求停止，则不再继续尝试
                    break
                #end if
            #end while
        #end if

        return aoContext.__dict__[strResultField]
    #end def

    #启动处理
    def start(self):
        if not self.__oNext is None:
            #先启动后继
            self.__oNext.start()
            if self.__oDoneThread is None:
                #需要处理完成队列
                self.__oDoneThread = threading.Thread(target = self.__processDoneQueueMain,
                                                      name = self.__strName + "_done")
                self.__oDoneThread.start()
            #end if
        #end if
    #end def

    #停止处理
    def stop(self):
        if not self.__oDoneThread is None:
            tmp = self.__oDoneThread
            self.__oDoneThread = None
            try:
                tmp.join()
            except Exception as e:
                strLog = "join done thread %s failed: %s" % (self.__strName, e)
                log.error(strLog)
                time.sleep(1)
            #end try
            del tmp
        #end if
        if not self.__oNext is None:
            self.__oNext.stop()
        #end if
    #end if

    #设置下一个处理者
    def set_next(self, aoNext):
        self.__oNext = aoNext
        return self
    #end def

    #派生类需要重写过滤动作，不要接异常，出错了把异常抛出去
    def filter(self, aoContext):
        log.warning("data_filter.filter need override")
        return False
    #end def

    #若为源头filter，需要重写，提供返回的上下文
    def get_next_context(self):
        log.warning("data_filter.filter get_next_context override")
        return None
    #end def

    '''
    获取下一个context，并分发处理
    @return 处理的context数量
    '''
    def dispatch_next_context(self):
        context = self.get_next_context()
        if context is None:
            return 0
        #end if

        #启动处理流程，返回成功处理任务数量
        return 1 if self.run(context) else 0
    #end def

#end class


