import threading
import queue
import time
import copy
from random import randint

if_need_stop = 2
num_point = [0,0,0,0,0,0]

def ctrl_run_stop():
    global if_need_stop
    t_start1 = time.time()
    limit_time1 = [[0,20], [160,180], [310,340]]
    print("ctrl_run_stop -- start")
    while True:
        time.sleep(3)
        try:
            len_time1 = int(time.time() - t_start1)

            bool_ctrl = (len_time1 in range(limit_time1[0][0], limit_time1[0][1])) or \
                        (len_time1 in range(limit_time1[1][0], limit_time1[1][1])) or \
                        (len_time1 in range(limit_time1[2][0], limit_time1[2][1]))
            if bool_ctrl:
                if if_need_stop != 0:  # 此时在运行
                    print("时刻：---停止")
                    if_need_stop = 0
            else:
                if if_need_stop != 1:  # 此时停止
                    print("时刻：-- 运行")
                    if_need_stop = 1

        except Exception as e:
            print(f"ctrl_run_stop  err: {e}")
            time.sleep(1)



def produce_point():
    global num_point, if_need_stop
    num_time1 = 0
    limit_list = [[30,45],[100,115]]
    while True:
        time.sleep(0.1)
        num_time1 += 1
        try:
            if if_need_stop == 0:
                time.sleep(2)
            else:
                num_point_now = randint(0, 5)
                for il in range(len(limit_list)):
                    if (num_time1 > limit_list[il][0]) and (num_time1 < limit_list[il][1]):
                        num_point_now = 1
                num_point[4] += num_point_now
                time.sleep(1.5)
        except Exception as e:
            print(f"produce_point  err: {e}")
            time.sleep(1)


