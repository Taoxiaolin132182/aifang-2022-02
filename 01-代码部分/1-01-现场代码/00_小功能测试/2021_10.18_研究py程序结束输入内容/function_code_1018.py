# coding=utf-8
import time
import os
import sys
import copy
# import subprocess
from subprocess import Popen, PIPE, STDOUT
import threading

should_be_path = "/opt/app/ai-product-haijiang/ai-hj-service/aiHjService/"
process_name_list1 = ["test_run.py", "daemon.py", "ai_hj_run_service.py"]
log_path_list1 = ["/mnt/data/data/3test_code/t_run.log", "/opt/logs/txl01/daemon.log", "/opt/logs/txl01/ctrl.log"]
pwd_p = "Welcome!@#"

'''开启程序-函数'''
def start_program(num1, bool_ori=True):
    pro_n1 = process_name_list1[num1]
    print("启动程序--先确认是否存在进程")
    stop_program(pro_n1, False)
    # 对 重定向文件 创建和赋权限
    if not os.path.exists(log_path_list1[num1]):
        cmd_log1 = "touch " + log_path_list1[num1]
        os.system(cmd_log1)
        print("创建了 重定向文件：{}".format(log_path_list1[num1]))
    cmd_log1 = "chmod 777 " + log_path_list1[num1] + " &"
    os.system(cmd_log1)
    print("对重定向文件：{} 赋权限".format(log_path_list1[num1]))
    if bool_ori:
        cmd_str = "echo %s|sudo -S nohup python3 %s > %s 2>&1 &" % (pwd_p, pro_n1, log_path_list1[num1])
    else:
        process_path1 = should_be_path + pro_n1
        cmd_str = "echo %s|sudo nohup python3 %s > %s 2>&1 &" % (pwd_p, process_path1, log_path_list1[num1])
        # cmd_str = "nohup python3 %s > %s 2>&1 &" % (process_path1, log_path_list1[num1])
    print("cmd_str:{}".format(cmd_str))
    result = os.system(cmd_str)
    if result == 0:
        print("\n@@@@@@     {} 程序已启动\n".format(pro_n1))
    else:
        print("\n程序启动失败\n")

'''关掉程序-函数'''
def stop_program(pro_name_stop, for_start=True):
    if for_start:
        print("001、准备--关闭程序")
    pro_n1 = pro_name_stop
    print("002、读取{}程序进程号".format(pro_n1))
    now_pro_id = search_process(pro_n1)
    if now_pro_id is None:
        print("003、程序：{} 不在运行\n".format(pro_n1))
    else:
        print("003、{} 程序进程号为：{}".format(pro_n1, now_pro_id))
        cmd_str2 = "kill -9 " + now_pro_id
        res1 = os.system(cmd_str2)
        if res1 == 0:
            print("\n004、结束{} 的进程 {}\n".format(pro_n1, now_pro_id))
        else:
            print("\n004、结束进程--失败\n")

# '''根据程序名称 搜索进程号--(自己写的)'''
# def search_process(pro_name, bool_ori=True):
#     now_id = 0
#     cmd_str1 = "ps -ef|grep " + pro_name
#     pid1 = os.popen(cmd_str1)
#     message1 = pid1.readlines()  # type: list
#     for line in message1:
#         # print("查询进程-过程:{}".format(line))
#         line2 = line.split("   ")
#         # if bool_ori:
#         #     bool_j = ("python3 " + pro_name) in line
#         # else:
#         bool_i1 = ("python3 " + pro_name) in line
#         bool_i2 = ("python3 " + should_be_path + pro_name) in line
#         bool_j = bool_i1 or bool_i2
#         # print("bool_j:{}".format(bool_j))
#         if (line2[0] == "root") and bool_j:
#             line3 = line2[1].strip(" ")
#             line4 = line3.split(" ")
#             if int(line4[0]) > now_id:
#                 now_id = copy.deepcopy(int(line4[0]))
#     if now_id == 0:
#         now_id = None
#     else:
#         now_id = str(now_id)
#     # print("process id :{}".format(now_id))
#     return now_id

'''根据程序名称 搜索进程号--(自己写的-优化)'''
def search_process(pro_name, bool_ori=True):
    now_id = None
    for i in range(2):
        if i < 1:
            cmd_str1 = "pgrep -f 'python3 {}'".format(pro_name)
        else:
            cmd_str1 = "pgrep -f 'python3 {}'".format(should_be_path + pro_name)
        # print("cmd_str1:{}".format(cmd_str1))
        pid1 = os.popen(cmd_str1)
        message1 = pid1.readlines()  # type: list
        # print("message1:{}".format(message1))
        if len(message1) > 1:
            now_id = message1[-2].replace("\n", "")
        # print("process id :{}".format(now_id))
    return now_id

'''根据程序名称 搜索进程号--(游江的模板)'''
def check_process_exist(process_key):
    # print("(subprocess)查询进程 %s 是否存在" % process_key)
    cmd_need1 = "python3 " + process_key
    child = Popen(["pgrep", "-f", cmd_need1], stdout=PIPE, shell=False)
    pid = child.communicate()[0]
    cmd_need2 = "python3 " + should_be_path + process_key
    print("cmd_need2:{}".format(cmd_need2))
    child2 = Popen(["pgrep", "-f", cmd_need2], stdout=PIPE, shell=False)
    pid2 = child2.communicate()[0]
    print("pid1:{} , pid2:{}  ".format(pid, pid2))
    if not pid or len(pid) == 0:
        if not pid2 or len(pid2) == 0:
            print("the [%s] process is not exist" % process_key)
            return None
        else:
            pid_str = str(pid2, encoding="utf-8").strip()  # bytes to string
    else:
        pid_str = str(pid, encoding="utf-8").strip()  # bytes to string
    if pid_str.find('\n') > 0:
        pids = pid_str.split('\n')
        pid = pids[-1]
    # print("(subprocess)process id : {}".format(pid_str))
    return pid

