import os
from threading import Condition

'''
@author maoyanwei
实现同java的count_down_latch
'''
class count_down_latch:
    def __init__(self, count):
        self.count = count
        self.condition = Condition()
        #我们也仿照Condition暴露下面两个接口
        self.acquire = self.condition.acquire
        self.release = self.condition.release

    def wait(self):
        self.condition.acquire()
        try:
            while self.count > 0: self.condition.wait()
        finally:
            self.condition.release()

    def count_down(self):
        self.condition.acquire()
        if self.count > 0:
            self.count -= 1
            if self.count <= 0: self.condition.notifyAll()
        #end if
        self.condition.release()

#end class

