import os
import cv2
import time
from AIDeviceCtrl import util
from AIDeviceCtrl.ai_encoder_device import *

'''
@author maoyanwei
多圈0-10V/0-20mA信号编码器，测试代码
详情参考doc下的文档说明
！！！ai_encoder_device实现非线程安全，同一实例不可在多线程下使用（本类静态方法可以在多线程下使用）。！！！
'''
def test_main():
    oDevice = ai_encoder_device()#

    oSerialList = oDevice.list_serial_port()#遍历列表
    print("found serial port：")
    for oInfo in oSerialList:
        print("name: %s, device: %s, description: %s" % (oInfo.name, oInfo.device, oInfo.description))
    #end for

    bResult = oDevice.open("/dev/ttyUSB0")
    print("oDevice.open: ", bResult)
    if not bResult:
        return
    #end if

    try:
        #先读取参数
        strAddress, strParams = oDevice.read_params()
        if strAddress is None:
            print("oDevice.read_params()失败")
            return
        #end if
        print("oDevice.read_params: addr = %s" % strAddress)
        #打印参数描述
        print("oDevice.read_params: params = %s" % ai_encoder_device.param_desc(strParams))

        #设置为被动模式
        if oDevice.set_passive_mode(strAddress):
            print("oDevice.set_passive_mode OK")
        else:
            print("oDevice.set_passive_mode FAILED")
        #end if

        #设置地址
        if oDevice.set_address(strAddress, 78):
            print("oDevice.set_address to 78 OK")
            #测试读取数据
            iData = oDevice.read_data(78)
            print("oDevice.read_data(from 78) = %s" % iData)

            if oDevice.set_address(78, strAddress):
                print("oDevice.set_address 78 to default OK")
            else:
                print("oDevice.set_address FAILED")
            #end if
        else:
            print("oDevice.set_address FAILED")
        #end if

        #测试读取数据
        fStart = time.time()
        for i in range(100):
            iData = oDevice.read_data(strAddress)
            if iData is None:
                print("oDevice.read_data(strAddress) failed")
                break
            #end if
            #print("oDevice.read_data(default) = %s" % iData)
        #end for
        fEnd = time.time()
        print("oDevice.read_data use time %sms" % ((fEnd - fStart) * 1000 / 100))
    finally:
        oDevice.close()
        del oDevice
    #end try

#end def

if __name__ == '__main__':
    test_main()
#end if
