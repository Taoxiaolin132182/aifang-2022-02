import os
import sys
import time
import pymysql
import traceback
from config import config
from . import util
from . import log

'''
@author maoyanwei
DB管理工具
'''


'''
连接数据库
@param aoConfig 连接参数
@return 成功返回连接，失败返回None
'''
def connect_mysql(aoConfig, abNeedErr = False):
    if aoConfig is None:
        strErr = "connect_mysql failed: config is NULL"
        log.error(strErr)
        return None if not abNeedErr else (None, strErr)

    try:
        oConn = pymysql.connect(**aoConfig)

        #确保默认是自动提交
        oConn.autocommit(True)

        return oConn if not abNeedErr else (oConn, "")
    except Exception as e:
        strErr = str(e)
        log.error("connect_mysql failed:" + strErr)
        return None if not abNeedErr else (None, strErr)
#end of connect_mysql

'''
连接数据库
@param astrHostDomain host
@return 成功返回连接，失败返回None
'''
def connect_mysql_with_host_domain(astrHostDomain, abNeedErr = False):
    oConfig = config.DB_HOST_TO_CONFIG.get(astrHostDomain, None)
    if oConfig is None:
        strErr = "connect_mysql_with_host_domain failed: %s config is NULL" % astrHostDomain
        log.error(strErr)
        return None if not abNeedErr else (None, strErr)
    #end if

    return connect_mysql(oConfig, abNeedErr)
#end def connect_mysql_with_host_domain

'''
检查mysql连接
@param aoConn 数据库连接
@return 成功返回tuple(True, "")，失败返回(False, strErr)
'''
def check_mysql_connection(aoConn):
    try:
        aoConn.ping(reconnect = True)
        return (True, "")
    except Exception as e:
        return (False, str(e))
#end def

'''
指定连接上执行sql
@param aoConn 数据库连接
@param astrSql sql语句
@param aoArgs 可选参数
@param abNeedPing 执行前先测试服务可用性
@return 成功返回tuple(影响条数, 结果集)，失败返回(-1, tuple())
'''
def execute_sql(aoConn, astrSql, aoArgs = None, abNeedPing = True):
    
    if abNeedPing:
        (bIsOk, strErr) = check_mysql_connection(aoConn)
        if not bIsOk:
            log.error("execute_sql err: check mysql failed, " + str(strErr))
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
        strErr = "execute_sql(%s)(%s) err: %s" % (astrSql, aoArgs, e)
        log.error(strErr)
        exstr = traceback.format_exc()
        print("=========== execute_sql failed ===========\n%s\n\n" % exstr)
        return (-1, tuple())

    finally:
        util.safeWork(lambda: None if oCursor is None else oCursor.close())
        oCursor = None

#end def execute_sql

'''
判断字段是否带索引
@param aoConn db连接
@param astrDBName db名字
@param astrTableName 表名字
@param astrFieldName 字段名字
@return 有索引返回True
'''
def is_index_field(aoConn, astrDBName, astrTableName, astrFieldName):

    strSql = "SHOW INDEX FROM %s.%s WHERE Seq_in_index = 1 AND Column_name = '%s'" % (astrDBName, astrTableName, astrFieldName)
    (iRows, oRecords) = execute_sql(aoConn, strSql)
    # 有的话就返回true
    return iRows >= 1
#end def is_index_field

'''
判断连接库的slave状态是否正常
@param aoConn db连接
@return 正常返回(True, "")，否则返回(False, strErr)
'''
def is_slave_ok(aoConn):
    if config.DEBUG_MODE:
        #调试环境直接认为成功
        return (True, "")
    #end if

    (iRows, oRecords) = execute_sql(aoConn, "SHOW SLAVE STATUS")
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

#end def is_slave_ok

'''
获取mysql表的引擎名字
@param aoConn db连接
@param astrDbName db名
@param astrTableName 表名
@return 成功返回("引擎名", "")，否则返回("", strErr)
'''
def get_mysql_table_engine(aoConn, astrDbName, astrTableName):
    try:
        strSql = "SHOW TABLE STATUS FROM %s WHERE `Name` = '%s'" % (astrDbName, astrTableName)
        (iRows, oRecords) = execute_sql(aoConn, strSql)
        if (iRows < 1):
            return ("", ("%s failed: %d" % (strSql, iRows)))
        #end if
        
        strEngine = oRecords[0][1]
        return (strEngine, "")

    except Exception as e:
        return ("", str(e))

#end def get_mysql_table_engine

