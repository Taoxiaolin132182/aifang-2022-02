import sys
import time
import threading
from . import log
from . import util
from . import db_mgr
from config import config

'''
@author maoyanwei
timer_thread类用于执行多个定时任务的线程，所有任务在一个线程中运行。
simple_task_thread基于timer_thread实现了一些常规定时任务，如删除日志，删除存储图片，删除过时数据库记录。
！！！本模块所有类本身非线程安全！！！
'''


class timer_thread(threading.Thread):
    '''
    用于执行多个定时任务的线程，所有任务在一个线程中运行
    '''

    def __init__(self, name):
        '''
        构造
        @param name 线程名
        '''

        super().__init__(target = self.__timer_thread_main, name = name)
        self.__bWork = False #运行标识
        self.__oTasks = [] #任务
    #end def

    def add_task(self, interval, task_function):
        '''
        添加定时任务
        @param interval 定时间隔（浮点秒数）
        @param task_function 到点执行的任务，任意可调用对象
        @return 返回任务id
        '''
        #添加三元组[任务间隔，任务回调，最近执行时间戳]
        self.__oTasks.append([interval, task_function, 0])
        return len(self.__oTasks)
    #end def

    def start(self):
        '''
        启动任务线程
        '''

        try:
            if self.__bWork:
                return
            #end if
            self.__bWork = True
            super().start()
        except Exception as e:
            self.__bWork = False
            log.error("timer_thread.start failed, %s" % e)
        #end try
    #end def

    def join(self, timeout=None):
        '''
        停止任务处理，等待线程结束
        '''

        self.__bWork = False
        try:
            super().join(timeout)
        except Exception as e:
            pass
        #end try
    #end def

    def __timer_thread_main(self):
        '''
        线程入口
        '''

        log.info("timer_thread[%s] started" % self.name)
        while self.__bWork:
            try:
                time.sleep(0.05)
                for oTask in self.__oTasks:
                    try:
                        #三元组[任务间隔，任务回调，最近执行时间戳]
                        interval, callback, last_tick = oTask
                        if time.time() - last_tick >= interval:
                            #到点执行任务
                            callback()
                            #成功执行，更新任务时间
                            oTask[2] = time.time()
                        #end if
                    except Exception as e:
                        log.error("timer_thread[%s] run task error: %s" % (self.name, e))
                    #end try
                #end for
            except Exception as loopException:
                log.error("timer_thread[%s] loop error: %s" % (self.name, loopException))
            #end try
        #end while
        log.info("timer_thread[%s] will exit" % self.name)
    #end def

#end class timer_thread


class simple_task_thread(timer_thread):
    '''
    已实现下列常规定时任务的timer_thread线程：
    1、定时删除日志：需要配置：config.LOG_PATH，config.LOG_DAYS
    2、定时删除磁盘上的图片，需要配置：config.DISK_SAVE_PATH，config.DISK_FREE_LIMIT1, config.DISK_FREE_LIMIT2
    3、定时删除过时数据库记录，需要配置：config.DB_CONFIG，config.CHECK_DB_CONFIG，
                                      config.LIMIT_DB_RECORD_NUM_1，LIMIT_DB_RECORD_NUM_2
    '''

    def __init__(self, name):
        '''
        构造
        @param name 线程名
        '''

        super().__init__(name = name)

        #磁盘检查间隔
        DISK_CHECK_INTERVAL = 10 if config.DEBUG_MODE else 60 * 2
        self.add_task(DISK_CHECK_INTERVAL, self._checkDiskTask)
        log.info("simple_task_thread add_task: _checkDiskTask, %ss" % DISK_CHECK_INTERVAL)

        #日志删除检查间隔
        LOG_CHECK_INTERVAL = 10 if config.DEBUG_MODE else 60 * 10
        self.add_task(LOG_CHECK_INTERVAL, self._checkLogTask)
        log.info("simple_task_thread add_task: _checkLogTask, %ss" % LOG_CHECK_INTERVAL)

        try:
            #检查是否有DB删除需求
            db_config = config.DB_CONFIG
            strDbName = db_config["db"]
            strTableNames = config.CHECK_DB_CONFIG["tables"]
            strKeyNames = config.CHECK_DB_CONFIG["keys"]

            #db任务检查间隔
            DB_CHECK_INTERVAL = 10 if config.DEBUG_MODE else 60 * 15
            self.add_task(DB_CHECK_INTERVAL, self._checkDBTask)
            log.info("simple_task_thread add_task: _checkDBTask, %ss" % DB_CHECK_INTERVAL)

        except Exception as e:
            #没有配置，不处理
            log.info("simple_task_thread: ignore default db task")
        #end try

    #end def

    def _checkDiskTask(self):
        '''
        检查磁盘任务
        '''

        try:
            curUsagePercent = util.getDiskUsagePercent(config.DISK_SAVE_PATH)
            if curUsagePercent < 0:
                raise Exception("getDiskUsagePercent failed")
            #end if

            if curUsagePercent > (100 - config.DISK_FREE_LIMIT1):
                #当前使用大于指定百分比，需要删除
                log.info(("_checkDiskTask: need to delete, "
                         "disk usage:%s%%, config.DISK_FREE_LIMIT1:%s%%") % (curUsagePercent, config.DISK_FREE_LIMIT1))
                bResult = util.delOldFilesWithDiskFreeLimit(config.DISK_SAVE_PATH, 
                                                            config.DISK_FREE_LIMIT1, config.DISK_FREE_LIMIT2)
                if bResult: log.info("_checkDiskTask: image file deleted")
                else: log.info("_checkDiskTask: NO image file deleted")
            else:
                #不需要删除
                log.debug("_checkDiskTask: no need to delete file")
            #end if

        except Exception as e:
            strLog = "_checkDiskTask failed: %s" % (e)
            log.error(strLog)
        #end try
    #end def

    def _checkLogTask(self):
        '''
        检查log任务
        '''

        try:
            if log.del_old_log():
                #执行过删除动作，则记录下
                log.info("_checkLogTask: old log deleted")
            else:
                log.debug("_checkLogTask: no old log")
            #end if
        except Exception as e:
            strLog = "_checkLogTask failed: %s" % (e)
            log.error(strLog)
        #end try
    #end def

    def _checkDBTask(self):
        '''
        检查db任务
        '''

        try:
            db_config = config.DB_CONFIG
            strDbName = db_config["db"]
            strTableNames = config.CHECK_DB_CONFIG["tables"]
            strKeyNames = config.CHECK_DB_CONFIG["keys"]
        except Exception as ecfg:
            #没有配置，不处理
            log.debug("simple_task_thread: ignore default db task")
            return
        #end try

        try:
            oConn, strErr = db_mgr.connect_mysql(db_config, True)
            if oConn is None:
                raise Exception("connect_mysql failed: %s" % strErr)
            #end if

            iDelRows, strErr = db_mgr.delete_old_record(oConn, strDbName, strTableNames, strKeyNames)
            if len(strErr) > 0:
                raise Exception("delete_old_record: " + strErr)
            #end if
            
            #成功记录下删除条数
            log.info("_checkDBTask delete rows: %s" % str(iDelRows))

        except Exception as e:
            strLog = "_checkDBTask failed: %s" % (e)
            log.error(strLog)
        finally:
            util.safeWork(lambda: None if oConn is None else oConn.close())
        #end try

    #end def

#end class simple_task_thread