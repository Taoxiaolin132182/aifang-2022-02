import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
import time
#添加包路径
START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, "..",".."))
import threading
sys.path.append(os.path.join(START_PY_PATH, ".."))
from config import config
from . import util

'''
@author maoyanwei
日志模块
'''

s_oLock = None
s_oLog = None

'''
初始化log配置
'''
def init_log(astrLogName):
    global s_oLog
    global s_oLock
    if s_oLog is None:
        #FORMAT = ('%(asctime)-15s %(threadName)-15s'
        #        ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
        FORMAT = ('%(asctime)-15s %(threadName)-15s %(levelname)-8s %(message)s')
        useLevel = logging.DEBUG if config.DEBUG_MODE else logging.INFO
        # logging.basicConfig(level = useLevel, 
        #                     format = FORMAT)
        # oRoot = logging.getLogger()
        #oRoot.setLevel(useLevel)
        s_oLog = logging.getLogger(astrLogName)
        s_oLog.setLevel(useLevel)

        #release生成当前日志文件名
        #timeArray = time.localtime(time.time())
        #strTime = time.strftime("%Y-%m-%d", timeArray)
        #strLogFilePath = os.path.join(config.LOG_PATH, astrLogName + "_" + strTime + ".log")
        #print("strLogFilePath = " + strLogFilePath)
        #handler = logging.StreamHandler() if config.DEBUG_MODE else logging.FileHandler(strLogFilePath)

        fmt = logging.Formatter(FORMAT)
        #调试时设置输出控制台，release直接输出到日志
        if config.DEBUG_MODE:
            handler = logging.StreamHandler()
        else:
            strLogFilePath = os.path.join(config.LOG_PATH, astrLogName + ".log")
            handler = TimedRotatingFileHandler(strLogFilePath, 
                                               when = 'midnight', interval = 1, backupCount = 7, encoding = 'utf-8')
            handler.suffix = "%Y-%m-%d.log"
        #end if
        handler.setLevel(useLevel)
        handler.setFormatter(fmt)
        s_oLog.addHandler(handler)

        s_oLock = threading.RLock()
        #done
    #end if
#end def

'''
删除旧的日志
执行了删除动作返回True
'''
def del_old_log():
    strLogPath = ""
    fLogDays = 14
    try:
        #为了防止误删除，我们要求必须配置
        strLogPath = config.LOG_PATH
        fLogDays = config.LOG_DAYS
    except Exception as e:
        error(str(e))
        return False
    #end try

    return util.delOldFilesWithDays(strLogPath, fLogDays)
#end def

"""
Log a message with severity 'CRITICAL' on the root logger
"""
def critical(msg, *args, **kwargs):
    global s_oLock
    global s_oLog
    if s_oLog is None: return
    with s_oLock:
        s_oLog.critical(msg, *args, **kwargs)
    # end with
# end def

"""
Log a message with severity 'ERROR' on the root logger
"""
def error(msg, *args, **kwargs):
    global s_oLock
    global s_oLog
    if s_oLog is None: return
    with s_oLock:
        s_oLog.error(msg, *args, **kwargs)
    # end with
# end def

"""
Log a message with severity 'WARNING' on the root logger
"""
def warning(msg, *args, **kwargs):
    global s_oLock
    global s_oLog
    if s_oLog is None: return
    with s_oLock:
        s_oLog.warning(msg, *args, **kwargs)
    # end with
# end def

"""
Log a message with severity 'INFO' on the root logger
"""
def info(msg, *args, **kwargs):
    global s_oLock
    global s_oLog
    if s_oLog is None: return
    with s_oLock:
        s_oLog.info(msg, *args, **kwargs)
    # end with
# end def

"""
Log a message with severity 'DEBUG' on the root logger
"""
def debug(msg, *args, **kwargs):
    global s_oLock
    global s_oLog
    if s_oLog is None: return
    with s_oLock:
        s_oLog.debug(msg, *args, **kwargs)
    # end with
# end def

