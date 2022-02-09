# coding=utf-8
import time, sys, os, copy, queue
import multiprocessing
# from multiprocessing import Process
import threading
import logging.config

logger1 = logging.getLogger('temp1')
logger2 = logging.getLogger('temp2')
logger3 = logging.getLogger('temp3')
logger4 = logging.getLogger('temp4')
logger5 = logging.getLogger('temp5')


class TestMainF1:
    def __init__(self):
        self.pic_p_use = [None] * 8
        self.light_num1 = 1
        self.name2 = None

    def test1_run1(self, name1):
        num1 = 0
        while True:
            time.sleep(1)
            num1 += 1
            try:
                # print("测试函数1运行中")
                # get_data = self.q_a1.get(timeout=2)
                # print("get_data:{}".format(get_data))
                # print("我是1号log, 这是第{}次".format(num1))
                logger1.info("我是2号log, 这是第{}次--{}".format(num1, name1))

            except Exception as e:
                print("error from test1_run1: {}".format(e))

    def test2_run2(self, name1):
        # pid2 = os.getpid()
        # print("该进程的ID: {}".format(pid2))

        # cmd1 = "taskset -p " + str(pid2)
        # r = os.popen(cmd1)
        # info = r.readlines()
        # print("现在进程所在cpu信息：{}".format(info))
        #
        # cmd2 = "taskset -pc 2 " + str(pid2)
        # r2 = os.popen(cmd2)
        # info2 = r2.readlines()
        # print("更改进程所在cpu信息：{}".format(info2))

        num1 = 0
        time.sleep(0.2)
        while True:
            time.sleep(1)
            num1 += 1
            try:
                # print("我是3号log, 这是第次--名字：")
                # print("我是4号log, 这是第{}次--名字".format(num1))
                logger1.info("我是5号log, 这是第{}次--名字：{}".format(num1, name1))

            except Exception as e:
                print("error from test1_run1: {}".format(e))








    def start_run(self):
        p1 = multiprocessing.Process(target=self.test1_run1, args=('eeeee',))
        p2 = multiprocessing.Process(target=self.test2_run2, args=('hello',))

        p1.start()
        p2.start()
        p1.join()
        p2.join()
        # self.canshu_change()

        print("所有进程已经全部开始")
        # self.test1_run1()
        # self.test2_run2("hello")
        pass



if __name__ == "__main__":
    logging.config.fileConfig("./log.conf")
    serv1 = TestMainF1()
    serv1.start_run()