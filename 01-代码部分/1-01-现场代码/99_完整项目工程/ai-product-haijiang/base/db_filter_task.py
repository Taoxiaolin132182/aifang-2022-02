import os
import sys
import time
import threading
from config import config
from . import util
from . import log
from .nop_filter import nop_data_filter

'''
@author maoyanwei
通过db_filter构建的db异步处理任务
'''
class db_filter_task():
    def __init__(self, db_filter_class, *args):
        '''
        @param db_filter_class 构建的db_filter类
        @param args 用于构造参数
        '''
        self.__oFilter = nop_data_filter("nop", db_filter_class, *args)
        self.queue_size = 100
        self.start = self.__oFilter.start
        self.stop = self.__oFilter.stop
    #end def

    def __del__(self):
        '''
        析构
        '''
        self.stop()
    #end def

    def add(self, task_context):
        '''
        添加任务处理
        @param task_context 任务上下文
        @return 成功添加返回True
        '''
        self.__oFilter.set_maxsize(self.queue_size)
        return self.__oFilter.run(task_context)
    #end def

#end class
