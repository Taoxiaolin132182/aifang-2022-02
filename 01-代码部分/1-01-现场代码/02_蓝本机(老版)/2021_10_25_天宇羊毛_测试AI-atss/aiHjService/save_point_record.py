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
CREATE TABLE `t_point_record` (
  `point_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `take_photo_id` bigint(20) unsigned NOT NULL COMMENT '拍照编号',
  `image_id` bigint(20) unsigned NOT NULL COMMENT '图片编号',
  `speed` decimal(4,0) NOT NULL COMMENT '传送带速度',
  `type` int(11) NOT NULL COMMENT '分类',
  `threshold` int(11) NOT NULL COMMENT '阈值',
  `level` int(11) NOT NULL COMMENT '等级',
  `point_xmax` int(11) NOT NULL DEFAULT '0' COMMENT '点的最大x坐标',
  `point_ymax` int(11) NOT NULL DEFAULT '0' COMMENT '点的最大y坐标',
  `point_xmin` int(11) NOT NULL DEFAULT '0' COMMENT '点的最小x坐标',
  `point_ymin` int(11) NOT NULL DEFAULT '0' COMMENT '点的最小y坐标',
  `point_xcenter` int(11) NOT NULL DEFAULT '0' COMMENT '点的中心x坐标',
  `point_ycenter` int(11) NOT NULL DEFAULT '0' COMMENT '点的中心y坐标',
  `state` tinyint(4) NOT NULL DEFAULT '1' COMMENT '状态[1:新增;2;超出边缘;3:重复;4:成功抓取;5:来不及抓取]',
  `is_del` tinyint(4) NOT NULL DEFAULT '1' COMMENT '是否删除[0:是;1:否]',
  `create_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '添加时间',
  `update_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '更新时间',
  PRIMARY KEY (`point_id`),
  KEY `idx_take_photo_id` (`take_photo_id`),
  KEY `idx_image_id` (`image_id`),
  KEY `idx_state` (`state`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8 COMMENT='点位表';
'''

'''
t_point_record存储上下文
'''
class point_record_context:
    def __init__(self):
        super().__init__()

        self.point_id = 0 #自增主键，key
        self.take_photo_id = 0 #拍照编号
        self.image_id = 0 #图片编号
        self.speed = 0 #传送带速度
        self.type = 0  # 分类
        self.threshold = 0  # 阈值
        self.level = 0  # 等级
        self.point_xmax = 0 #点的最大x坐标
        self.point_ymax = 0 #点的最大y坐标
        self.point_xmin = 0 #点的最小x坐标
        self.point_ymin = 0 #点的最小y坐标
        self.point_xcenter = 0 #点的中心x坐标
        self.point_ycenter = 0 #点的中心y坐标
        self.state = 1 #状态[1:新增;2;超出边缘;3:重复;4:成功抓取;5:来不及抓取]
        self.is_del = 1 #是否删除[0:是;1:否]

        self.log = ""
    #end def
#end class

'''
@author maoyanwei
保存到数据库t_point_record
'''
class save_point_record(db_filter):
    #构造
    def __init__(self):
        super().__init__("save_point_record")
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

        if aoContext.point_id <= 0:
            #插入操作
            strSql = (
                      "INSERT INTO `db_cotton_local`.`t_point_record`"
                      "(`take_photo_id`,`image_id`,`speed`,`type`,`threshold`,`level`,"
                      "`point_xmax`,`point_ymax`,`point_xmin`,`point_ymin`,`point_xcenter`,`point_ycenter`,"
                      "`state`,`is_del`,`create_time`,`update_time`) "
                      "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
                      "%s,%s,FROM_UNIXTIME(%s),FROM_UNIXTIME(%s))"
                     )
            oValues = (aoContext.take_photo_id, aoContext.image_id, aoContext.speed, aoContext.type, aoContext.threshold, aoContext.level,
                       aoContext.point_xmax, aoContext.point_ymax, aoContext.point_xmin, aoContext.point_ymin, 
                       aoContext.point_xcenter, aoContext.point_ycenter, 
                       aoContext.state, aoContext.is_del, curTimestamp, curTimestamp)
        else:
            #更新操作
            strSql = (
                      "UPDATE `db_cotton_local`.`t_point_record` "
                      "SET `take_photo_id`=%s,`image_id`=%s,`speed`=%s,`type`=%s,`threshold`=%s,`level`=%s,"
                      "`point_xmax`=%s,`point_ymax`=%s,`point_xmin`=%s,`point_ymin`=%s,`point_xcenter`=%s,`point_ycenter`=%s,"
                      "`state`=%s,`is_del`=%s,`update_time`=FROM_UNIXTIME(%s) "
                      "WHERE point_id=%s"
                     )
            oValues = (aoContext.take_photo_id, aoContext.image_id, aoContext.speed, aoContext.type, aoContext.threshold, aoContext.level,
                       aoContext.point_xmax, aoContext.point_ymax, aoContext.point_xmin, aoContext.point_ymin, 
                       aoContext.point_xcenter, aoContext.point_ycenter, 
                       aoContext.state, aoContext.is_del, curTimestamp, aoContext.point_id)
        #end if

        #执行sql
        (iResult, oRecords) = db_mgr.execute_sql(conn, strSql, oValues)
        if iResult < 1:
            # 失败
            raise Exception("execute [%s] failed" % strSql)
            return False
        #end if

        if aoContext.point_id <= 0:
            (iResult, oLastIds) = db_mgr.execute_sql(conn, "SELECT LAST_INSERT_ID()")
            if iResult != 1:
            # 获取id失败
                raise Exception("get LAST_INSERT_ID failed")
                return False
            #end if
            aoContext.point_id = oLastIds[0][0]
        #end if

        #db操作成功
        return True
    #end def

#end class
