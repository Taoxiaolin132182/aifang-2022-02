# coding=utf-8

import os
import sys
import time
import ctypes
import traceback
import serial #安装包名pyserial
import serial.tools.list_ports

from . import config
from . import util

'''
@author maoyanwei
多圈4-20mA模拟电流 值编码器，多圈0-10V/0-20mA信号编码器
详情参考doc下的文档说明
！！！本实现非线程安全，同一实例不可在多线程下使用（本类静态方法可以在多线程下使用）。！！！
'''
class ai_encoder_device:
    #构造
    def __init__(self, baudrate = 19200, timeout = 1.0):
        self.__oSer = serial.Serial()
        self.baudrate = baudrate
        self.timeout = timeout
    #end def

    #析构
    def __del__(self):
        #print("~ai_encoder_device")
        self.close()
    #end def

    '''
	 获取当前串口列表
	 @return 返回当前串口列表
    '''
    def list_serial_port(self):
        try:
            oList = list(serial.tools.list_ports.comports())
            return oList
        except Exception as e:
            print(e)
            return []
        #end try
    #end if

    #关闭通讯
    def close(self):
        util.safeWork(lambda: self.__oSer.close())
    #end def

    '''
    打开串口控制
    @param astrComPort 串口名
    @return 成功打开返回True
    '''
    def open(self, astrComPort):
        try:
            if self.__oSer.is_open:
                #已经打开了
                return False
            #end if

            '''
            通讯协议RS485
            支持波特率：4800bps. 9600bps. 19200bps. 38400bps. 115200bps.
            帧格式：数据位8位，停止位1位，无奇偶校验，无控制流。
            '''
            self.__oSer.port = astrComPort
            self.__oSer.baudrate = self.baudrate
            self.__oSer.bytesize = serial.EIGHTBITS
            self.__oSer.stopbits = serial.STOPBITS_ONE
            self.__oSer.parity = serial.PARITY_NONE
            self.__oSer.timeout = 0.001
            self.__oSer.write_timeout = self.timeout
            self.__oSer.open()

            return self.__oSer.is_open

        except Exception as e:
            print(e)
            self.close()
            return False
        #end try
    #end def

    '''
    ASCII 码参数    ASCII 码参数
    01 4800bps波特率 02 9600bps波特率
    03 19200bps 波特率  04 38400bps波特率
    05 115200bps波特率
    09 被动模式
    06 顺时针数据加 10 循环模式
    07 逆时针数据加 11 往复模式
    08 主动模式
    '''
    PARAM_MAP = \
        { 
            0x01 : "4800bps", 0x02 : "9600bps", 0x03 : "19200bps", 0x04 : "38400bps", 0x05 : "115200bps",
            0x06 : "顺时针数据加", 0x07 : "逆时针数据加", 0x08 : "主动模式", 0x09 : "被动模式", 
            0x10 : "循环模式", 0x11 : "往复模式"
        }

    '''
    参数值返回对应描述
    @param params 参数字符串
    @return 成功返回对应的描述，失败返回""
    '''
    @staticmethod
    def param_desc(params):
        try:
            strResult = ""
            for s in params:
                k = ord(s)
                v = ai_encoder_device.PARAM_MAP.get(k, "未知%s" % k)
                strResult += (v + ",")
            #end for
            return strResult[0:len(strResult)] if len(strResult) > 0 else ""
        except Exception as e:
            exstr = traceback.format_exc()
            print(exstr)
            print(e)
            return ""
        #end try
    #end def

    '''
    读取编码器参数
    @return 成功返回(地址, 参数)，
            失败返回(None, None)
    '''
    def read_params(self):
        try:
        #上位机发送：D+00+A+0D      编码器回：X+地址+a+方向+波特率+工作状态+工作模式+0D
        #例：上位机发送：44 00 41 0D       编码器回：58 30 31 61 06 03 11 09 0D
        #(编码器地址01，顺时针增加，波特率19200，往复模式，被动模式。）
            if not self.__oSer.is_open:
                #没有打开，失败
                raise Exception("read_params: must call open")
            #end if

            btBuf = bytearray(4)
            btBuf[0] = 0x44
            btBuf[1] = 0x00
            btBuf[2] = 0x41
            btBuf[3] = 0x0D
            iResult = self.__oSer.write(btBuf)
            #必须发送的数量是一致的
            if iResult != len(btBuf):
                raise Exception("__oSer.write: " + str(iResult))
            #end if

            #读取参数
            strAddress, strResp = self.__read()
            if strResp[0] != 'a':
                #不是期待的分隔符，协议错误
                raise Exception("read_params: strResp[0] != 'a'")
            #end if
            strResp = strResp[1:]
            return (strAddress, strResp)

        except Exception as e:
            exstr = traceback.format_exc()
            print(exstr)
            print(e)
            return (None, None)
        #end try
    #end def

    '''
    设置编码器为被动模式
    @return 成功返回True，失败返回False
    '''
    def set_passive_mode(self, address):
        #设置主被动模式：（编程允许线接高电平时有效）
        #上位机发送：D+地址+I+模式+0D        编码器回：  X+地址+i+模式+0D
        #例：上位机发送：44 30 31 49 09 0D     编码器回：  58 30 31 69 09 0D
        #（设置为问答模式）
        return self.__change_setting(address, 0x49, 0x09, 1)
    #end def

    '''
    设置地址
    @param address 地址
    @param new_address 新地址
    @return 成功返回True，失败返回False
    '''
    def set_address(self, address, new_address):
        try:
            #设置地址：（编程允许线接高电平时有效）
            #上位机发送：D+地址+B+新地址+0D 编码器回： X+地址+b+新地址+0D
            #例：上位机发送：44 30 30 42 30 31 0D 编码器回： 58 30 30 62 30 31 0D
            #（将地址00 改为01）
            new_address = str(new_address)
            if len(new_address) > 2:
                raise Exception("set_address: len(new_address) > 2")
            #end if
            new_address = "0" * (2 - len(new_address)) + new_address
            return self.__change_setting(address, 0x42, new_address, 2)

        except Exception as e:
            exstr = traceback.format_exc()
            print(exstr)
            print(e)
            return False
        #end try
    #end def

    '''
    更改设置
    @param address 地址
    @param cmd 更改命令标识
    @param value 更改值
    @param value_len 更改值长度
    @return 成功返回True，失败返回False
    '''
    def __change_setting(self, address, cmd, value, value_len):
        try:
            if not self.__oSer.is_open:
                #没有打开，失败
                raise Exception("__change_setting: must call open")
            #end if

            address = str(address)
            value = str(value)
            btBuf = bytearray(5 + value_len)
            iPos = self.__write_address(address, btBuf)
            btBuf[iPos] = cmd
            iPos += 1
            for i in range(value_len):
                btBuf[iPos + i] = ord(value[i])
            #end for
            iPos += value_len
            btBuf[iPos] = 0x0D

            iResult = self.__oSer.write(btBuf)
            #必须发送的数量是一致的
            if iResult != len(btBuf):
                raise Exception("__oSer.write: " + str(iResult))
            #end if

            #获取响应
            strAddress, strResp = self.__read()
            if address != strAddress:
                #地址不一致
                raise Exception("__change_setting: address != strAddress")
            #end if
            if strResp[0] != chr(cmd + 0x20):
                #不是期待的分隔符，协议错误
                raise Exception("__change_setting: strResp[0] != chr(cmd + 0x20)")
            #end if
            if strResp[1:] != value:
                #不一致
                raise Exception("__change_setting: strResp[1:] != value")
            #end if
            return True

        except Exception as e:
            exstr = traceback.format_exc()
            print(exstr)
            print(e)
            return False
        #end try
    #end def

    '''
    读数据
    @param address 编码器地址，范围为0到99
    @return 成功返回读取的数据，失败返回None
    '''
    def read_data(self, address):
        try:
            if not self.__oSer.is_open:
                #没有打开，失败
                raise Exception("read_data: must call open")
            #end if

            #上位机发送：D+地址+0D   编码器回：X+地址+>+符号位+数据位+0D
            #例：上位机发送44 30 31 0D    编码器回：58 30 31 3E 2B 30 30 30 30 30 30 30 31 32 33 0D
            address = str(address)
            btBuf = bytearray(4)
            iPos = self.__write_address(address, btBuf)
            btBuf[iPos] = 0x0D
            iResult = self.__oSer.write(btBuf)
            #必须发送的数量是一致的
            if iResult != len(btBuf):
                raise Exception("__oSer.write: " + str(iResult))
            #end if

            #获取响应
            strAddress, strResp = self.__read()
            if address != strAddress:
                #地址不一致
                raise Exception("read_data: address != strAddress")
            #end if
            if strResp[0] != '>':
                #不是期待的分隔符，协议错误
                raise Exception("read_data: strResp[0] != '>'")
            #end if
            strResp = strResp[1:]
            return int(strResp)

        except Exception as e:
            exstr = traceback.format_exc()
            print(exstr)
            print(e)
            return None
        #end try

    #end def

    '''
    写入地址到buf
    失败抛出异常
    @param address 字符串地址
    @param buf 写入buf
    @return 下一个写入位置
    '''
    def __write_address(self, address, buf):
        iAddrLen = len(address)
        if iAddrLen > 2 or iAddrLen == 0:
            raise Exception("__write_address: address len error")
        #end if

        buf[0] = 0x44
        buf[1] = 0x30 if iAddrLen < 2 else ord(address[0])
        buf[2] = ord(address[iAddrLen - 1])
        return 3
    #end def

    '''
    读取数据，解析一帧数据
    @return 成功返回(地址，响应)，失败抛出异常
    '''
    def __read(self):
        btBuf = bytearray()
        beginTime = time.time()
        while True:
            #btResult = b'X10>-1234567\r'
            #btResult = b'\x58\x30\x31\x61\x06\x03\x11\x09\x0D'
            btResult = self.__oSer.read(128)
            if btResult is None or len(btResult) == 0:
                if time.time() - beginTime > self.timeout:
                    #超过指定时间任然没有读取到完整的包
                    raise Exception("__read timeout")
                #end if
                continue
            #end if
            btBuf.extend(btResult)
            if btResult[len(btResult) - 1] == 0x0D:
                break
            #end if
        #end while

        #到这里是一帧数据了
        if btBuf[0] != 0x58:
            #非X开头，协议错误
            raise Exception("__read: first byte is %s" % btBuf[0])
        #end if

        btAddress = btBuf[1:3]
        strAddress = str(btAddress, encoding = "utf-8")#.rstrip(' \x00')
        btResp = btBuf[3:len(btBuf) - 1]
        strResp = str(btResp, encoding = "utf-8")
        return (strAddress, strResp)
    #end def

#end class