'''
从schema获取表记录数
@param aoConn db连接
@param astrDbName db名
@param astrTableName 表名
@return 成功返回(row_count, "")，否则返回(-1, strErr)
'''
def get_mysql_row_count_from_schema(aoConn, astrDBName, astrTableName):
    try:
        strSql = ("SELECT TABLE_ROWS FROM `information_schema`.`TABLES` "
                  "WHERE TABLE_SCHEMA='%s' AND TABLE_NAME='%s';") % (astrDBName, astrTableName)
        (iRows, oRecords) = execute_sql(aoConn, strSql)
        if (iRows < 1):
            return (-1, ("%s failed: %s" % (strSql, iRows)))
        #end if

        iRows = oRecords[0][0]
        return (iRows, "")

    except Exception as e:
        return (-1, str(e))
    #end try
#end def

'''
获取超过指定条数的记录key
@param aoConn db连接
@param astrDbName db名
@param astrTableName 表名
@param astrKeyField 主键
@param aiLimit1 当记录数到达aiLimit1时，删除到aiLimit2的范围内
@param aiLimit2 当记录数到达aiLimit1时，删除到aiLimit2的范围内
@return 无删除返回(None, "")，可以删除返回(key, "")，失败返回(None, strErr)
'''
def get_delete_key_when_need(aoConn, astrDBName, astrTableName, astrKeyField, aiLimit1, aiLimit2):
    try:
        if aiLimit2 >= aiLimit1:
            return (None, "Limit2(%s) >= Limit1(%s)" % (aiLimit2, aiLimit1))
        #end if

        iCurRows, strErr = get_mysql_row_count_from_schema(aoConn, astrDBName, astrTableName)
        if len(strErr) > 0:
            raise Exception(strErr)
        #end if

        if iCurRows < aiLimit1:
            #记录数未到，不需要删除
            return (None, "")
        #end if

        iDeleteRows = iCurRows - aiLimit2
        strSql = "SELECT %s FROM %s.%s ORDER BY %s LIMIT %s, 1;" % (astrKeyField, astrDBName, astrTableName, astrKeyField, iDeleteRows - 1)
        (iRows, oRecords) = execute_sql(aoConn, strSql)
        if (iRows < 1):
            return (-1, ("%s failed: %d" % (strSql, iRows)))
        #end if
        okey = oRecords[0][0]
        return (okey, "")

    except Exception as e:
        return (None, str(e))
    #end try
#end def

'''
删除指定多个表中小于等于key的记录
@param aoConn db连接
@param astrDbName db名
@param astrTableNames 表名集合，如(tab1, tab2, ...)
@param astrKeyField 主键
@param aoKey 比较的key值
@return 成功返回([del_row1, del_row2, ...], "")，失败返回([], strErr)
'''
def delete_record_when_be_key(aoConn, astrDBName, astrTableNames, astrKeyField, aoKey):
    iDelRows = []
    try:
        for tab in astrTableNames:
            strSql = "DELETE FROM %s.%s WHERE %s <= %%s;" % (astrDBName, tab, astrKeyField)
            (iRows, oRecords) = execute_sql(aoConn, strSql, aoKey)
            iDelRows.append(iRows)
        #end for
        return (iDelRows, "")
    except Exception as e:
        return (iDelRows, str(e))
    #end try
#end def

def delete_old_record(aoConn, astrDBName, astrTableNames, astrKeyFields):
    '''
    根据config配置，删除指定多个表里的过期记录
    @param aoConn db连接
    @param astrDbName db名
    @param astrTableNames 表名集合，如(tab1, tab2, ...)
    @param astrKeyFields 主键名集合，如(id1, id2, id3)
    @return 成功返回([del_row1, del_row2, ...], "")，失败返回([], strErr)
    '''

    iDelRows = []
    try:
        iLen = len(astrTableNames)
        if iLen != len(astrKeyFields):
            raise Exception("len(astrTableNames) != len(astrKeyFields)")
        #end if

        for i in range(iLen):
            oKey, strErr = get_delete_key_when_need(aoConn, astrDBName, astrTableNames[i], astrKeyFields[i],
                                                    config.LIMIT_DB_RECORD_NUM_1, config.LIMIT_DB_RECORD_NUM_2)
            if len(strErr) > 0:
                raise Exception("get_delete_key_when_need: " + strErr)
            #end if

            if oKey is None:
                #当前表无需删除
                log.debug("delete_old_record: %s.%s no need to delete record" % (astrDBName, astrTableNames[i]))
                iDelRows.append(0)
                continue
            #end if

            #从表中删除
            iRows, strErr = delete_record_when_be_key(aoConn, astrDBName, (astrTableNames[i], ), 
                                                      astrKeyFields[i], oKey)
            if len(strErr) > 0:
                raise Exception("delete_record_when_be_key: " + strErr)
            #end if
            #成功保存删除记录数
            iDelRows.append(iRows[0])
        #end for

        return (iDelRows, "")

    except Exception as e:
        return (iDelRows, str(e))
    #end try
#end def