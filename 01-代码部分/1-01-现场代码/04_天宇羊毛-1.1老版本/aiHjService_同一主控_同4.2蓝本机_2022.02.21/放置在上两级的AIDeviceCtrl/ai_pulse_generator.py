# coding=utf-8

import os
import sys
import time
import ctypes
import traceback
import serial #安装包名pyserial
import serial.tools.list_ports
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

from . import config
from . import util

'''
@author maoyanwei
脉冲发生器，流量计设备
详情参考doc下的文档说明
！！！本实现非线程安全，同一实例不可在多线程下使用（本类静态方法可以在多线程下使用）。！！！
'''
class ai_pulse_generator:
    UNIT = 0x1

    def __init__(self, device_type, port = None):
        '''
        构造
        @param port 端口，为None可在后续open时指定
        @param device_type 设备类型字符串，传'normal'或'advance'
        '''
        self.__oConn = None
        self.port = port
        self.device_type = device_type.lower()
        if self.device_type == 'normal':
            self.__handleResponse = self.__decodeNormalResponse
            self.__readCount = 6
            self.baudrate = 9600
        elif self.device_type == 'advance' :
            self.__handleResponse = self.__decodeAdvanceResponse
            self.__readCount = 14
            self.baudrate = 9600
        else:
            raise Exception("invalid device_type %s" % self.device_type)
        #end if
    #end def

    def __del__(self):
        '''
        析构
        '''
        #print("~ai_pulse_generator")
        self.close()
    #end def

    def list_serial_port(self):
        '''
        获取当前串口列表
        @return 返回当前串口列表
        '''
        try:
            oList = list(serial.tools.list_ports.comports())
            return oList
        except Exception as e:
            print(e)
            return []
        #end try
    #end if

    def close(self):
        '''
        关闭通讯
        '''
        if self.__oConn is None:
            return
        #end if
        util.safeWork(lambda: self.__oConn.close())
        self.__oConn = None
    #end def

    @property
    def is_connected(self):
        '''
        是否连接
        '''
        return not self.__oConn is None
    #end def

    def open(self, astrComPort = None):
        '''
        打开modbus连接
        @param astrComPort 串口名
        @return 成功打开返回True
        '''
        try:
            if self.is_connected:
                #已经打开了
                return False
            #end if
            if astrComPort is None: astrComPort = self.port
            else: self.port = astrComPort

            '''
            通讯:
            出厂地址：1（默认)
            波特率：9600，8 位数据位，1 位停止位，无校验。（9600，8，1，n)
            '''
            self.__oConn = ModbusClient(method = 'rtu', port = astrComPort, timeout = 2, 
                                        baudrate = self.baudrate)
            if not self.__oConn.connect():
                raise Exception("self.__oConn.connect() failed")
            #end if
            return True

        except Exception as e:
            print(e)
            self.close()
            return False
        #end try
    #end def

    def read_data(self):
        '''
        读取流量计数据
        @return 根据设备类型不同，返回不同的tuple；失败返回None
        '''
        try:
            if not self.__oConn:
                #没有打开，失败
                raise Exception("read_data: must call open")
            #end if

            response = self.__oConn.read_holding_registers(0, self.__readCount, 
                                                           unit = ai_pulse_generator.UNIT)
            if response.isError():
                raise Exception("read_holding_registers: %s" % str(response))
            #end if
            
            #返回解析的结果
            return self.__handleResponse(response.registers)
        except Exception as e:
            exstr = traceback.format_exc()
            print(exstr)
            print(e)
            return None
        #end try
    #end def

    def __decodeNormalResponse(self, registers):
        '''
        解析普通型号的响应
        @return 成功返回(瞬时流量值uint32_t, 累计流量uint32_t, 频率值uint32_t)
        '''
        #MCGS 区号 读写属性 类型 modbus 地址 变量说明
        #4区 只读 32位无符号 0 瞬时流量值0.001L
        #4区 只读 32位无符号 2 累计流量(掉电存储)0.01L
        #4区 只读 32位无符号 4 频率值/分钟
        return (ai_pulse_generator._toUint32(registers, 0), 
                ai_pulse_generator._toUint32(registers, 2), 
                ai_pulse_generator._toUint32(registers, 4))
    #end def

    def __decodeAdvanceResponse(self, registers):
        '''
        解析高级型号的响应
        @return 成功返回(瞬时量float, 工况流量float, 累积量uint64_t, 温度float, 压力float, 频率float)
        '''

        decoder = BinaryPayloadDecoder.fromRegisters(registers,
                                                     byteorder=Endian.Big,
                                                     wordorder=Endian.Big)
        #量纲名称	地址	类型	字节数
        #瞬时量	0x0000	浮点	4
        fInstantaneousValue = decoder.decode_32bit_float()
        #工况流量	0x0004	浮点	4
        fWorkingConditionValue = decoder.decode_32bit_float()
        #累积量低位	0x0008	长整形	4
        iTotalValueLow = decoder.decode_32bit_uint()
        #累积量高位	0x000C	长整形	4
        iTotalValueHi = decoder.decode_32bit_uint()
        #累积量为含三位小数的无符号定点数，低位为32位无符号长整数，
        #当>=1000'000'000时向高位进位（高位+1），高位为16位无符号整数，通讯规格化为32位长整数
        #累积量 = 累积量高位 × 1000'000 + 累积量低位 ÷ 1000
        iTotalValue = int(iTotalValueHi * 1000000 + iTotalValueLow / 1000)
        #温度	0x0010	浮点	4
        fTemperatureValue = decoder.decode_32bit_float()
        #压力	0x0014	浮点	4
        fPressureValue = decoder.decode_32bit_float()
        #频率	0x0018	浮点	4
        fFrequencyValue = decoder.decode_32bit_float()

        return (fInstantaneousValue, fWorkingConditionValue, iTotalValue, 
                fTemperatureValue, fPressureValue, fFrequencyValue)
    #end def

    def _toUint32(registers, pos):
        '''
        寄存器转为uint32，失败抛异常
        '''
        return (registers[pos] << 16) | registers[pos + 1]
    #end def

#end class
