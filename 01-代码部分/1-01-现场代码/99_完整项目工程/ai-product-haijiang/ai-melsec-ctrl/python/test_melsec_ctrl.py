import os
import sys
#import cv2
import time
from melsec_ctrl.melsec_ctrl import melsec_ctrl

#确保取到真正的脚本目录，不要用sys.path[0]
TASK_PY_PATH = os.path.split(os.path.realpath(__file__))[0]

'''
@author maoyanwei
本文件测试melsec_ctrl类
'''

#测试
def test():
    #创建控制对象
    oCtrl = melsec_ctrl()
    bResult = oCtrl.open(("192.168.1.250", 10002))
    if not bResult:
        print("打开设备连接失败")
        sys.exit(1)
        return
    #end if

    #测试远程控制命令
    bResult = oCtrl.remote_run()
    print("远程启动命令结果：", bResult)

    ########## 测试按位读写 #############
    #写9个bit
    strSoftAddr = "M2000"
    btWriteData = [0, 1, 1, 1, 0, 0, 0, 1, 1]
    bResult = oCtrl.write_bit_data(strSoftAddr, btWriteData)
    print("write_bit_data结果：", "成功：" if bResult else "失败：", btWriteData)
    if bResult:
        #读刚才写入的bit个数，校验对不对
        btReadData = oCtrl.read_bit_data(strSoftAddr, len(btWriteData))
        if btReadData is None:
            print("read_bit_data失败")
            sys.exit(1)
            return
        #end if
        #校验是否和写入的一致
        if len(btWriteData) != len(btReadData):
            print("read_bit_data虽然成功，但获取的数据长度错误")
            sys.exit(1)
            return
        #end if
        for i in range(len(btWriteData)):
            if btWriteData[i] != btReadData[i]:
                print("read_bit_data虽然成功，但获取的数据值错误：", btReadData)
                sys.exit(1)
                return
            #end if
        #end for
        print("read_bit_data成功，且和write_bit_data写入时内容一致")
    #end if

    ########## 测试按字读写 #############
    #写4个word
    strSoftAddr = "D5000"
    btWriteData = [0x1234, 0x5678, 0x7890, 0x9527]
    bResult = oCtrl.write_word_data(strSoftAddr, btWriteData)
    print("write_word_data = ", "成功：" if bResult else "失败：", btWriteData)
    if bResult:
        #读刚才写入的word个数，校验对不对
        btReadData = oCtrl.read_word_data(strSoftAddr, len(btWriteData))
        if btReadData is None:
            print("read_word_data失败")
            sys.exit(1)
            return
        #end if
        #校验是否和写入的一致
        if len(btWriteData) != len(btReadData):
            print("read_word_data虽然成功，但获取的数据长度错误")
            sys.exit(1)
            return
        #end if
        for i in range(len(btWriteData)):
            if btWriteData[i] != btReadData[i]:
                print("read_word_data虽然成功，但获取的数据值错误：", btReadData)
                sys.exit(1)
                return
            #end if
        #end for
        print("read_word_data成功，且和write_word_data写入时内容一致")
    #end if

    #另有双字读写，可以测试下
    #write_dword_data/read_dword_data

    #测试远程控制命令
    #bResult = oCtrl.remote_stop()
    #print("远程停止命令结果：", bResult)

    #关闭
    oCtrl.close()
    del oCtrl
#end def test

if __name__ == '__main__':
    test()
