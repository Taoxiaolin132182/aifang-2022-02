import os
import sys
import ctypes
import numpy

from . import util

'''
相关ctypes使用参考python官方文档：
https://docs.python.org/3/library/ctypes.html
'''


'''
python调用c++类
'''
class PythonCallCpp:

    #根据动态库名构造
    def __init__(self, astrLoadLib, abIsStdCall = False):
        try:
            if abIsStdCall:
                self.__hLib = ctypes.windll.LoadLibrary(astrLoadLib)
            else:
                self.__hLib = ctypes.cdll.LoadLibrary(astrLoadLib)
            #end if
        except Exception as e:
            self.__hLib = None
            util.addLog("LoadLibrary %s err: %s" % (astrLoadLib, str(e)))
    #end def

    '''
    析构
    '''
    def __del__(self):
        if not self.__hLib is None:
            del self.__hLib
            self.__hLib = None
    #end def

    #是否有效
    def isValid(self):
        return not self.__hLib is None
    #end def

    '''
    找不到的属性对应到lib对象
    '''
    def __getattr__(self, name):
        if name == "__hLib":
            #eval会导致__getattr__调用（并不会像python文档说的那样先走__getattribute__？）
            return self.__hLib
        #end if
        callFunc = "self.__hLib." + name
        oResult = eval(callFunc)
        if not oResult is None:
            #缓存下次调用加速
            self.__dict__[name] = oResult
        #end if
        #print("call __getattr__(%s)" % name)
        return oResult
    #end def

    '''
    c数组转为numpy数组ndarray
    例子：oCallCpp.ndarrayWithCArray(aryBmp, aoShape = (2, 2, 3), aeDtType = numpy.uint8)
    @param aoCAry C数组
    @param aoShape 指定数组维度，默认是1维数组
    @param aeDtType 指定元素类型，默认自动识别
    '''
    def ndarrayWithCArray(self, aoCAry, aoShape = None, aeDtType = None):
        strOrder = 'C'
        oResult = numpy.array(aoCAry, dtype = aeDtType, copy = False, order = strOrder, subok = False)
        if not aoShape is None:
            oResult = numpy.reshape(oResult, aoShape, order = strOrder)
        #end if
        return oResult
    #end def ndarrayWithCArray

#end class PythonCallCpp


#测试
def test():
    oCallCpp = None

    #测标准c调用
    if util.isWindows():
        oCallCpp = PythonCallCpp(astrLoadLib = "msvcrt.dll", abIsStdCall = False)
    else:
        oCallCpp = PythonCallCpp(astrLoadLib = "libc.so.6", abIsStdCall = False)
    #end if
    if not oCallCpp.isValid():
        return
    #end if
    #整形变量可以不用写ctypes.c_int
    oCallCpp.printf(b"call cpp printf: an int %d, a double %f\n", ctypes.c_int(1234), ctypes.c_double(3.14))
    oCallCpp.printf(b"call cpp printf: a str %s\n", b"haha, i am string")

    #数组
    ArrayInt10 = ctypes.c_int * 10
    aryInt = ArrayInt10()
    print("sizeof(aryInt) = %d" % ctypes.sizeof(aryInt))
    oCallCpp.memset(ctypes.byref(aryInt), -1, ctypes.sizeof(aryInt))

    iLen = len(aryInt)
    for i in range(iLen):
        aryInt[i] += i
    #end for
    for i in aryInt:
        print("i in aryInt = %d" % i)
    #end for

    #cpp数组可以转list
    oList = list(aryInt)
    for i in oList:
        print("i in oList = %d" % i)
    #end for

    #cpp数组转numpy数组
    BmpAryInt = ctypes.c_uint8 * (2 * 2 * 3)
    aryBmp = BmpAryInt()
    aryBmp[0] = 0;aryBmp[1] = 0;aryBmp[2] = 255;        #red
    aryBmp[3] = 0;aryBmp[4] = 255;aryBmp[5] = 0;        #green
    aryBmp[6] = 255;aryBmp[7] = 0;aryBmp[8] = 0;        #blue
    aryBmp[9] = 255;aryBmp[10] = 255;aryBmp[11] = 255;  #white
    ndBmpArray = oCallCpp.ndarrayWithCArray(aryBmp, aoShape = (2, 2, 3))
    import cv2
    cv2.namedWindow("test", cv2.WINDOW_NORMAL)
    cv2.imshow("test", ndBmpArray)
    cv2.resizeWindow("test", 128, 128)
    cv2.waitKey()
    cv2.destroyAllWindows()
    del oCallCpp

    #测stdcall
    if util.isWindows():        
        oCallCpp = PythonCallCpp(astrLoadLib = "User32.dll", abIsStdCall = True)
        iResult = oCallCpp.MessageBoxA(0, b"hello, messagebox", b"i am title", 0x40)
        del oCallCpp
        print("MessageBoxA return %d" % iResult)
    #end if

#end def

if __name__ == '__main__':
    test()
