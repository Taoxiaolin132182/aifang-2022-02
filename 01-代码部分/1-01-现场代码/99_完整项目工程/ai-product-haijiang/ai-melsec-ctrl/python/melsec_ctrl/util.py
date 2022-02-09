import sys
import time
import subprocess
import ctypes
import platform
import traceback
from . import config

'''
记录日志
@param log 日志内容
'''
def addLog(log):
    curTime = time.time()
    timeArray = time.localtime(curTime)
    strTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    print("%s %s" % (strTime, log))
    sys.stdout.flush()
#end of def addLog

'''
安全执行一些工作
@param aoFunc 运行函数
@return 成功执行返回True
'''
def safeWork(aoFunc):
    try:
        aoFunc()
        return True
    except Exception as e:
        exstr = traceback.format_exc()
        print(exstr)
        addLog("safeWork failed:" + str(e))
        return False
#end def

'''
执行并等待一个进程结束
@return 成功获取(退出码, "")，失败返回(None, strErr)
'''
def popen(astrExePath, cwd=None):
    try:
        p = subprocess.Popen(astrExePath, shell=True, cwd=cwd)
        p.wait()
        iResult = ctypes.c_int32(p.returncode).value
        addLog("popen [%s...] result: %d" % (astrExePath[0:50], iResult))
        return (iResult, "")
    except Exception as e:
        strErr = "popen [%s...] failed: %s" % (astrExePath[0:50], str(e))
        addLog(strErr)
        return (None, strErr)
#end def popen

'''
@return 是windows返回True
'''
def isWindows():
    strOsName = platform.system()
    return strOsName == "Windows"
#end def isWindows


