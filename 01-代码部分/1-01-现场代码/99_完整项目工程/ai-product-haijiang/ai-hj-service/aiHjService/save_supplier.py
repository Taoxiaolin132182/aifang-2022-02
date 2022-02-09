import os
import sys
import time
import threading

START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, "..", ".."))

from config import config
from base import util
from base.db_filter import db_filter
from base import db_mgr

'''
CREATE TABLE `t_supplier` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `number` bigint(11) unsigned NOT NULL DEFAULT '1' COMMENT '编号',
  `Chinese_name` varchar(30) NOT NULL DEFAULT '' COMMENT '中文名称',
  `for_short` varchar(30) NOT NULL DEFAULT '' COMMENT '英文简称',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

CREATE TABLE `t_supplier` (
  `number` bigint(11) unsigned NOT NULL DEFAULT '1' COMMENT '编号',
  `Chinese_name` varchar(30) NOT NULL DEFAULT '' COMMENT '中文名称',
  `for_short` varchar(30) NOT NULL DEFAULT '' COMMENT '英文简称'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
'''

'''
t_supplier存储上下文
'''


class supplier_context:
    def __init__(self):
        super().__init__()

        curTimestamp = time.time()
        self.id = 0  # 自增主键
        self.number = 1  # 约定编号
        self.Chinese_name = 0  # 中文名称
        self.for_short = 0  # 英文简称




'''
@author txl copy maoyanwei
保存到数据库t_supplier
'''


class save_supplier(db_filter):
    # 构造
    def __init__(self):
        super().__init__("save_supplier")
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

        # if aoContext.id <= 0:
            # 插入操作
        strSql = (
            "INSERT INTO `db_cotton_local`.`t_supplier`"
            "(`number`,`Chinese_name`,`for_short`) "
            "VALUES (%s,%s,%s)"
        )
        oValues = (aoContext.number, aoContext.Chinese_name,  aoContext.for_short)
        # else:
        #     # 更新操作
        #     strSql = (
        #         "UPDATE `db_cotton_local`.`t_supplier` "
        #         "SET `number`=%s,`Chinese_name`=%s,`for_short`=%s"
        #         "WHERE id=%s"
        #     )
        #     oValues = (aoContext.number, aoContext.Chinese_name,  aoContext.for_short, aoContext.id)
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
