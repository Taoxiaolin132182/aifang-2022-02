# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
import os, json, copy, time, threading

'''需要配置的参数'''
config_choose_for_arm = 1  # ARM编号： 1 or 2
sys_num = 1  # windows: 0 || linux: 1
bool_unlock = [False, 480, None, []]  # [全局开关，时间限制，时间戳，登录IP]
if_use_1 = 0  # 0 为可用， 非0为 不可用
list_for_parameter = ["5.91", "5.91"]  # 传送带速度比率参数[高处，低处](一般是相同的，但有不同的情况(河南盛泰1.1))

# --------     -----------   ---------
bool_auto_stop = True
path_cfg_list = [
    r"C:\001chengxu\04\2020twelve_1207\08_web_test\test_base_func1\af-config.txt",
    r"/mnt/data/data/aimodel/af-config.txt", ]
path_cfg1 = path_cfg_list[sys_num]
tips = {"tips1": "<300整数", "tips2": "<1000内整数", "tips3": "<2小数"}
index_mes1 = [
                "<a href='/index/'>   首页   </a>",
                "<a href='/show12/'>  2抓手配置  </a>",
                "<a href='/show14/'>  4抓手配置  </a>",
                "<a href='https://www.baidu.com/'>   百度   </a>",
                str(config_choose_for_arm)
            ]

'''读取txt input:完整路径  output: 是否异常结果'''
def read_txt1(path_txt1):
    bool_read_ok = False  # 读取是否异常
    message1 = None
    try:
        if os.path.exists(path_txt1):
            print("\n==================\n开始读取txt信息\n")
            print("{} 此文件存在".format(path_txt1))
            # encoding=  gbk utf-8 ansi
            with open(path_txt1, "rb") as f_str:
                message1 = json.load(f_str)
                # print("读取内容为：\n{}".format(message1))
                # print("信息个数：{}".format(len(message1)))
                # print("信息类型：{}".format(type(message1)))

            print("读取txt配置文件，完成")
            bool_read_ok = True
        else:
            print("{} 该文件不存在".format(path_txt1))
    except Exception as e:
        print(f"read_txt1  err: {e}")
    return bool_read_ok, message1

'''把信息写入 txt'''
def write_change_mes(path_w, data1):
    if data1 is None:
        global if_use_1
        data1 = {
            "bool_use": if_use_1,
            "claw1": {"x": [0, 0, 0], "y": [0, 0, 0], "t": [0, 0, 0]},
            "claw2": {"x": [0, 0, 0], "y": [0, 0, 0], "t": [0, 0, 0]},
            "claw3": {"x": [0, 0, 0], "y": [0, 0, 0], "t": [0, 0, 0]},
            "claw4": {"x": [0, 0, 0], "y": [0, 0, 0], "t": [0, 0, 0]}}
    with open(path_w, "w") as f_dict:
        f_dict.write(json.dumps(data1))  # 开始存信息，写入txt文件
    # time.sleep(0.2)
    # cmd_str1 = "cp " + path_w + " /mnt/data/data/aimodel/"
    # os.system(cmd_str1)
    return data1

'''控制print 是否打印 函数'''
def ctrl_print(mess,bool_show=False):  # bool_show = True(显示)， = False(不显示)
    if bool_show:
        print(mess)

'''获取当前文件的所在路径'''
def get_my_path():
    now_path = os.path.abspath(__file__)  # 包含文件本身名称
    print("\n当前脚本所在完整路径为：{}".format(now_path))
    now_path_up = os.path.dirname(now_path)
    print("\n当前脚本所在路径为：{}".format(now_path_up))
    return now_path_up


'''处理得到的每个元素(字符串)'''
def deal_input_data1(name, data):
    bool_res1 = 0
    if "x" in name:
        res_d1 = int(float(data))
        if (res_d1 < -300) or (res_d1 > 300):
            res_d1 = ""
            bool_res1 = 1
    elif "y" in name:
        res_d1 = int(float(data))
        if (res_d1 < -1000) or (res_d1 > 1000):
            res_d1 = ""
            bool_res1 = 1
    else:
        res_d1 = round(float(data), 3)
        if (res_d1 < -2) or (res_d1 > 2):
            res_d1 = ""
            bool_res1 = 1
    return bool_res1, res_d1


