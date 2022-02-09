# coding=utf-8
import time, sys, os, copy, queue
import multiprocessing
# from multiprocessing import Process
import threading
import logging.config

# logger1 = logging.getLogger('temp1')
# logger2 = logging.getLogger('temp2')
# logger3 = logging.getLogger('temp3')
# logger4 = logging.getLogger('temp4')
# logger5 = logging.getLogger('temp5')


class TestMainF1:
    def __init__(self):
        self.q_a1 = queue.Queue(maxsize=20)
        self.pic_p_use = [None] * 8
        self.light_num1 = 1
        self.name2 = None

    def test1_run1(self):
        num1 = 0
        while True:
            time.sleep(1)
            num1 += 1
            try:
                # print("测试函数1运行中")
                # get_data = self.q_a1.get(timeout=2)
                # print("get_data:{}".format(get_data))
                print("我是1号log, 这是第{}次".format(num1))
                # logger2.info("我是2号log, 这是第{}次".format(num1))

            except Exception as e:
                print("error from test1_run1: {}".format(e))

    def test2_run2(self):
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
                print("我是4号log, 这是第{}次--名字".format(num1))
                # print("我是5号log, 这是第{}次--名字：{}".format(num1, name1))

            except Exception as e:
                print("error from test1_run1: {}".format(e))


    def create_file_path1(self):
        date_today = "2021_1115"  # 检查本地时间和网络时间
        Ctrl_light = True
        if date_today is not None:
            self.save_pic_aipath = "/mnt/data/data/image_original/img_" + date_today
            date_path1 = date_today + "_inter"
        else:
            date_path1 = time.strftime("%Y_%m%d", time.localtime()) + "_lost"
        date_path2 = "renjie_1.1_arm1_" + date_path1

        pre_path_list1 = ["/mnt/data/data/image_original/", "/mnt/data/data/upload_image/", "/mnt/data/data/image/",
                          "/mnt/data/data/image/havebox/", "/mnt/data/data/image/nobox/"]
        '''[0]have-W, [1]no-W, [2]up-have-W, [3]up-no-W, 
           [4]have-UV, [5]no-UV, [6]up-have-UV, [7]up-no-UV'''
        self.pic_p_use[0] = os.path.join(pre_path_list1[3], date_path2 + "_W")
        self.pic_p_use[1] = os.path.join(pre_path_list1[4], date_path2 + "_W")
        self.pic_p_use[2] = os.path.join(pre_path_list1[1], date_path2 + "_have_W")
        self.pic_p_use[3] = os.path.join(pre_path_list1[1], date_path2 + "_no_W")
        if Ctrl_light:
            self.pic_p_use[4] = os.path.join(pre_path_list1[3], date_path2 + "_UV")
            self.pic_p_use[5] = os.path.join(pre_path_list1[4], date_path2 + "_UV")
            self.pic_p_use[6] = os.path.join(pre_path_list1[1], date_path2 + "_have_UV")
            self.pic_p_use[7] = os.path.join(pre_path_list1[1], date_path2 + "_no_UV")

        for ip in range(len(pre_path_list1) + len(self.pic_p_use) + 1):
            if ip < len(pre_path_list1):
                path_p1 = pre_path_list1[ip]
            else:
                if ip == len(pre_path_list1):
                    path_p1 = self.save_pic_aipath
                else:
                    path_p1 = self.pic_p_use[ip - len(pre_path_list1) - 1]
                print("pic_path({})：{}".format(ip + 1 - len(pre_path_list1), path_p1))
            if path_p1 is None:
                break
            else:
                if not os.path.exists(path_p1):
                    os.makedirs(path_p1)
        for iph in range(len(pre_path_list1) - 2):
            chmod_code1 = "chmod -R 777 " + pre_path_list1[iph] + " &"
            # os.system(chmod_code1)
            print(chmod_code1)


    def canshu_change(self):
        for i in range(80):
            print("IP :{}  num:{}".format(i, self.light_num1))
            self.light_num1 = 1 - self.light_num1
            print("IP :{}  num:{}".format(i, self.light_num1))
            time.sleep(2)




    def start_run(self):
        p1 = multiprocessing.Process(target=self.test2_run2)
        # p2 = multiprocessing.Process(target=self.test2_run2, args=('hello',))

        p1.start()
        p1.join()
        # p2.start()

        # self.canshu_change()

        print("所有进程已经全部开始")
        # self.test1_run1()
        # self.test2_run2("hello")
        pass


def main_func1():
    # p1 = multiprocessing.Process(target=test1_run1())
    p1 = multiprocessing.Process(target=test2_run2, args=('bye,bye',))
    p2 = multiprocessing.Process(target=test2_run2, args=('hello',))

    # p1 = threading.Thread(target=test2_run2("bye,bye"))
    # p2 = threading.Thread(target=test2_run2("hello"))

    p1.start()
    p2.start()


    # self.canshu_change()

    print("所有进程已经全部开始")
    pass


def test1_run1():
    num1 = 0
    while True:
        time.sleep(1)
        num1 += 1
        try:
            # print("测试函数1运行中")
            # get_data = self.q_a1.get(timeout=2)
            # print("get_data:{}".format(get_data))
            print("我是1号log, 这是第{}次".format(num1))
            print("我是2号log, 这是第{}次".format(num1))

        except Exception as e:
            print("error from test1_run1: {}".format(e))

def test2_run2(name1):
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

    # num1 = 0
    time.sleep(0.2)
    while True:
        time.sleep(1)
        # num1 += 1
        try:
            print("我是3号log, 这是第次--名字：{}".format(name1))
            # print("我是4号log, 这是第{}次--名字：{}".format(num1, name1))
            # print("我是5号log, 这是第{}次--名字：{}".format(num1, name1))

        except Exception as e:
            print("error from test1_run1: {}".format(e))





if __name__ == "__main__":
    # logging.config.fileConfig("./log.conf")
    serv1 = TestMainF1()
    serv1.start_run()
    # main_func1()
    pass