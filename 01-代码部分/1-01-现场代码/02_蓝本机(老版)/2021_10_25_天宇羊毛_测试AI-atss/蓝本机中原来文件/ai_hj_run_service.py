# coding=utf-8
import time
import os
import sys
import threading


def start_program():
    print("启动程序")
    pass

def stop_program():
    print("关闭程序")
    pass

def search_process():
    pass
def receive_input_message1():
    print("程序开始")
    allow_message1 = ['start', 'stop', 'restart']
    get_mess1 = sys.argv   # ['function_code_1018.py', 'start', 'stop', 'restart']
    print("接收的信息：{}".format(get_mess1))

    if len(get_mess1) > 1:
        if (get_mess1[1] == allow_message1[0]) or (get_mess1[1] == allow_message1[2]):
            start_program()
        elif get_mess1[1] == allow_message1[1]:
            stop_program()
        else:
            if len(get_mess1) == 2:
                print("输入的 '{}' 字符不匹配\n请输入列表中字符：{}".format(get_mess1[1], allow_message1))
            else:
                print("输入的 {} 字符不匹配\n请输入列表中字符：{}".format(get_mess1[1:], allow_message1))
    else:
        print("没有进行任何输入")

def keep_run():
    for i in range(8888):
        print("第{}次等待，每次10秒".format(i + 1))
        time.sleep(0.5)

def backup_signal():
    init_flag = "init.txt"
    if os.path.exists(init_flag):
        os.remove(init_flag)
    try:
        f = open(init_flag, "w")
        f.write("success")
        f.close()
    except:
        print("write init status error =======")

def main_func1():
    backup_signal()
    keep_run()
    # receive_input_message1()
    pass

if __name__ == "__main__":
    main_func1()