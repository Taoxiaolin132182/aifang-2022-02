import os
import sys
import time
import ctypes
import numpy
import serial #安装包名pyserial
import serial.tools.list_ports
from concurrent.futures import ThreadPoolExecutor

from . import config
from . import util
from .PythonCallCpp import PythonCallCpp

'''
@author maoyanwei
本模块用于AI产品项目中的常见设备控制
'''

#确保取到真正的脚本目录，不要用sys.path[0]
TASK_PY_PATH = os.path.split(os.path.realpath(__file__))[0]

#用于ai_device_ctrl操作回调接口
class ai_device_ctrl_callback:

    #---------------- LED回调 BEGIN ----------------

    '''
    调用ai_device_ctrl.async_send_led_cmd操作结果回调
    @param aiTransId 调用ai_device_ctrl.async_send_led_cmd时传递的transId
    @param abResult 操作成功传递True
    '''
    def on_send_led_cmd_result(self, aiTransId, abResult):
        print("on_send_led_cmd_result(aiTransId=%s, abResult=%s)" % (aiTransId, abResult))
    #end def

    #---------------- LED回调 END ----------------


    #---------------- 光栅回调 BEGIN ----------------

    '''
    读取到了一帧光栅数据回调
    @param abIsCovered 为True表明当前光栅被遮蔽了
    @param abIsChanged 为True表明当前光栅遮蔽状态与前一帧发生了变化
    @param aoUserData 调用open_raster_serial时传递的用户自定义数据
    '''
    def on_read_raster_data(self, abIsCovered, abIsChanged, aoUserData):
        print("on_read_raster_data(abIsCovered=%s, abIsChanged=%s, aoUserData=%s)" % (abIsCovered, abIsChanged, aoUserData))
    #end def

    '''
    光栅错误处理回调，回调一旦发生光栅设备通讯已经被关闭，需要自己后续重新打开
    @param astrErr 错误描述
    @param aoUserData 调用open_raster_serial时传递的用户自定义数据
    '''
    def on_raster_error(self, astrErr, aoUserData):
        print("on_raster_error(astrErr=%s, aoUserData=%s)" % (astrErr, aoUserData))
    #end def

    #---------------- 光栅回调 END ----------------

#endif


