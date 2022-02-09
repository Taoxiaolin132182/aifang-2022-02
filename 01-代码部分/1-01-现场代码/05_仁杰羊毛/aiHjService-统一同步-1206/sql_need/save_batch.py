import os
import sys
import time
import threading

START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, "..", "..", ".."))

from config import config
from base import util
from base.db_filter import db_filter
from base import db_mgr

'''
CREATE TABLE `t_batch` (
  `primary_batch` varchar(30) NOT NULL DEFAULT '' COMMENT '大批次',
  `secondary_batch` varchar(30) NOT NULL DEFAULT '' COMMENT '小批次',
  `create_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '添加时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
'''

'''
t_batch存储上下文
'''


class batch_context:
    def __init__(self):
        super().__init__()


        self.id = 0  # 自增主键
        self.primary_batch = 0  # 异常代码
        self.secondary_batch = 0  # 异常时间

    # end def


# end class

'''
@author txl copy maoyanwei
保存到数据库t_batch
'''


class save_batch(db_filter):
    # 构造
    def __init__(self):
        super().__init__("save_batch")
        self.execute = self.run

    # end def

    # 析构
    def __del__(self):
        super().__del__()

    # end def

    # 过滤动作，不要接异常，出错了把异常抛出去
    def filter(self, aoContext):
        # 基类先处理
        if not super().filter(aoContext):
            return False
        # end if

        conn = self.conn
        curTimestamp = time.time()

        if aoContext.id <= 0:
            # 插入操作
            strSql = (
                "INSERT INTO `db_cotton_local`.`t_batch`"
                "(`primary_batch`,`secondary_batch`,`create_time`) "
                "VALUES (%s,%s,FROM_UNIXTIME(%s))"
            )
            oValues = (aoContext.primary_batch, aoContext.secondary_batch, curTimestamp)
        else:
            # 更新操作
            strSql = (
                "UPDATE `db_cotton_local`.`t_batch` "
                "SET `primary_batch`=%s,`secondary_batch`=%s,`create_time`=FROM_UNIXTIME(%s)"
                "WHERE id=%s"
            )
            oValues = (aoContext.primary_batch, aoContext.secondary_batch, curTimestamp, aoContext.id)
        # end if

        # 执行sql
        (iResult, oRecords) = db_mgr.execute_sql(conn, strSql, oValues)

        if iResult < 1:
            # 失败
            raise Exception("execute [%s] failed" % strSql)
            return False
        # end if

        if aoContext.id <= 0:
            (iResult, oLastIds) = db_mgr.execute_sql(conn, "SELECT LAST_INSERT_ID()")
            if iResult != 1:
                # 获取id失败
                raise Exception("get LAST_INSERT_ID failed")
                return False
            # end if
            aoContext.id = oLastIds[0][0]
        # end if
        # db操作成功
        return True
    # end def

# end class