def show_mes2(request):
    global index_mes1, bool_unlock, path_cfg1, tips
    bool_can_run = False
    error_mes1 = ""
    "1层登录锁，2层IP核对，3层时间锁"
    ip = get_ip(request)  # 获取访问端 IP
    if bool_unlock[0]:  # 1层登录锁
        if ip == bool_unlock[3][0]:  # 2层IP核对
            if time.time() - bool_unlock[2] <= bool_unlock[1]:  # 3层时间锁
                boll_res, res_data1 = read_txt1(path_cfg1)  # 读取 txt 文件，失败返回 False, None
                if not boll_res:
                    print("读取配置文件失败, 开始赋予初始值")
                    res_data1 = write_change_mes(path_cfg1, res_data1)  # 写入初始值，并返回来(危险项，会重置掉原来的记录)
                '''处理 承接页面的 参数字段'''
                ctx = copy.deepcopy(res_data1)  # 拷贝给ctx 参数，后面会和post后的值作比较
                link1 = {"data_1": index_mes1}
                res_post = {"data": ctx, "tip": tips, "link1": link1}
                if request.POST:  # 当post 有返回时
                    str_list1 = [["1", "2"], ["x", "y", "t"], ["a", "b", "c"]]
                    # 根据上面的列表 比对分析 获取到的数据
                    get_claw_param(str_list1, ctx, res_data1, request)
                    bool_can_run = True
                return render(request, "show-mes2.html", res_post)
            else:
                bool_unlock[0] = False  # 登录锁重置
                bool_unlock[3] = []  # IP对比项清空
                error_mes1 = "登录超时，请重新登录"
        else:
            error_mes1 = "已有登录者，请稍后再试"
    else:
        error_mes1 = "未登录，请先登录"
    if not bool_can_run:
        rec_data = {"error": error_mes1}
        return render(request, "login.html", rec_data)

def show_mes4(request):
    global index_mes1, bool_unlock, path_cfg1, tips
    bool_can_run = False
    error_mes1 = ""
    "1层登录锁，2层IP核对，3层时间锁"
    ip = get_ip(request)  # 获取访问端 IP
    if bool_unlock[0]:  # 1层登录锁
        if ip == bool_unlock[3][0]:  # 2层IP核对
            if time.time() - bool_unlock[2] <= bool_unlock[1]:  # 3层时间锁
                boll_res, res_data1 = read_txt1(path_cfg1)  # 读取 txt 文件，失败返回 False, None
                if not boll_res:
                    print("读取配置文件失败, 开始赋予初始值")
                    res_data1 = write_change_mes(path_cfg1, res_data1)  # 写入初始值，并返回来(危险项，会重置掉原来的记录)
                '''处理 承接页面的 参数字段'''
                ctx = copy.deepcopy(res_data1)  # 拷贝给ctx 参数，后面会和post后的值作比较
                link1 = {"data_1": index_mes1}
                res_post = {"data": ctx, "tip": tips, "link1": link1}
                if request.POST:  # 当post 有返回时
                    str_list1 = [["1", "2", "3", "4"], ["x", "y", "t"], ["a", "b", "c"]]
                    # 根据上面的列表 比对分析 获取到的数据
                    get_claw_param(str_list1, ctx, res_data1, request)
                    bool_can_run = True
                return render(request, "show-mes4.html", res_post)
            else:
                bool_unlock[0] = False  # 登录锁重置
                bool_unlock[3] = []  # IP对比项清空
                error_mes1 = "登录超时，请重新登录"
        else:
            error_mes1 = "已有登录者，请稍后再试"
    else:
        error_mes1 = "未登录，请先登录"
    if not bool_can_run:
        rec_data = {"error": error_mes1}
        return render(request, "login.html", rec_data)

def index_t1(request):
    global index_mes1
    add_mes1 = "<a href='/instructions/'> 补偿参数说明 </a>"
    mes_cp2 = copy.deepcopy(index_mes1)
    mes_cp2.append(add_mes1)
    res_post_index = {"data_1": mes_cp2}
    return render(request, "index-1.html", res_post_index)

def instructions_t1(request):
    global index_mes1, config_choose_for_arm, list_for_parameter

    now_param = list_for_parameter[int(config_choose_for_arm) - 1]
    mes_cp1 = copy.deepcopy(index_mes1)
    mes_cp1[4] = now_param
    res_post_index = {"data_1": mes_cp1}
    return render(request, "instructions_1.html", res_post_index)


