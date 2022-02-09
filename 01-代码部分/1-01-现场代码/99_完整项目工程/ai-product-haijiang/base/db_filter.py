import os
import sys
import time
import threading
from config import config
from . import util
from . import log
from . import db_mgr
from .data_filter import data_filter

'''
@author maoyanwei
数据库filter基类
'''
class db_filter(data_filter):
    #构造
    def __init__(self, name):
        super().__init__(name)
        self.__conn = None #数据库连接
    #end def

    #析构
    def __del__(self):
        super().__del__()
    #end def

    @property
    def conn(self):
        '''
        db连接
        '''
        return self.__conn
    #end def

    #建立mysql连接，失败抛出异常
    def __connect_db(self):
        oConn, strErr = db_mgr.connect_mysql(config.DB_CONFIG, True)
        if oConn is None:
            raise Exception("connect_mysql failed: %s" % strErr)
            return
        #end if
        #新建连接成功
        self.__conn = oConn
        log.info("connect db ok")
    #end def

    #检查已有连接，失败抛出异常
    def __check_db_connect(self):
        (bConnIsOk, strErr) = db_mgr.check_mysql_connection(self.__conn)
        if bConnIsOk:
            #可用则不管
            #print("check_mysql_connection ok")
            return
        #end if

        #现有连接不可用了，总是关闭
        util.safeWork(lambda: self.__conn.close())
        self.__conn = None
        log.warning("check_mysql_connection failed: %s" % strErr)
        
        #重新创建新的
        self.__connect_db()
    #end def

    #过滤动作，不要接异常，出错了把异常抛出去
    def filter(self, aoContext):

        #先检查要不要连接db
        if self.__conn is None:
            self.__connect_db()
        else:
            #已有连接检查是否仍然可用
            self.__check_db_connect()
        #end if

        #db操作成功
        return True
    #end def

#end class
