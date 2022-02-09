import os
import sys
import time
import signal
import traceback
from config import config
from . import util
from . import log

'''
@author maoyanwei
全局服务类
Windows下调试，用 Ctrl+C 柔和结束
Linux下前台作业，同样用 Ctrl+C 柔和结束
Linux下后台作业，用 kill -15 柔和结束
Linux下程序挂掉会自己再拉起来
使用时要求传递一个真正提供服务的类名
'''
class fork_service:
    #唯一实例
    g_oInstance = None
    g_pid = 0

    '''
    构造
    @param astrServiceName 服务名字
    @param aoImpl 服务实现类，不是实例
    '''
    def __init__(self, astrServiceName, aoImplClass):
        super().__init__()
        self.__strServiceName = astrServiceName

        #信号处理
        if not util.isWindows():
            signal.signal(signal.SIGHUP, signal.SIG_IGN)
            signal.signal(signal.SIGQUIT, signal.SIG_IGN)
        #end if
        signal.signal(signal.SIGTERM, fork_service.sig_handler)
        signal.signal(signal.SIGINT, fork_service.sig_handler)

        fork_service.g_oInstance = self
        try:
            while not fork_service.g_oInstance is None:
                #Windows没有fork，只用来调试逻辑吧
                pid = 0 if util.isWindows() else os.fork()
                if pid == 0:
                    if not util.isWindows():
                        signal.signal(signal.SIGINT, signal.SIG_IGN)
                    #end if
                    self.__init_server(aoImplClass)
                    break
                else:
                    #监控异常
                    fork_service.g_pid = pid
                    log.info("server pid = %s" % pid)
                    while True:
                        try:
                            (wpid, iExitCode) = os.waitpid(pid, 0)
                            log.info("server %s exit code:%s" % (wpid, iExitCode))
                            break
                        except Exception as e:
                            log.error("waitpid failed: %s" % (e))
                        #end try
                    #end while
                #end if
            #end while
            if pid != 0:
                log.info("monitor server exit")
                os._exit(0)
            #end if
        except OSError as oe:
            log.error("%s init os failed, %s" % (self.__strServiceName, oe))
            os._exit(127)
        except Exception as e:
            log.error("%s init failed, %s" % (self.__strServiceName, e))
            exstr = traceback.format_exc()
            log.error("=========== init failed ===========\n%s\n\n" % exstr)
            os._exit(127)
        #end try
    #end def

    #析构
    def __del__(self):
        self.stop()
    #end def

    #内部用初始化服务
    def __init_server(self, aoImplClass):
        #创建实现
        try:
            self.__impl = aoImplClass()
            self.__isServiceRunning = False
            if self.__impl is None:
                raise Exception("fork_service impl must not be None")
            #end if
            if id(fork_service.g_oInstance) != id(self):
                raise Exception("fork_service must be single")
            #end if
        except Exception as e:
            exstr = traceback.format_exc()
            log.error("=========== __init_server failed ===========\n%s\n\n" % exstr)
            log.error("%s __init_server failed, %s" % (self.__strServiceName, e))
            os._exit(127)
    #end def

    #@return 服务名
    def service_name(self):
        return self.__strServiceName
    #end def

    #信号处理
    def sig_handler(signum, frame):
        #可能不安全，release不要
        log.debug("sig_handler for %s" % signum)

        if fork_service.g_oInstance is None:
            os._exit(0)
        #end if
        fork_service.g_oInstance.stop()
        fork_service.g_oInstance = None

        if fork_service.g_pid != 0:
            os.kill(fork_service.g_pid, signal.SIGTERM)
            fork_service.g_pid = 0
        #end if
    #end def

    #标记服务需要停止
    def stop(self):
        self.__isServiceRunning = False
    #end def

    '''
    服务启动
    '''
    def start(self):
        if self.__isServiceRunning:
            return
        #end if
        self.__isServiceRunning = True

        #TODO: 此处需要插入编译器atomic_signal_fence确保绝对安全，python不知道怎么玩，以后再说
        if fork_service.g_oInstance is None:
            log.error("fork_service.g_oInstance is None")
            os._exit(127)
            return
        #end if

        self.__impl.start()
        log.info("%s start" % self.__strServiceName)

        #开始服务
        while self.__isServiceRunning:
            #执行处理任务
            try:
                iProcessCount = self.__impl.run()
            except Exception as e:
                log.error("%s run failed, %s" % (self.__strServiceName, e))
                #TODO: 暂时等一会重试
                time.sleep(1)
                continue
            #end try

            if iProcessCount == 0:
                #什么都没有干成功，休息下
                time.sleep(0.01)
            elif iProcessCount < 0:
                log.error("%s run failed, iProcessCount = %s" % (self.__strServiceName, iProcessCount))
                break
            #end if
        #end of while
        self.__isServiceRunning = False
        self.__impl.stop()
        log.info("%s exit" % self.__strServiceName)
        time.sleep(0.5)
        os._exit(0)
    #end def run

#end class