#AI各种设备控制类
class ai_device_ctrl:
    
    #构造
    def __init__(self):        
        self.__oCallback = None
        self.__oLib = None
        self.led_baudrate = 19200

        #LED部分
        self.__oLedSer = serial.Serial() #LED光源控制串口
        self.__oPoolForLED = ThreadPoolExecutor(1, "PoolForLED")

        #光栅部分
        self.__oRasterSer = serial.Serial() #光栅设备控制串口
        self.__oPoolForRaster = ThreadPoolExecutor(1, "PoolForRaster")

    #end def

    #整个进程退出时调用，清理资源
    def clean(self):
        util.safeWork(lambda: self.__oPoolForLED.shutdown())
        util.safeWork(lambda: self.__oPoolForRaster.shutdown())
        del self.__oLib
        self.__oLib = None
    #end def

    #析构
    def __del__(self):
        #print("~ai_device_ctrl")
        self.clean()
    #end def

    #设置回调
    def set_callback(self, aoCallback):
        self.__oCallback = aoCallback
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

    '''
    设置为4路led
    '''
    def set_for_4_led(self):
        self.led_baudrate = 9600
    #end def

    '''
    打开串口控制LED光源
    @param astrComPort 串口名
    @param afTimeout 读写超时秒数(float类型)
    @return 成功打开返回True
    '''
    def open_led_serial(self, astrComPort, afTimeout = 1.0):
        try:
            if self.__oLedSer.is_open:
                #已经打开了
                return False
            #end if

            '''
            通讯协议RS232
            波特率 19200
            数据位 8
            停止位 1
            校验位 无
            流控制 无
            '''
            self.__oLedSer.baudrate = self.led_baudrate
            self.__oLedSer.port = astrComPort
            self.__oLedSer.bytesize = serial.EIGHTBITS
            self.__oLedSer.stopbits = serial.STOPBITS_ONE
            self.__oLedSer.parity = serial.PARITY_NONE
            
            self.__oLedSer.timeout = afTimeout
            self.__oLedSer.write_timeout = afTimeout

            self.__oLedSer.open()

            return self.__oLedSer.is_open

        except Exception as e:
            print(e)
            self.close_led_serial()
            return False
        #end try
    #end def

    '''
    发送配置LED光源指令，使用前必须先调用open_led_serial打开串口
    @param aoCfgList 配置列表数组，格式为[(第1通道亮度级int, 是否亮bool), (第2通道亮度级int, 是否亮bool), ...]；
                     亮度级别为0-255数值，是否亮用True表示亮；
    @return 成功返回True
    '''
    def send_led_cmd(self, aoCfgList):
        try:
            if not self.__oLedSer.is_open:
                #没有打开，失败
                raise Exception("must call open_led_serial")
            #end if

            if aoCfgList is None:
                raise Exception("aoCfgList is None")
            #end if

            # 先组合字符串
            # 其中'S'为起始字符，'T'代表光源状态开，'F'代表光源状态灭
            # 'C'校验码，'#'为结束字符
            # 例如：S100T150F200T120FC#
            strCmd = "S"
            for cfg in aoCfgList:
                strCmd += ("%s%s" % (cfg[0], "T" if cfg[1] else "F"))
            #end for
            strCmd += "C#"
            #print(strCmd)

            #发送指令
            sendBuf = bytes(strCmd, encoding = "utf8")
            iResult = self.__oLedSer.write(sendBuf)
            #必须发送的数量是一致的
            if iResult != len(sendBuf):
                raise Exception("__oLedSer.write: " + str(iResult))
            #end if

            #获取返回字符，如通讯成功，上位机应接受到字符'!'
            RETURN_VAL = ord('!')
            btResult = self.__oLedSer.read(1)
            if btResult is None or len(btResult) <= 0:
                raise Exception("__oLedSer.read timeout")
            #end idf
            
            #必须相等才认为成功
            return btResult[0] == RETURN_VAL

        except Exception as e:
            print(e)
            return False
        #end try

    #end def


    #本方法在线程池中调用，内部使用
    def _async_send_led_cmd_inner(self, aoCfgList, aiTransId):
        #print("_async_send_led_cmd, aoCfgList = %s, trans = %s" % (aoCfgList, aiTransId))

        bResult = self.send_led_cmd(aoCfgList)
        util.safeWork(lambda: None if self.__oCallback is None 
                      else self.__oCallback.on_send_led_cmd_result(aiTransId, bResult))
        #print("_async_send_led_cmd, result = %s" % bResult)
    #end def

    '''
    与send_led_cmd相同，为异步调用，结果在callback中获取
    @param aoCfgList 参考send_led_cmd中说明
    @param aiTransId 自定义标识本次请求的id
    @return 异步调度成功，返回True（并非代表最后执行结果成功）
    '''
    def async_send_led_cmd(self, aoCfgList, aiTransId):
        try:
            self.__oPoolForLED.submit(ai_device_ctrl._async_send_led_cmd_inner, self, aoCfgList, aiTransId)
            return True
        except Exception as e:
            print(e)
            return False
        #end try
    #end def

    '''
    关闭串口控制LED光源
    '''
    def close_led_serial(self):
        try:
            self.__oLedSer.close()
        except Exception as e:
            print(e)
        #end try
    #end def


    '''
    打开串口控制光栅
    @param astrComPort 串口名
    @param aoUserData 用户自定义数据，在回调中使用
    @return 成功打开返回True
    '''
    def open_raster_serial(self, astrComPort, aoUserData):
        try:
            if self.__oRasterSer.is_open:
                #已经打开了
                return False
            #end if

            '''
            485通讯接口
            波特率 115200
            起始位 1
            数据位 8
            校验位 1bit奇校验
            停止位 1
            '''
            fTimeout = 2.0
            self.__oRasterSer.baudrate = 115200
            self.__oRasterSer.port = astrComPort
            self.__oRasterSer.bytesize = serial.EIGHTBITS
            self.__oRasterSer.stopbits = serial.STOPBITS_ONE
            self.__oRasterSer.parity = serial.PARITY_ODD
            
            self.__oRasterSer.timeout = fTimeout
            self.__oRasterSer.write_timeout = fTimeout

            self.__oPoolForRaster.submit(ai_device_ctrl._read_raster_data_inner, self, aoUserData)
            return True

        except Exception as e:
            print(e)
            self.close_raster_serial()
            return False
        #end try
    #end def

    #处理一帧数据
    def __handle_frame(self, aryReadBuf):
        #每帧起始码2字节 + 光栅地址1字节 + 数据4字节（14根线）
        iReadLen = len(aryReadBuf)
        if iReadLen < 7:
            #还不到一帧数据呢
            return (aryReadBuf, None, None)
        #end if

        #检查起始码
        if aryReadBuf[0] != 0xaa or aryReadBuf[1] != 0xaa:
            raise Exception("raster start code error")
        #end if

        #光栅地址
        btRasterAddr = aryReadBuf[2]
        #遮光
        bIsCovered = (aryReadBuf[3] != 0 or aryReadBuf[4] != 0 or 
                      aryReadBuf[5] != 0 or aryReadBuf[6] != 0)
        #下一帧
        return (aryReadBuf[7:], btRasterAddr, bIsCovered)
    #end def

    #本方法在线程池中调用，内部使用
    def _read_raster_data_inner(self, aoUserData):
        #print("enter _read_raster_data_inner")

        aryReadBuf = b''
        btRasterAddr, bIsCovered = (None, None)

        try:
            self.__oRasterSer.open()
            if not self.__oRasterSer.is_open:
                   raise Exception("open raster serial failed")
            #end if

            while self.__oRasterSer.is_open:
                btResult = self.__oRasterSer.read(7)
                if not self.__oRasterSer.is_open:
                    #读取期间关闭了串口，退出
                    break
                #end if

                if btResult is None or len(btResult) <= 0:
                    #可能设备出错了
                    raise Exception("__oRasterSer.read: timeout")
                    #btResult = b'\xaa\xaa\xcc\x00\x01'
                #end if
                aryReadBuf += btResult

                #处理帧数据
                (aryReadBuf, btRasterAddr, bIsCurCovered) = self.__handle_frame(aryReadBuf)
                if not bIsCurCovered is None:
                    #on_read_raster_data(self, abIsCovered, abIsChanged, aoUserData):
                    bIsChanged = (bIsCurCovered != bIsCovered)
                    bIsCovered = bIsCurCovered

                    #回调结果
                    util.safeWork(lambda: None if self.__oCallback is None
                                  else self.__oCallback.on_read_raster_data(bIsCurCovered, bIsChanged, aoUserData))
                #end if
            #end while

        except Exception as e:
            #到这里错误不可恢复，先关闭
            self.close_raster_serial()
            #再回调
            util.safeWork(lambda: print(e) if self.__oCallback is None
                          else self.__oCallback.on_raster_error(str(e), aoUserData))
        #end try

        #print("exit _read_raster_data_inner")
    #end def


    '''
    关闭串口控制光栅
    '''
    def close_raster_serial(self):
        try:
            self.__oRasterSer.close()
        except Exception as e:
            print(e)
        #end try
    #end def


#end class ai_device_ctrl

