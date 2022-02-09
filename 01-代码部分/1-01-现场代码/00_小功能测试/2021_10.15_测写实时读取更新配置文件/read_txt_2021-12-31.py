import os, time, copy, json


'''
1、确定文件存在
2、去对比文件的创建，修改时间

'''

class airun:
    def __init__(self):
        self.time_str1 = None
        self.path1_file = r"C:\001chengxu\04\2020twelve_1207\08_web_test\test_base_func1\af-config.txt"

    '''起始函数'''
    def run_func_m(self):
        X_l_cfg = [None] * 4
        Y_l_cfg = [None] * 4
        T_l_cfg = [None] * 4
        use_num = 0  # 配置文件中的可使用标记数
        claw_list1 = ["claw1", "claw2", "claw3", "claw4"]
        res_mes1 = self.get_file_message()
        if res_mes1 is not None:
            if res_mes1["bool_use"] == use_num:
                print("配置文件为 可录入状态")
                for i in range(len(claw_list1)):
                    X_l_cfg[i] = res_mes1[claw_list1[i]]["x"]
                    Y_l_cfg[i] = res_mes1[claw_list1[i]]["y"]
                    T_l_cfg[i] = res_mes1[claw_list1[i]]["t"]
        res_data1 = {"X": X_l_cfg, "Y": Y_l_cfg, "T": T_l_cfg}
        print("读取整理后的补偿参数为：\n{}".format(res_data1))
    '''获取配置文件信息'''
    def get_file_message(self):
        path2 = self.path1_file
        mes_res = None
        if self.check_file_time(path2):
            # 读取文件内容
            bool_res, mes_res = self.read_txt_message(path2)
        return mes_res

    '''读取txt input:完整路径  output: 是否异常结果'''
    def read_txt_message(self, path):
        bool_read_ok = False  # 读取是否异常
        message1 = None
        try:
            if os.path.exists(path):
                print("\n==================\n开始读取txt信息\n")
                print("{} 此文件存在".format(path))
                # encoding=  gbk utf-8 ansi
                with open(path, "rb") as f_str:
                    message1 = json.load(f_str)
                    print("信息个数：{}".format(len(message1)))
                    print("信息类型：{}".format(type(message1)))
                    print("\n==================\n读取内容为:\n{}".format(message1))
                print("读取txt配置文件，完成")
                bool_read_ok = True
            else:
                print("{} 该文件不存在".format(path))
        except Exception as e:
            print(f"read_txt1  err: {e}")
        return bool_read_ok, message1

    '''检查文件的 创建和修改时间'''
    def check_file_time(self, path):
        bool_changed1 = False  # 默认是：False(表示没变化 和之前一样的)
        # path = "/mnt/data"
        # path = r"C:\001chengxu\04\2020twelve_1207\08_web_test\test_base_func1\af-config.txt"
        if os.path.exists(path):
            print("文件存在")
            now_file_time1 = self.get_file_time(path)
            if self.time_str1 == now_file_time1:
                print("配置文件未发生变化")
            else:
                print("配置文件发生了变化")
                bool_changed1 = True
                self.time_str1 = copy.deepcopy(now_file_time1)
        return bool_changed1

    '''获取文件的 创建和修改时间'''
    def get_file_time(self, path_t):
        time_list1 = [None, None]  # [文件创建时间, 文件修改时间]
        if os.path.exists(path_t):
            # print("文件存在")
            time_list1 = [os.path.getctime(path_t), os.path.getmtime(path_t)]
        return time_list1










'''主调用函数'''
def main_func1():
    service1 = airun()  # 实例化
    service1.run_func_m()
    pass

if __name__ == "__main__":
    main_func1()