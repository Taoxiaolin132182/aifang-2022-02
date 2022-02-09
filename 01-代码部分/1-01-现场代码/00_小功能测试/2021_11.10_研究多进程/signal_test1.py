# coding=utf-8
import signal
import os
import time

def handle_signal(signum,frame):
    print('Received and handle:',signum)

def handle_test1(signum1,frame):
    print('--test--Received and handle:',signum1)
    print("I will stop process")
    time.sleep(1)
    os._exit(0)

#注册信号处理程序
signal.signal(signal.SIGUSR1, handle_signal)
signal.signal(signal.SIGUSR2, handle_signal)
signal.signal(signal.SIGINT, handle_test1)

def main_func1():
    print("The process's PID is:",os.getpid())
    num1 = 0
    while True:
        num1 += 1
        print('Waiting...{}'.format(num1))
        time.sleep(2)


if __name__ == "__main__":
    main_func1()