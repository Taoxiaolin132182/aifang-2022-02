import os
import time
from threading import Condition


class count_down_latch:
    def __init__(self, count):
        self.count = count
        self.condition = Condition()
        #我们也仿照Condition暴露下面两个接口
        self.acquire = self.condition.acquire
        self.release = self.condition.release

    def wait(self):
        self.condition.acquire()
        # print("wait not timeout")
        try:
            while self.count > 0:
                self.condition.wait()
        finally:
            self.condition.release()

    def wait_with_timeout(self,timeout):
        self.condition.acquire()
        # print("wait with timeout")
        try:
            while self.count > 0:
                bResult = self.condition.wait(timeout)
                if not bResult:
                    break

            return bResult
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