'''获取 命令中的输入字符'''
def receive_input_message1():
    '''
    help : 查询 守护进程，和主程序  是否运行
    stop : kill 掉当前主程序进程
    stop all : kill 掉当前守护进程 + 主程序进程
    start: 开启 主程序
    start all: 开启 守护进程
    '''
    # print("= = = = = = = = = = = = = =")
    # print(" = = = = = = = = = = = = = =")
    # print("程序开始")
    choose_num = [1, 0]   # [守护进程下标, 主进程下标]
    bool_print_tis = False
    allow_message1 = ['help', 'start', 'stop', 'restart', 'all']
    simple_message1 = ['-h', '-r', '-p', '-k', 'a']
    get_mess1 = sys.argv   # ['function_code_1018.py', 'start', 'stop', 'restart']
    # print("接收的信息：{}\n".format(get_mess1))
    nowpath = get_my_path()  # 获取当前路径
    bool_r = check_paths(nowpath)  # 检查是否在目标路径(相同为True，不同为False)
    if not bool_r:
        print("\n请将本文件放入下面路径下：\n{}".format(should_be_path))
        print("\n 否则无法执行")
        time.sleep(0.5)
        os._exit(0)

    if len(get_mess1) > 1:  # 当输入的内容 大于1个时--[0]是本程序名称
        if (get_mess1[1] == allow_message1[1]) or (get_mess1[1] == allow_message1[3]) or \
                (get_mess1[1] == simple_message1[1]) or (get_mess1[1] == simple_message1[3]):
            if len(get_mess1) == 2:  # 符合 start
                print("\n(start) 开启 主程序\n=================")
                start_program(choose_num[1], bool_r)
            else:  # 由 第二个输入时
                if (get_mess1[2] == allow_message1[-1]) or (get_mess1[2] == simple_message1[-1]):
                    print("\n(start all) 开启 守护进程\n=================")
                    start_program(choose_num[0], bool_r)
                else:
                    bool_print_tis = True
        elif (get_mess1[1] == allow_message1[2]) or (get_mess1[1] == simple_message1[2]):
            if len(get_mess1) == 2:  # 符合 stop
                print("\n(stop) kill 掉当前主程序进程\n=================")
                stop_program(process_name_list1[choose_num[1]])
            else:
                if (get_mess1[2] == allow_message1[-1]) or (get_mess1[2] == simple_message1[-1]):
                    print("\n(stop all) kill 掉当前守护进程 + 主程序进程\n=================")
                    stop_program(process_name_list1[choose_num[0]])
                    time.sleep(0.5)
                    print("\n(stop all) - - - - - - - - -")
                    stop_program(process_name_list1[choose_num[1]])
                else:
                    bool_print_tis = True
        # help 部分
        elif (get_mess1[1] == allow_message1[0]) or (get_mess1[1] == simple_message1[0]):
            print("\n(help) 查询 守护进程，和主程序  是否运行\n=================")
            now_pro_id1 = search_process(process_name_list1[choose_num[0]])
            # now_pro_id1 = check_process_exist(process_name_list1[choose_num[0]])
            if now_pro_id1 is None:
                print("(help) 守护进程 不在运行")
            else:
                print("(help) 守护进程 正在运行，进程号为：{}".format(now_pro_id1))
            # print("\n")
            now_pro_id2 = search_process(process_name_list1[choose_num[1]])
            # now_pro_id2 = check_process_exist(process_name_list1[choose_num[1]])
            if now_pro_id2 is None:
                print("(help) 主程序 不在运行")
            else:
                print("(help) 主程序 正在运行，进程号为：{}".format(now_pro_id2))
            str_cmd = [allow_message1[1], allow_message1[2], allow_message1[1] + " " + allow_message1[-1],
                       allow_message1[2] + " " + allow_message1[-1], ]
            print("\n(help) @@@可添加输入字符:{}\n".format(str_cmd))
            str_cmd_s = [simple_message1[1], simple_message1[2], simple_message1[1] + " " + simple_message1[-1],
                       simple_message1[2] + " " + simple_message1[-1], ]
            print("(help) @@@可添加输入字符(精简):{}\n".format(str_cmd_s))

        else:  # 输入内容不正确
            bool_print_tis = True
    else:
        print("\n没有进行 任何输入\n")
        print("请输入列表中字符：{}\n".format(allow_message1[:4]))
        print("或是输入精简字符：{}\n".format(simple_message1[:4]))
    if bool_print_tis:
        print("输入的 '{}' 字符不匹配\n请输入列表中字符：{}\n".format(get_mess1[1:], allow_message1[:4]))
        print("或是输入精简字符：{}\n".format(simple_message1[:4]))
'''获取当前文件的所在路径'''
def get_my_path():
    now_path = os.path.abspath(__file__)  # 包含文件本身名称
    now_path_up = os.path.dirname(now_path)
    print("\n当前脚本所在路径为：{}".format(now_path_up))
    return now_path_up

'''检查是否在目标路径'''
def check_paths(path1):
    now_path1 = path1 + "/"
    if now_path1 == should_be_path:
        bool_new_path = True
    else:
        bool_new_path = False
    print("所在路径 是否为 目标路径：{}".format(bool_new_path))
    return bool_new_path


'''主函数'''
def main_func1():
    # nowpath = get_my_path()
    # bool_r = check_paths(nowpath)
    receive_input_message1()
    pass

if __name__ == "__main__":
    main_func1()