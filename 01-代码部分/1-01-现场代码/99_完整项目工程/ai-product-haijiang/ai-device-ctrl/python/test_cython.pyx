import os
import sys
import ctypes
import time

from concurrent.futures import ThreadPoolExecutor

#确保取到真正的脚本目录，不要用sys.path[0]
TASK_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
strLoadLib = os.path.join(TASK_PY_PATH, "AIDeviceCtrlDll.dll")
hLib = ctypes.cdll.LoadLibrary(strLoadLib)
hLib.cc_use_cpu.restype = None


def py_thread_call_py():
    print("python线程：py_thread_call_py开始")
    while True: pass
    print("python线程：py_thread_call_py退出")
#end def

def py_thread_call_cpp():
    print("python线程：py_thread_call_cpp开始")
    hLib.cc_use_cpu()
    print("python线程：py_thread_call_cpp退出")
#end def

def cpp_thread_call_py():
    print("cpp线程：cpp_thread_call_py开始")
    while True: pass
    print("cpp线程：cpp_thread_call_py退出")
#end def

cpp_thread_call_py_t = ctypes.CFUNCTYPE(None)
cpp_thread_call_py_callback = cpp_thread_call_py_t(cpp_thread_call_py)
hLib.cc_call_python.argtypes = [cpp_thread_call_py_t]
hLib.cc_call_python.restype = None


def say_hello_to(name):
    print("Hello %s!" % name)
#end def


def test_python_thread():
    print("准备启动2个py_thread_call_py")
    oPool = ThreadPoolExecutor(2, "TestPool")
    oPool.submit(py_thread_call_py)
    oPool.submit(py_thread_call_py)
#end def

def test_cppthread_callpython():
    print("准备启动2个cpp_thread_call_py")
    hLib.cc_call_python(cpp_thread_call_py_callback)
    hLib.cc_call_python(cpp_thread_call_py_callback)
#end def
