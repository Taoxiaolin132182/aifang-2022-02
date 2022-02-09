import os
import sys
import ctypes
import time

import test_cython

if __name__ == '__main__':
    test_cython.say_hello_to("test cython ok")

    #test_cython.test_python_thread()
    test_cython.test_cppthread_callpython()

    print("python主线程循环开始")
    while True: pass
    print("python主线程循环结束")
    sys.exit(0)

#end if
