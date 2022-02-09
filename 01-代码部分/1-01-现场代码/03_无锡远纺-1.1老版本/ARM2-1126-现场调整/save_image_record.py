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
CREATE TABLE `t_image_record` (
  `image_id` bigint(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '图片编号',
  `take_photo_id` bigint(20) unsigned NOT NULL COMMENT '拍照编号',
  `batch_no` varchar(32) NOT NULL DEFAULT '""' COMMENT '批次号',
  `image_path` varchar(255) CHARACTER SET utf8mb4 NOT NULL DEFAULT '' COMMENT '图片地址',
  `photo_begin_time` timestamp(3) NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '拍照开始时间',
  `photo_end_time` timestamp(3) NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '拍照结束时间',
  `call_ai_begin_time` timestamp(3) NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '调用AI开始时间',
  `call_ai_end_time` timestamp(3) NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '调用AI结束时间',
  `create_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '添加时间',
  `update_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '更新时间',
  `state` tinyint(4) NOT NULL DEFAULT '1' COMMENT '状态[0:无效;1:有效]',
  PRIMARY KEY (`image_id`),
  KEY `idx_take_photo_id` (`take_photo_id`),
  KEY `idx_photo_begin_time` (`photo_begin_time`),
  KEY `idx_call_ai_begin_time` (`call_ai_begin_time`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='图片表';
'''

'''
t_image_record存储上下文
'''
class image_record_context:
    def __init__(self):
        super().__init__()

        curTimestamp = time.time()
        self.image_id = 0 #图片编号，key
        self.take_photo_id = 0 #拍照编号
        self.batch_no = ""  # 批次号
        self.image_path = "" #图片地址
        self.photo_begin_time = curTimestamp #拍照开始时间
        self.photo_end_time = curTimestamp #拍照结束时间
        self.call_ai_begin_time = 0 #调用AI开始时间
        self.call_ai_end_time = 0 #调用AI结束时间
        self.state = 1 #状态[0:无效;1:有效]'
        self.log = ""
    #end def
#end class

'''
@author maoyanwei
保存到数据库t_image_record
'''
class save_image_record(db_filter):
    #构造
    def __init__(self):
        super().__init__("save_image_record")
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

        if aoContext.image_id <= 0:
            #插入操作
            strSql = (
                      "INSERT INTO `db_cotton_local`.`t_image_record`"
                      "(`take_photo_id`,`batch_no`,`image_path`,`photo_begin_time`,`photo_end_time`,"
                      "`call_ai_begin_time`,`call_ai_end_time`,`create_time`,`update_time`,`state`) "
                      "VALUES (%s,%s,%s,FROM_UNIXTIME(%s),FROM_UNIXTIME(%s),FROM_UNIXTIME(%s),FROM_UNIXTIME(%s),"
                      "FROM_UNIXTIME(%s),FROM_UNIXTIME(%s),%s)"
                     )
            oValues = (aoContext.take_photo_id, aoContext.batch_no, aoContext.image_path, aoContext.photo_begin_time, aoContext.photo_end_time,
                       aoContext.call_ai_begin_time, aoContext.call_ai_end_time,
                       curTimestamp, curTimestamp, aoContext.state)
        else:
            #更新操作
            strSql = (
                      "UPDATE `db_cotton_local`.`t_image_record` "
                      "SET `take_photo_id`=%s,`batch_no`=%s,`image_path`=%s,`photo_begin_time`=FROM_UNIXTIME(%s),`photo_end_time`=FROM_UNIXTIME(%s),"
                      "`call_ai_begin_time`=FROM_UNIXTIME(%s),`call_ai_end_time`=FROM_UNIXTIME(%s),"
                      "`update_time`=FROM_UNIXTIME(%s),`state`=%s "
                      "WHERE image_id=%s"
                     )
            oValues = (aoContext.take_photo_id, aoContext.batch_no, aoContext.image_path, aoContext.photo_begin_time, aoContext.photo_end_time,
                       aoContext.call_ai_begin_time, aoContext.call_ai_end_time,
                       curTimestamp, aoContext.state, aoContext.image_id)
        #end if

        #执行sql
        (iResult, oRecords) = db_mgr.execute_sql(conn, strSql, oValues)
        if iResult < 1:
            # 失败
            raise Exception("execute [%s] failed" % strSql)
            return False
        #end if

        if aoContext.image_id <= 0:
            (iResult, oLastIds) = db_mgr.execute_sql(conn, "SELECT LAST_INSERT_ID()")
            if iResult != 1:
            # 获取id失败
                raise Exception("get LAST_INSERT_ID failed")
                return False
            #end if
            aoContext.image_id = oLastIds[0][0]
        #end if

        #db操作成功
        return True
    #end def

#end class
