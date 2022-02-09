import time, copy, os

import config_basis as bcfg




def calculate1_22_0125():
    X1_LEN1 = [270, 271, 272]
    X2_LEN1 = [275, 276, 277]
    X3_LEN1 = [280, 280, 280]
    X4_LEN1 = [280, 280, 280]
    add_list = [[1, 1, 1], [2, 2, 2], [3, 3, 3], [4, 4, 4]]
    list1 = [X1_LEN1, X2_LEN1, X3_LEN1, X4_LEN1]
    list1_ori = copy.deepcopy(list1)

    print(list1)

    Min_value_X = 30  # 抓取限位X最小
    Max_value_X = 1770  # 抓取限位X最小
    x_limit = [[0, 0]] * 4
    for xli in range(len(x_limit)):
        x_limit[xli] = [Min_value_X + list1_ori[xli][0], Max_value_X + list1_ori[xli][0]]
    print("x_limit: {}".format(x_limit))

    # for i in range(len(list1)):
    #     list1[i] = [x + y for x, y in zip(list1_ori[i], add_list[i])]
    # print(list1)
    # x_lis1 = [x + y for x, y in zip(list1, add_list)]
    # print(x_lis1)




def calculate1():
    data1 = 0
    g_list1 = [False, 0, 0, ]
    for i in range(40):
        time.sleep(0.5)
        data1 += 10
        now_m1 = (int(data1) // 60) + 1
        print("计数：{} ，处理：{}".format(data1, now_m1))
        if now_m1 != g_list1[2]:
            g_list1 = [True, i, copy.deepcopy(now_m1)]
            print("====={}".format(g_list1))

def calculate2():
    record_data1 = [222,222]
    count_ok1 = [0,1,0]

    end_times = record_data1[1] if count_ok1[1] == 0 else count_ok1[1] + 1
    print("end_times", end_times)

def test_time_print():
    t1 = time.time()
    for i in range(40):
        time.sleep(2)
        length_time = round(time.time() - t1, 2)
        str_add1 = bcfg.t_str1
        print("第{}次的输出，现在运行时间：{} ---{}".format(i + 1, length_time, str_add1))

def judge_num1():
    model_c = ["old", "new", 1]
    cam_n = ["A", "B", "C"]
    original_num = {"A": 1, "B": 3, "C": 2}
    for i in range(len(cam_n)):
        num_now1 = original_num[cam_n[i]]
        if model_c[model_c[2]] == "old":
            now_data1 = num_now1 - 1
        else:
            # now_data1 = 0 if num_now1 == 1 else 2 if num_now1 == 2 else 1
            t_list1 = [0, 2, 1]
            now_data1 = t_list1[num_now1 - 1]
        print("转换结果：{} -- {}".format(cam_n[i], now_data1))


def get_pid():
    pid_child = os.getpid()
    pid_parent = os.getppid()
    print("本程序进程：{}".format([pid_child, pid_parent]))

def main_func1():
    calculate1_22_0125()
    # get_pid()
    # calculate2()
    # test_time_print()
    # judge_num1()

if __name__ == "__main__":
    main_func1()