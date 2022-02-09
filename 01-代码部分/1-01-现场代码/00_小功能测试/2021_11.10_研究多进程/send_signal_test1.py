# coding=utf-8
import signal
import os, sys
import time




def main_func1():
    print("准备发送 signal ")
    get_mess1 = sys.argv  # ['function_code_1018.py', 'start', 'stop', 'restart']
    print("get_mess1:{}".format(get_mess1))
    if len(get_mess1) > 1:
        try:
            id_p = int(get_mess1[1])
            os.kill(id_p, signal.SIGUSR1)
            # time.sleep(5)
            # os.kill(id_p, signal.SIGUSR2)
            # time.sleep(5)
            # os.kill(id_p, signal.SIGINT)

        except Exception as e:
            print("error input ID: {}".format(e))
    else:
        print("没用输入 任何内容")

if __name__ == "__main__":
    main_func1()