import os
import sys
import time
import pymysql
import subprocess
import ctypes
import platform
import traceback
import psutil
import shutil
from pathlib import Path
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
连接数据库
@param aoConfig 连接参数
@return 成功返回连接，失败返回None
'''
def connectMysql(aoConfig, abNeedErr = False):
    if aoConfig is None:
        strErr = "connectMysql failed: config is NULL"
        addLog(strErr)
        return None if not abNeedErr else (None, strErr)

    try:
        oConn = pymysql.connect(**aoConfig)

        #确保默认是自动提交
        oConn.autocommit(True)

        return oConn if not abNeedErr else (oConn, "")
    except Exception as e:
        strErr = str(e)
        addLog("connectMysql failed:" + strErr)
        return None if not abNeedErr else (None, strErr)
#end of connectMysql

'''
连接数据库
@param astrHostDomain host
@return 成功返回连接，失败返回None
'''
def connectMysqlWithHostDomain(astrHostDomain, abNeedErr = False):
    oConfig = config.DB_HOST_TO_CONFIG.get(astrHostDomain, None)
    if oConfig is None:
        strErr = "connectMysqlWithHostDomain failed: %s config is NULL" % astrHostDomain
        addLog(strErr)
        return None if not abNeedErr else (None, strErr)
    #end if

    return connectMysql(oConfig, abNeedErr)
#end def connectMysqlWithHostDomain

'''
指定连接上执行sql
@param aoConn 数据库连接
@param astrSql sql语句
@param aoArgs 可选参数
@param abNeedPing 执行前先测试服务可用性
@return 成功返回tuple(影响条数, 结果集)，失败返回(-1, tuple())
'''
def executeSql(aoConn, astrSql, aoArgs = None, abNeedPing = True):
    
    if abNeedPing:
        (bIsOk, strErr) = checkMysqlConnection(aoConn)
        if not bIsOk:
            addLog("executeSql err: check mysql failed, " + str(strErr))
            return (-9999, tuple())
        #end if
    #end if
    
    oCursor = None
    try:
        oCursor = aoConn.cursor()
        iResult = oCursor.execute(astrSql, aoArgs)
        if iResult < 1: 
            return (iResult, tuple())
        #end if

        oRecords = oCursor.fetchall()
        return (iResult, oRecords)

    except Exception as e:
        addLog("executeSql err: " + str(e))
        return (-1, tuple())

    finally:
        safeWork(lambda: None if oCursor is None else oCursor.close())
        oCursor = None

#end def executeSql

'''
检查mysql连接
@param aoConn 数据库连接
@return 成功返回tuple(True, "")，失败返回(False, strErr)
'''
def checkMysqlConnection(aoConn):
    try:
        aoConn.ping(reconnect = True)
        return (True, "")
    except Exception as e:
        return (False, str(e))
#end def


'''
判断字段是否带索引
@param aoConn db连接
@param astrDBName db名字
@param astrTableName 表名字
@param astrFieldName 字段名字
@return 有索引返回True
'''
def isIndexWithFieldName(aoConn, astrDBName, astrTableName, astrFieldName):

    strSql = "SHOW INDEX FROM %s.%s WHERE Seq_in_index = 1 AND Column_name = '%s'" % (astrDBName, astrTableName, astrFieldName)
    (iRows, oRecords) = executeSql(aoConn, strSql)
    # 有的话就返回true
    return iRows >= 1
#end def isIndexWithFieldName


'''
判断连接库的slave状态是否正常
@param aoConn db连接
@return 正常返回(True, "")，否则返回(False, strErr)
'''
def isSlaveOK(aoConn):
    if config.DEBUG_MODE:
        #调试环境直接认为成功
        return (True, "")
    #end if

    (iRows, oRecords) = executeSql(aoConn, "SHOW SLAVE STATUS")
    if (iRows < 1):
        return (False, "can not get slave status")
    #end if

    try:
        oRecord = oRecords[0]
        strSlaveIoRunning = oRecord[10]
        strSlaveSqlRunning = oRecord[11]
        if "Yes" == strSlaveIoRunning and "Yes" == strSlaveSqlRunning:
            return (True, "")
        #end if

        return (False, "SlaveIoRunning=%s, SlaveSqlRunning=%s" % (strSlaveIoRunning, strSlaveSqlRunning))

    except Exception as e:
        return (False, str(e))

#end def isSlaveOK

'''
获取mysql表的引擎名字
@param aoConn db连接
@param astrDbName db名
@param astrTableName 表名
@return 成功返回("引擎名", "")，否则返回("", strErr)
'''
def getMysqlTableEngine(aoConn, astrDbName, astrTableName):
    try:
        strSql = "SHOW TABLE STATUS FROM %s WHERE `Name` = '%s'" % (astrDbName, astrTableName)
        (iRows, oRecords) = executeSql(aoConn, strSql)
        if (iRows < 1):
            return ("", ("%s failed: %d" % (strSql, iRows)))
        #end if
        
        strEngine = oRecords[0][1]
        return (strEngine, "")

    except Exception as e:
        return ("", str(e))

#end def getMysqlTableEngine


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
返回磁盘使用空间百分比
@return 磁盘使用空间百分比0-100，失败返回-1
'''
def getDiskUsagePercent(astrDir):
    try:
        return psutil.disk_usage(astrDir).percent
    except Exception as e:
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
若指定磁盘占用高于最大值，则删除n天前的文件
@param astrDir 检查磁盘占用的目录
@param afMaxPercent 最大允许占用百分比值（0-100）
@param astrDelDir 删除文件的目录
@param auDeleteDays 删除auDeleteDays天前的
@return 执行了删除动作返回True
'''
def delFilesIfDiskPercentAbove(astrDir, afMaxPercent, astrDelDir, auDeleteDays):
    try:
        fUsePercent = getDiskUsagePercent(astrDir)
        if fUsePercent <= afMaxPercent:
            return False
        #end if
        
        bResult = False
        fCurTime = time.time()
        fDiffSeconds = auDeleteDays * 24 * 3600 #天数换算为妙

        oDelPath = Path(astrDelDir)
        for oChild in oDelPath.iterdir():
            fMTimeLen = fCurTime - oChild.stat().st_mtime
            if fMTimeLen > fDiffSeconds:                
                strPathName = oChild.as_posix()
                if delPathName(strPathName):
                    bResult = True
                    #addLog("delFilesIfDiskPercentAbove: delete '%s' OK" % strPathName)
                else:
                    addLog("delFilesIfDiskPercentAbove: delete '%s' failed" % strPathName)
                #end if
            #end if
        #end for
        
        return bResult

    except Exception as e:
        addLog("delFilesIfDiskPercentAbove error: %s" % e)
        return False
    #end try
#end def
