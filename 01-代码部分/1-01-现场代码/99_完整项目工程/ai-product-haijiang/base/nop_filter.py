import os
import sys
import time
import threading
from config import config
from . import util
from . import log
from .data_filter import data_filter

class nop_filter(data_filter):
    '''
    @author maoyanwei
    一个什么都不处理的filter
    本类run是线程安全的，可以作为数据驱动入口
    '''

    #构造
    def __init__(self, name = "nop"):
        super().__init__(name)
    #end def

    #过滤动作，不要接异常，出错了把异常抛出去
    def filter(self, aoContext):
        return not aoContext is None
    #end def

#end class

class nop_data_filter(nop_filter):
    '''
    @author maoyanwei
    以nop_filter为起始filter的filter
    '''

    #构造
    def __init__(self, nop_name, data_filter_class, *args):
        super().__init__(nop_name)

        '''
        流程为：
        nop_filter => data_filter_class
        '''
        self.set_next(data_filter_class(*args))
    #end def

