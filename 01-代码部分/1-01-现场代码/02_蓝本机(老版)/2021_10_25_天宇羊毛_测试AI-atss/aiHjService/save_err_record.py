import os
import sys
import time
import threading

START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, "..",".."))

from config import config
from base import util
from base.db_filter import db_filter
from base import db_mgr

'''
CREATE TABLE `t_err_record` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `err_code` int(11) NOT NULL DEFAULT '0' COMMENT '异常代码',
  `err_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '异常时间',
  `create_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '添加时间',
  `update_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '更新时间',
  `err_instructions` varchar(64) NOT NULL COMMENT '代码说明',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8;
'''

'''
t_err_record存储上下文
'''
class err_context:
    def __init__(self):
        super().__init__()

        curTimestamp = time.time()
        self.id = 0 #自增主键
        self.err_code = 0 #异常代码
        self.err_time = 0 #异常时间
        self.err_instructions = None #代码说明
        self.log = ""
    #end def
#end class

'''
@author txl copy maoyanwei
保存到数据库t_err_record
'''
class save_err(db_filter):
    #构造
    def __init__(self):
        super().__init__("save_err")
        self.execute = self.run
    #end def

    #析构
    def __del__(self):
        super().__del__()
    #end def

    #过滤动作，不要接异常，出错了把异常抛出去
    def filter(self, aoContext):
        #基类先处理
        if not super().filter(aoContext):
            return False
        #end if
        
        conn = self.conn
        curTimestamp = time.time()

        if aoContext.id <= 0:
            #插入操作
            strSql = (
                      "INSERT INTO `db_cotton_local`.`t_err_record`"
                      "(`err_code`,`err_time`,`create_time`,`update_time`,`err_instructions`) "
                      "VALUES (%s,FROM_UNIXTIME(%s),FROM_UNIXTIME(%s),FROM_UNIXTIME(%s),%s)"
                     )
            oValues = (aoContext.err_code, aoContext.err_time, curTimestamp, curTimestamp,aoContext.err_instructions)
        else:
            #更新操作
            strSql = (
                      "UPDATE `db_cotton_local`.`t_err_record` "
                      "SET `err_code`=%s,`err_time`=FROM_UNIXTIME(%s),`update_time`=FROM_UNIXTIME(%s),`err_instructions`=%s"
                      "WHERE id=%s"
                     )
            oValues = (aoContext.err_code, aoContext.err_time, curTimestamp,aoContext.err_instructions, aoContext.id)
        #end if

        #执行sql
        (iResult, oRecords) = db_mgr.execute_sql(conn, strSql, oValues)

        if iResult < 1:
            # 失败
            raise Exception("execute [%s] failed" % strSql)
            return False
        #end if

        if aoContext.id <= 0:
            (iResult, oLastIds) = db_mgr.execute_sql(conn, "SELECT LAST_INSERT_ID()")
            if iResult != 1:
            # 获取id失败
                raise Exception("get LAST_INSERT_ID failed")
                return False
            #end if
            aoContext.id = oLastIds[0][0]
        #end if
        #db操作成功
        return True
    #end def

#end class