def record_point_count():
    print("开始  循环检测--线程")
    # dict_record_data1 = aicfg.Record_data  # 配置参数
    dict_record_data1 = {
        "max_once_time_length": 6,  # 每遍时长-(分钟)
        "max_times": 1,  # 最大遍数-(次)
        "every_time_length": 1,  # 单次时间间隔-(分钟)
        "every_ok_count": 60,  # 单次达标数量-(个)
        "continuous_times": 5,  # 连续次数-(个)
    }
    record_data1 = [int(dict_record_data1["max_once_time_length"]) * 60, dict_record_data1["max_times"],
                    int(dict_record_data1["every_time_length"]) * 60, dict_record_data1["every_ok_count"],
                    dict_record_data1["continuous_times"], ]
    queue_record_a = queue.Queue(maxsize=int(record_data1[4]))  # 存放个数的队列，长度由配置文件中决定
    for ir in range(int(record_data1[4])):  # 将存放队列写满 0 ，以保证取队列时正常
        if not queue_record_a.full():
            queue_record_a.put(0)
    list_check1 = [0] * int(record_data1[4])  # 记录当前的5次时间段的异纤个数  --每次会覆盖
    # list_bool1 = [0] * int(record_data1[4])  # 记录对应时间段的判断值
    list_start_stop = [0, 0]  # 开始、停止标记位  -需要重置
    old_num = 0  # 前次记录个数
    num_run_time = 0  # 记录时间的段编号
    list_time_run = [None, None, None, ]  # [运行开始时刻-总，运行开始时刻-分段, ]
    list_time_stop = [None, None, None, ]  # [停止开始时刻,  ]
    return_data1 = [0, 0]  # 时间返回 [运行时间，此过程的停止时间]
    bool_if_get_num = False
    global if_need_stop, num_point
    while True:
        time.sleep(0.1)
        try:
            '''时间部分'''
            if if_need_stop == 0:  # 信号停止中
                if list_time_stop[0] is None:  # 初始 或 被满5分钟的条件 清空
                    '''把运行时间看作连续，在运行前的停顿无意义，运行中的停顿肯定在某一个时间段内'''
                    if list_time_run[0] is not None:
                        list_time_stop[0] = time.time()  # 写入此分段中的停顿 初始时间
                        return_data1[1] = 1  # 停顿时长 置为1秒
                        print("第{}个时间段，停顿开始计时".format(num_run_time))
                    else:
                        time.sleep(1)
                else:
                    return_data1[1] = round(time.time() - list_time_stop[0], 2)  # 更新停顿时间

                time.sleep(1)
                continue
            else:  # 处于运行过程中
                if list_time_run[0] is None:  # 只会在第一次运行中执行
                    print("PLC给出运行信号，开始计时检测")
                    list_time_run[0] = time.time()  # 运行开始总计--计时
                    list_time_run[1] = time.time()  # 运行开始分段--计时
                else:
                    len_r1 = round(time.time() - list_time_run[1] - return_data1[1], 2)  # =现在时间-开始时间-停顿时长
                    if len_r1 >= record_data1[2]:  # 现在分段时间 大于 限制时长时
                        # print("len_r1:{}".format(len_r1))
                        '''显示时间刻度'''
                        time_array1 = time.localtime(time.time())  # 格式化时间戳为本地的时间
                        strtime1 = time.strftime("%H:%M", time_array1)
                        time_array2 = time.localtime(list_time_run[1])  # 格式化时间戳为本地的时间
                        strtime2 = time.strftime("%H:%M", time_array2)
                        print("第{}个时间段({}--{}),停顿{}分钟".format(
                            num_run_time + 1, strtime2, strtime1, round(return_data1[1]/60, 1)))
                        '''重置分段计时的变量'''
                        # print("重置分段计时的变量")
                        list_time_run[1] = time.time()  # 运行开始分段--计时--满5分钟重置
                        list_time_stop[0] = None  # 停顿时间清空为None
                        return_data1[1] = 0  # 停顿时长置为0
                        bool_if_get_num = True

                        now_time_length_all = (num_run_time + 1) * record_data1[2]  # 现在运行次数*分段时间
                        if now_time_length_all >= record_data1[0] * record_data1[1]:  # >= 每遍时长*最大遍数
                            print("已经运行{}遍-每遍{}分钟".format(record_data1[1], int(record_data1[0] / 60)))
                            print("发送PLC达标信号")
                            # self.bool_up_to_standard = True
                            list_start_stop[1] = 1  # 触发停止
                    else:  # 不满5分钟时，睡眠跳过
                        time.sleep(1)
                        continue

            '''获取异纤数量部分'''
            if bool_if_get_num:
                bool_if_get_num = False
                num_run_time += 1
                # print("第{}个时间段，开始取数".format(num_run_time))

                now_differ = num_point[4] - old_num  # 此次时段增加的个数
                old_num = copy.deepcopy(num_point[4])  # 前次记录个数
                if queue_record_a.full():  # 把最早的拿出来
                    throw1 = queue_record_a.get()
                queue_record_a.put(now_differ)  # 放入最新的
                for i in range(int(record_data1[4])):
                    list_check1[i] = queue_record_a.get()  # 把现有的全拿出来
                    queue_record_a.put(list_check1[i])
                print("第{}个时间段，最近{}组异纤取数列表:{}".format(num_run_time, int(record_data1[4]), list_check1))

                if list_start_stop[0] == 0:  # 还未开始产生点
                    # 判断是否开始有点产生
                    bool_start1 = (list_check1[0] > int(record_data1[2] / 10)) and \
                                  (list_check1[1] > int(record_data1[2] / 10))
                    if bool_start1:  # 说明产生点了
                        print("判断出有效数据产生，开启判断信号")
                        list_start_stop[0] = 1
                if list_start_stop[0] == 1:  # 开始产生点位后
                    list_bool1 = [0] * int(record_data1[4])  # 对应 判断值列表 清零
                    for il in range(int(record_data1[4])):
                        if list_check1[il] < int(record_data1[3]):  # 当某一个时间段内的数量 小于 设定阈值
                            list_bool1[il] = 1  # 对应 判断值 =1
                    bool_l1 = (sum(list_bool1) == int(record_data1[4]))  # 达标判断
                    if bool_l1:
                        print("发送PLC达标信号")
                        # self.bool_up_to_standard = True
                        list_start_stop[1] = 1  # 触发停止

            '''完成后重置所有变量'''
            if list_start_stop[1] == 1:
                list_start_stop = [0, 0]  # 开始、停止标记位
                return_data1 = [0, 0]  # 时间返回 [运行时间，此过程的停止时间]
                list_time_run = [None, None, None, ]  # [运行开始时刻-总，运行开始时刻-分段, ]
                list_time_stop = [None, None, None, ]  # [停止开始时刻,  ]
                # old_num = 0  # 前次记录个数

                num_run_time = 0  # 记录时间的段编号
                for ir in range(int(record_data1[4])):  # 将存放队列写满 0 ，以保证取队列时正常
                    if queue_record_a.full():
                        throw1 = queue_record_a.get()
                    queue_record_a.put(0)
                time.sleep(3)
                print("达标信号给出，重置所有信号")
                time.sleep(5)

        except Exception as e:
            print(f"record_point_count  err: {e}")
            time.sleep(1)


def main_func1():
    th1 = threading.Thread(target=ctrl_run_stop, args=(), name="ctrl_run_stop")
    th1.start()
    th2 = threading.Thread(target=produce_point, args=(), name="produce_point")
    th2.start()
    th3 = threading.Thread(target=record_point_count, args=(), name="record_point_count")
    th3.start()


def test1():
    list_1 = [2,8]
    for i in range(20):
        if i in range(list_1[0], list_1[1]):  # 左闭右开
            print("{} --ok".format(i))
        else:
            print("{} --ng".format(i))

if __name__ == "__main__":
    main_func1()
    # test1()