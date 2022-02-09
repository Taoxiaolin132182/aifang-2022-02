# coding=utf-8
import time, sys, os, copy, queue, signal
import multiprocessing
# from multiprocessing import Process
import threading
import logging.config
import test_cfg1 as aicfg

logger1 = logging.getLogger('temp1')
logger2 = logging.getLogger('temp2')
logger3 = logging.getLogger('temp3')
logger4 = logging.getLogger('temp4')
logger5 = logging.getLogger('temp5')


list_sig = [True, True, True]
def judge_sig1(signum,frame):
    global list_sig
    print("接收到主动关闭信号：{}".format(signum))
    list_sig[0] = False

signal.signal(signal.SIGUSR1, judge_sig1)

class TestMainF1:
    def __init__(self):
        self.pic_p_use = [None] * 8
        self.light_num1 = 1
        self.name2 = None

    def test1_run1(self, name1):
        num1 = 0
        while True:
            time.sleep(4)
            num1 += 1
            try:
                logger1.info("我是2号log---{}, 这是第{}次--{}".format(list_sig[0], num1, name1))


            except Exception as e:
                print("error from test1_run1: {}".format(e))

    def test2_run2(self, name1):
        num1 = 0; time.sleep(0.2)
        while True:
            time.sleep(4)
            num1 += 1
            try:
                # print("我是3号log, 这是第次--名字：")
                # print("我是4号log, 这是第{}次--名字".format(num1))
                logger1.info("我是5号log----{}, 这是第{}次--名字：{}".format(list_sig[0], num1, name1))

            except Exception as e:
                print("error from test1_run1: {}".format(e))

    def use_thread1(self,name3):
        print("启动线程名：{}".format(name3))
        tp1 = threading.Thread(target=self.test1_run1, args=('eeeee',), name="test1_run1")
        tp1.start()
        tp1.join()  # 到这一步就阻塞了
        tp2 = threading.Thread(target=self.test2_run2, args=('hello',), name="test2_run2")
        tp2.start()

        tp2.join()

    def wait_sign(self):
        global list_sig
        bool_sig1 = True
        print("开始等待外部信号 + 内部异常")
        print("The process's PID is:", os.getpid())
        while bool_sig1:
            if list_sig[0]:
                time.sleep(2)
            else:
                print("类中接收到 关闭程序的信号，等待2秒")
                time.sleep(2)
                bool_sig1 = False
        return bool_sig1



    def start_run(self):
        # p1 = multiprocessing.Process(target=self.test1_run1, args=('eeeee',), daemon=True)
        # p2 = multiprocessing.Process(target=self.test2_run2, args=('hello',), daemon=True)
        p3 = multiprocessing.Process(target=self.use_thread1, args=('eeeee',), daemon=True)
        p3.start()
        # p1.start()
        # p2.start()
        # p1.join()
        # p2.join()
        # self.canshu_change()
        # time.sleep(300)
        print("所有进程已经全部开始")
        bool_res1 = self.wait_sign()
        if not bool_res1:
            # p1.close()
            # p2.close()
            print("进入退出程序")
            time.sleep(10.5)
            # os._exit(0)
            sys.exit(0)

        # self.test1_run1()
        # self.test2_run2("hello")
        pass



if __name__ == "__main__":
    logging.config.fileConfig("./log.conf")
    serv1 = TestMainF1()
    serv1.start_run()