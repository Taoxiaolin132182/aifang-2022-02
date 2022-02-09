import os
import threading
import traceback
from . import log

'''
@author maoyanwei
本类是多个运行线程的组合管理类，只提供基础的启动停止方法，不同于线程池，切勿混淆
'''
class thread_group:
    def __init__(self, name, count, thread_one_loop, *args):
        '''
        初始化线程组
        @param name 线程名前缀
        @param count 线程组内线程数
        @param thread_one_loop 单次循环回调，定义如：thread_one_loop(index, lambda:is_working, arg, ...) -> bool
        @param args 传给thread_one_loop的参数
        构造失败抛出异常
        '''
        self.threads = [None] * count
        self.__name = name
        self.__thread_one_loop = thread_one_loop
        self.__args = args
    #end def

    def __thread_main(self, index):
        '''
        线程入口
        @param index 线程索引
        '''
        strThreadName = self.threads[index].name
        log.info("thread '%s' started" % strThreadName)

        while not self.threads[index] is None:
            try:
                #回调
                if not self.__thread_one_loop(index, lambda: self.threads[index], *self.__args):
                    break
                #end if
            except Exception as e:
                exstr = traceback.format_exc()
                log.error("thread '%s': __thread_one_loop exception, %s" % (strThreadName, exstr))
                log.error("thread '%s': __thread_one_loop failed, %s" % (strThreadName, e))
            #end try
        #end while
        log.info("thread '%s' will exit" % strThreadName)
    #end def

    def start(self):
        '''
        启动线程组
        @return 成功返回True
        '''
        if (len(self.threads) == 0) or (not self.threads[0] is None):
            return False
        #end if

        for i in range(len(self.threads)):
            t = threading.Thread(target = self.__thread_main, name = self.__name + str(i), args = (i,))
            self.threads[i] = t
            t.start()
        #end for
        return True
    #end def

    def stop(self):
        '''
        停止线程组
        '''
        if (len(self.threads) == 0) or (self.threads[0] is None):
            return False
        #end if

        for i in range(len(self.threads)):
            t = self.threads[i]
            self.threads[i] = None
            try:
                t.join()
            except Exception as e:
                strLog = "join Thread '%s' failed: %s" % (t.name, e)
                log.error(strLog)
            finally:
                del t
            #end try
        #end for
    #end def

#end class