# 加载登录界面
def login(request):
    return render(request, "login.html")

# 验证登录
def do_login(request):
    global bool_unlock  # 引用全局变量 登录时间锁+ IP
    bool_can_login = False  # 局部变量 登录可行信号
    error_mes1 = ""
    can_list = ["admin", "Welcome!@#"]  # 暂时设定的登录账号和密码
    username = request.POST.get('username')  # 获取页面端的用户名
    password = request.POST.get('password')  # 获取页面端的密码
    # print("User:{} -- Password:{}".format(username, password))
    if username == can_list[0] and password == can_list[1]:  # 登录账号和密码 符合
        '''获取网页访问端的IP'''
        ip = get_ip(request)
        '''判断上面获取的IP 和现有的是否吻合'''
        if len(bool_unlock[3]) == 0:  # 如果IP未添加(初始 或 时间重置)
            bool_unlock[3].append(ip)
            bool_can_login = True  # 确认可行
        else:  # 已有IP，先考虑是否同一个，
            if bool_unlock[3][0] == ip:  # IP符合
                bool_can_login = True  # 确认可行
            else:  # 不同时，看是否上一个已超时
                if time.time() - bool_unlock[2] <= bool_unlock[1]:  # 3层时间锁
                    error_mes1 = "已有登录者，请稍后再试"
                else:
                    bool_can_login = True  # 确认可行
                    bool_unlock[3][0] = ip
    else:
        error_mes1 = "账号或密码错误"
    '''合法登录'''
    if bool_can_login:
        '''打印pid'''
        get_pid()
        bool_unlock[0] = True  # 开锁
        bool_unlock[2] = time.time()  # 起始时间戳
        return redirect('/index/')  # 导航地址
    else:
        rec_data = {"error": error_mes1}  # 异常提示
        return render(request, "login.html", rec_data)  # 登录页面

'''获取网页访问端的IP'''
def get_ip(request):
    try:
        xff1 = request.META.get('HTTP_X_FORWARDED_FOR')
        print("xff1:{}".format(xff1))
        if xff1:
            ip = xff1.split(",")[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        print("IP:{}".format(ip))
        return ip
    except Exception as e:
        print(f"get_ip --- err: {e}")

'''获取网页录入字段 分析写入'''
def get_claw_param(str_list1, ctx, res_data1, request):
    bool_err = 0
    if len(str_list1) == 3:  # 设定列表
        for num1 in str_list1[0]:  # 分几个抓手
            claw_name1 = "claw" + num1
            for value1 in str_list1[1]:  # 分 位置参数xyt
                for cid in range(len(str_list1[2])):  # 分 相机号
                    c_name1 = value1 + num1 + str_list1[2][cid]
                    h_name1 = "h" + c_name1  # 构成页面参数名
                    res_xyt = request.POST[h_name1]
                    if len(res_xyt) == 0:
                        continue
                    bool_res1, d_res1 = deal_input_data1(c_name1, res_xyt)  # 处理得到的每个元素(字符串)
                    bool_err += bool_res1  # 出错次数累加
                    if bool_err > 0:  # 一旦录入出错，放弃
                        break
                    ctx[claw_name1][value1][cid] = d_res1  # 把现有值更新到 更新字典
        if bool_err > 0:  # 出错输出
            print("数据输出错误, 不进行写入")
        else:
            # print("收到数据：{}".format(ctx))
            if ctx != res_data1:  # 有合法的不同值 录入
                write_change_mes(path_cfg1, ctx)
                print("数据写入txt文档")
            else:
                print("修改内容一致，无需写入")

def get_pid():
    global bool_auto_stop
    if bool_auto_stop:
        bool_auto_stop = False
        pid_child = os.getpid()
        pid_parent = os.getppid()
        print("本程序进程：{}".format([pid_child, pid_parent]))
        th4_signal = threading.Thread(target=stop_job1, args=(), name="stop_job1")
        th4_signal.start()

def stop_job1():
    first_time = time.time()
    limit_time = 60 * 15
    while True:
        time.sleep(2)
        if time.time() - first_time > limit_time:
            print("已到达设定时间，退出程序")
            break
    os._exit(0)
