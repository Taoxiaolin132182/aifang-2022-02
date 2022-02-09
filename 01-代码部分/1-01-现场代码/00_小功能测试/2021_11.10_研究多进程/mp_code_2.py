import multiprocessing
import time


class A:
    def __init__(self):
        self.a = None
        self.b = None
        # 创建一个共享内存
        # self.my_dict = multiprocessing.Manager().dict()

    # def get_num_a(self):
    #     print("计算逻辑A")
    #     time.sleep(3)
    #     # self.a = 10
    #     self.my_dict["a"] = 10

    def get_num_a(self, name1):
        print("计算逻辑A")
        time.sleep(1)
        i = 0
        while True:
            try:
                print("I'am A for {} times--{}".format(i, name1))
                i += 1
                time.sleep(1)
            except Exception as e:
                print("error from test1_run1: {}".format(e))

    def get_num_b(self, name2):
        print("计算逻辑B")
        time.sleep(1.5)
        for i in range(10):
            try:
                print("I'am B for {} times--{}".format(i, name2))
                time.sleep(1)
            except Exception as e:
                print("error from test1_run2: {}".format(e))

    # def get_num_b(self):
    #     print("计算逻辑B")
    #     time.sleep(5)
    #     # self.b = 6
    #     self.my_dict["b"] = 6

    def sum_ab(self):
        self.a = self.my_dict["a"]
        self.b = self.my_dict["b"]
        print("a的值为：{}".format(self.a))
        print("b的值为：{}".format(self.b))
        ret = self.a + self.b
        return ret

    def run(self):
        # self.get_num_a()
        # self.get_num_b()
        # print(self.sum_ab())
        p1 = multiprocessing.Process(target=self.get_num_a, args=("hhhh", ))
        p2 = multiprocessing.Process(target=self.get_num_b, args=("eeee", ))
        p1.start()
        p2.start()
        p1.join()
        p2.join()
        # print(self.sum_ab())
        print("完成调用")

if __name__ == "__main__":
    t1 = time.time()
    func = A()
    func.run()
    t2 = time.time()
    print("cost time: {}".format(t2 - t1))
