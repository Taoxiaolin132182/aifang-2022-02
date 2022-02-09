import os
import sys
import time
import subprocess
import ctypes
import platform
import psutil
import shutil
import traceback
from pathlib import Path
# #添加包路径
# START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
# sys.path.append(os.path.join(START_PY_PATH, ".."))
from config import config

'''
@author maoyanwei
一些工具函数
'''


'''
字符串转数字，失败返回default值
@param str转换的字符串
@param default 失败返回值
@param base 默认十进制
'''
def stol(strValue, default = None, base = 10):
    try:
        return int(strValue, base)
    except Exception as e:
        return default
#end def

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


'''
获取系统编译架构
@return 返回x86_64，aarch64等架构字符串
'''
def machineType():
    try:
        if isWindows():
            #假定win都是x64
            return "x86_64"
        #end if
        return os.uname()[4]
    except Exception as e:
        addLog("machine: " + str(e))
        return ""
#end def

'''
@return 若系统编译架构为X86_64，则返回True
'''
def isX86_64Machine():
    return "x86_64" in machineType()
#end def

'''
返回磁盘使用空间百分比
@return 磁盘使用空间百分比0-100，失败返回-1
'''
def getDiskUsagePercent(astrDir):
    try:
        return psutil.disk_usage(astrDir).percent
    except Exception as e:
        exstr = traceback.format_exc()
        print(exstr)
        addLog("getDiskUsagePercent error: %s" % e)
        return -1
    #end try
#end def

'''
删除指定路径
@param astrPathName 需要删除的指定路径
@return 成功返回True
'''
def delPathName(astrPathName):
    try:
        oPath = Path(astrPathName)
        if oPath.is_dir():
            try:
                shutil.rmtree(astrPathName)
            except Exception as e0:
                shutil.rmtree(astrPathName)
            #end try
            return True
        #end if

        os.remove(astrPathName)
        return True

    except Exception as e:
        addLog("delPathName error: %s" % e)
        return False
    #end try
#end def

'''
删除n天前的文件
@param astrDelDir 删除文件的目录
@param auDeleteDays 删除auDeleteDays天前的
@return 执行了删除动作返回True
'''
def delOldFilesWithDays(astrDelDir, auDeleteDays):
    bResult = False
    try:
        fCurTime = time.time()
        fDiffSeconds = auDeleteDays * 24 * 3600 #天数换算为妙

        oDelPath = Path(astrDelDir)
        for oChild in oDelPath.iterdir():
            fMTimeLen = fCurTime - oChild.stat().st_mtime
            if fMTimeLen > fDiffSeconds:
                strPathName = oChild.as_posix()
                if delPathName(strPathName):
                    bResult = True
                    #addLog("delOldFilesWithDays: delete '%s' OK" % strPathName)
                else:
                    addLog("delOldFilesWithDays: delete '%s' failed" % strPathName)
                #end if
            #end if
        #end for
    except Exception as e:
        addLog("delOldFilesWithDays error: %s" % e)
    #end try

    return bResult
#end def

'''
当astrDelDir所在磁盘剩余空间百分比不足auLimit1时，
删除astrDelDir目录中最早的文件，确保有auLimit2的剩余空间
@param astrDelDir 删除文件的目录
@param auLimit1 看上面的解释
@param auLimit2 看上面的解释
@param abDelDir 是否需要删除空目录
@return 执行了删除动作返回True
'''
def delOldFilesWithDiskFreeLimit(astrDelDir, auLimit1, auLimit2, abDelDir = False):
    bResult = False
    try:
        if not abDelDir:
            #最高层按照auLimit1判断
            if getDiskUsagePercent(astrDelDir) < 100 - auLimit1:
                #当前空间满足要求了，不需要删除
                return bResult
            #end if
        #end if

        curList = [] #保存当前目录列表
        #先统计指定目录下的文件和目录信息
        oDelPath = Path(astrDelDir)
        for oChild in oDelPath.iterdir():
            fTime = oChild.stat().st_mtime
            strPathName = oChild.as_posix()
            oPath = Path(strPathName)
            curList.append((fTime, strPathName, oPath.is_dir()))
            del oPath
        #end for
        if len(curList) == 0:
            #目录是空的
            if abDelDir:
                #需要删除空目录
                delPathName(astrDelDir)
            #end if
            return False #没有删除文件
        #end if

        #按时间排序，最小的在最前面
        curList.sort(key = lambda x:x[0], reverse = False)
        
        for item in curList:
            #for debug
            #print(item)
            if item[2]:
                #print("enter dir:", item[1])
                #是目录，我们继续递归进去找，由于是子目录，故可以删除之
                if delOldFilesWithDiskFreeLimit(item[1], auLimit1, auLimit2, True):
                    bResult = True
                    if getDiskUsagePercent(astrDelDir) <= 100 - auLimit2:
                        #当前空间满足要求了，可以提前结束删除过程
                        return bResult
                    #end if
                #end if
                #print("exit dir:", item[1])
            else:
                #是文件，直接删掉
                if delPathName(item[1]):
                    bResult = True
                    if getDiskUsagePercent(astrDelDir) <= 100 - auLimit2:
                        #当前空间满足要求了，可以提前结束删除过程
                        return bResult
                    #end if
                else:
                    addLog("delOldFilesWithDiskFreeLimit: delete '%s' failed" % item[1])
                #end if
            #end if
        #end for

    except Exception as e:
        addLog("delOldFilesWithDiskFreeLimit error: %s" % e)
    #end try

    return bResult
#end def
