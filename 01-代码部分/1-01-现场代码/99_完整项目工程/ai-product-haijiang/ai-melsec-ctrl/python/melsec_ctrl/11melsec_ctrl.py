import os
import sys
import time
import numpy
import socket
from . import config
from . import util

#确保取到真正的脚本目录，不要用sys.path[0]
TASK_PY_PATH = os.path.split(os.path.realpath(__file__))[0]

'''
@author maoyanwei
本项目实现与三菱可编程控制器的通讯、控制
本模块协议均严格按照毕华提供的文档手册实现，有问题找毕华。
协议详见：《FX3U-ENET-ADP用户手册》第7章

！！由于MC协议是停等协议，故本类设计暂不考虑线程安全问题，
使用时请勿在多线程中操作本类实例，否则结果不确定！！
'''
class melsec_ctrl:
    
    #构造
    def __init__(self):
        self.__oSocket = None
        self.__iTimeout = 15
    #end def

    #析构，尽量外部调用close关闭
    def __del__(self):
        self.close()
    #end def

    #当前连接是否已经打开
    def is_actived(self):
        return not self.__oSocket is None
    #end def

    '''
    打开设备通讯连接
    @param address 地址pair(host, port)
    @param timeout 超时秒数
    @return 成功返回True
    '''
    def open(self, address, timeout = 15.0):
        if self.is_actived():
            util.addLog("melsec_ctrl.open err: is_actived")
            return False
        #end if
        try:
            self.__oSocket = socket.create_connection(address, timeout)
            self.__iTimeout = timeout
            return True
        except Exception as e:
            util.addLog("melsec_ctrl.open err: %s" % str(e))
            self.__oSocket = None
            return False
        #end try
    #end def

    #关闭设备连接
    def close(self):
        util.safeWork(lambda: None if self.__oSocket is None else self.__oSocket.close())
        self.__oSocket = None
    #end def

    '''
    发送请求报文，获取响应，外部一般不直接调用此方法，因为本方法只处理了请求头和响应头。
    协议详见：《FX3U-ENET-ADP用户手册》第7章
    @param aiSubtitle 副标题
    @param abtSendData 命令报文的请求体部分
    @param aiSendLen 请求体长度
    @param aiResponseLen 若有响应体部分，则指定长度（字节），否则为0
    @return 成功返回响应数据，失败返回None
    '''
    def sendReq(self, aiSubtitle, abtSendData, aiSendLen, aiResponseLen = 0):
        iHeadLen = 4
        try:
            if not self.is_actived():
                raise Exception("not actived")
            #end if

            iTotalSendLen = iHeadLen + aiSendLen
            
            #以下协议参考7.3.3章节
            btSendBuf = bytearray(iTotalSendLen)

            #副标题1字节
            aiSubtitle = aiSubtitle & 0xFF
            btSendBuf[0] = aiSubtitle
            #PC号
            btSendBuf[1] = 0xFF
            #监视定时器
            btSendBuf[2] = 0x0A
            btSendBuf[3] = 0x00
            #协议体
            if not abtSendData is None:
                for i in range(aiSendLen):
                    btSendBuf[iHeadLen + i] = abtSendData[i]
                #end for
            #end if

            self.__oSocket.sendall(btSendBuf)
            
            #TODO: 此处有个隐忧，我们取消了超时设定，阻塞收模式可能一直不返回
            #等有时间再处理吧，暂且不管了，认为服务端总是正确的
            self.__oSocket.setblocking(True)
            btRecvBuf = self.__oSocket.recv(2, socket.MSG_WAITALL)
            #检查响应副标题，根据文档，我总结的规律：响应总是命令的值+0x80
            if btRecvBuf[0] != (0x80 + aiSubtitle):
                raise Exception("response subtitle(%s) error" % btRecvBuf[0])
            #end if
            #检查结束代码
            iEndCode = btRecvBuf[1]
            if iEndCode == 0x00:
                #这里是正常响应
                if aiResponseLen > 0:
                    btReturn = self.__oSocket.recv(aiResponseLen, socket.MSG_WAITALL)
                    return btReturn
                else:
                    return bytes(0)
                #end if
            elif iEndCode == 0x5B:
                #处理异常响应
                btRecvBuf = self.__oSocket.recv(2, socket.MSG_WAITALL)
                iErrCode = btRecvBuf[0]
                if btRecvBuf[1] != 0x00:
                    #TODO: 已经发生异常了，且协议错误，我们先不管
                    util.addLog("melsec_ctrl.sendReq: Protocol error, btRecvBuf[1] != 0x00")
                #end if
                raise Exception("MC return err code %s" % iErrCode)
            else:
                #非5B的异常结束(50～60H)
                raise Exception("MC return EndCode %s" % iEndCode)
            #end if

            #不应该执行到此处
            return None

        #根据python文档，现在新版本python，发生EINTR不再抛出异常，我暂且认为我们用的是新版本。
        #except InterruptedError:
        #    pass

        except OSError as ose:
            util.addLog("melsec_ctrl.sendReq oserr: %s" % str(ose))
            self.close()
            return None

        except Exception as e:
            util.addLog("melsec_ctrl.sendReq err: %s" % str(e))
            return None

        finally:
            #总是重置超时
            util.safeWork(lambda: None if self.__oSocket is None else self.__oSocket.settimeout(self.__iTimeout))
    #end def
    
    '''
    二进制码通信中进行远程RUN(命令:13H)
    参考7.6章节
    '''
    def remote_run(self):
        return not self.sendReq(0x13, None, 0, 0) is None
    #end def

    '''
    二进制码通信中进行远程STOP(命令:14H)
    参考7.6章节
    '''
    def remote_stop(self):
        return not self.sendReq(0x14, None, 0, 0) is None
    #end def

    '''
    按位写入软元件
    协议详见：《FX3U-ENET-ADP用户手册》第7章
    @param astrSoft 软元件名字和编号，如“M100”
    @param aoBitData 数组每个元素作为一个bit处理，非0值表示ON状态
    @return 成功返回True
    '''
    def write_bit_data(self, astrSoft, aoBitData):
        return self.__write_data(astrSoft, aoBitData, True)
    #end def

    '''
    按字写入软元件
    协议详见：《FX3U-ENET-ADP用户手册》第7章
    @param astrSoft 软元件名字和编号，如“C100”
    @param aoWordData 数组每个元素作为一个字处理
    @return 成功返回True
    '''
    def write_word_data(self, astrSoft, aoWordData):
        return self.__write_data(astrSoft, aoWordData, False)
    #end def

    '''
    按双字写入软元件
    协议详见：《FX3U-ENET-ADP用户手册》第7章
    @param astrSoft 软元件名字和编号，如“C100”
    @param aoDWordData 数组每个元素作为一个双字处理
    @return 成功返回True
    '''
    def write_dword_data(self, astrSoft, aoDWordData):
        try:
            aryWord = []
            for dwValue in aoDWordData:
                iHigh = (dwValue >> 16) & 0xFFFF
                iLow = dwValue & 0xFFFF
                aryWord.append(iLow)
                aryWord.append(iHigh)
            #end for
            return self.write_word_data(astrSoft, aryWord)
        except Exception as e:
            util.addLog("melsec_ctrl.write_dword_data err: %s" % str(e))
            return False
    #end def

    '''
    按位读出软元件
    协议详见：《FX3U-ENET-ADP用户手册》第7章
    @param astrSoft 软元件名字和编号，如“M100”
    @param auCount 读取的软元件个数（bit数）
    @return 成功返回读取的数组，数组每个元素作为一个bit处理；失败返回None
    '''
    def read_bit_data(self, astrSoft, auCount):
        return self.__read_data(astrSoft, auCount, True)
    #end def

    '''
    按字读出软元件
    协议详见：《FX3U-ENET-ADP用户手册》第7章
    @param astrSoft 软元件名字和编号，如“C100”
    @param auCount 读取的软元件个数（字个数）
    @return 成功返回读取的数组，数组每个元素作为一个word处理；失败返回None
    '''
    def read_word_data(self, astrSoft, auCount):
        return self.__read_data(astrSoft, auCount, False)
    #end def

    '''
    按双字读出软元件
    协议详见：《FX3U-ENET-ADP用户手册》第7章
    @param astrSoft 软元件名字和编号，如“C100”
    @param auCount 读取的双字个数（非软元件个数）
    @return 成功返回读取的数组，数组每个元素作为一个dword处理；失败返回None
    '''
    def read_dword_data(self, astrSoft, auCount):
        aryWord = self.read_word_data(astrSoft, auCount * 2)
        if aryWord is None:
            return None
        #end if
        aryResult = []
        for i in range(auCount):
            dwValue = aryWord[i * 2] | (aryWord[i * 2 + 1] << 16)
            aryResult.append(dwValue)
        #end for
        return aryResult
    #end def

    '''
    把字符命令写到字节数组里去
    @param astrSoft 软元件名字和编号，如“M100”
    @param auNum 根据《7.4 MC协议的命令和功能一览》一节描述的操作单位数量
    @param abtBuf 写入缓冲
    @param aiBufIndex 写入索引
    @return 成功返回后续索引，失败返回-1
    '''
    @staticmethod
    def _write_str_cmd(astrSoft, auNum, abtBuf, aiBufIndex):
        try:
            if len(astrSoft) <= 1:
                raise Exception("soft len err")
            #end if

            #解析后填入
            iSoftName = ord(astrSoft[0]) & 0xff
            iSoftNo = int(astrSoft[1:])
            aiBufIndex = melsec_ctrl._write_int(abtBuf, aiBufIndex, iSoftNo)
            abtBuf[aiBufIndex] = 0x20
            abtBuf[aiBufIndex + 1] = iSoftName
            abtBuf[aiBufIndex + 2] = (auNum & 0xff)
            abtBuf[aiBufIndex + 3] = 0x00
            return aiBufIndex + 4

        except Exception as e:
            util.addLog("melsec_ctrl.__write_str_cmd err: %s" % str(e))
            return -1
    #end def

    '''
    写入软元件数据
    @param abtBuf 写入缓冲
    @param aiBufIndex 写入索引
    @param aoData 当按位写入时，数组每个元素作为一个bit处理，否则作为一个字处理
    @param abIsBit 为true时按位处理，否则按字处理
    @return 成功返回后续索引，失败返回-1
    '''
    @staticmethod
    def _write_soft_data(abtBuf, aiBufIndex, aoData, abIsBit):
        try:
            iDataLen = len(aoData)
            if iDataLen == 0:
                raise Exception("data len is 0")
            #end if
            i = 0

            if abIsBit:
                #位软元件按位为单位
                iEnd = iDataLen if iDataLen % 2 == 0 else iDataLen - 1
                while i < iEnd:
                    btHi = 0x10 if aoData[i] != 0 else 0x00
                    btLow = 0x1 if aoData[i + 1] != 0 else 0x00
                    i += 2
                    abtBuf[aiBufIndex] = (btHi | btLow)
                    aiBufIndex += 1
                #end while
                if i < iDataLen:
                    #若是奇数个，需要补最后一个虚拟位
                    btHi = 0x10 if aoData[i] != 0 else 0x00
                    abtBuf[aiBufIndex] = btHi
                    aiBufIndex += 1
                #end if
            else:
                #位软元件按字为单位暂不考虑，这里只可能是字软元件，顺序刚好是一致的
                while i < iDataLen:
                    aiBufIndex = melsec_ctrl._write_word(abtBuf, aiBufIndex, aoData[i])
                    i += 1
                #end while
            #end if

            return aiBufIndex

        except Exception as e:
            util.addLog("melsec_ctrl._write_soft_data err: %s" % str(e))
            return -1
    #end def

    '''
    读出软元件数据
    @param abtBuf 读取缓冲
    @param aiBufIndex 缓冲索引
    @param auCount 读取的软元件个数
    @param abIsBit 为true时按位处理，否则按字处理
    @return 成功返回(下一个索引位置, 读取的数组)，失败返回(aiBufIndex, None)
    '''
    @staticmethod
    def _read_soft_data(abtBuf, aiBufIndex, auCount, abIsBit):
        try:
            if auCount <= 0:
                return (aiBufIndex, [])
            #end if
            oResult = []
            i = 0
            if abIsBit:
                #位软元件按位为单位
                while i < auCount:
                    btValue = abtBuf[aiBufIndex]
                    aiBufIndex += 1
                    oResult.append(1 if (btValue & 0x10) != 0 else 0) #高位是第一个
                    oResult.append(1 if (btValue & 0x1) != 0 else 0)  #低位是第二个
                    i += 2
                #end while
                if i > auCount:
                    #多写了一个，删除
                    oResult.pop()
                #end if
            else:
                 #位软元件按字为单位暂不考虑，这里只可能是字软元件，顺序刚好是一致的
                while i < auCount:
                    aiBufIndex, iValue = melsec_ctrl._read_word(abtBuf, aiBufIndex)
                    oResult.append(iValue)
                    i += 1
                #end while
            #end if

            return (aiBufIndex, oResult)

        except Exception as e:
            util.addLog("melsec_ctrl._read_soft_data err: %s" % str(e))
            return (aiBufIndex, None)
    #end def

    '''
    按位或者字写入软元件
    协议详见：《FX3U-ENET-ADP用户手册》第7章
    @param astrSoft 软元件名字和编号，如“M100”
    @param abtWriteData 当按位写入时，数组每个元素作为一个bit处理，否则作为一个字处理
    @param abIsBit 为true时按位处理，否则按字处理
    @return 成功返回True
    '''
    def __write_data(self, astrSoft, abtWriteData, abIsBit):
        try:
            btBuf = bytearray(1024 * 8)
            #填写字符命令
            iBufIndex = melsec_ctrl._write_str_cmd(astrSoft, len(abtWriteData), btBuf, 0)
            #填软元件数据
            iBufIndex = melsec_ctrl._write_soft_data(btBuf, iBufIndex, abtWriteData, abIsBit)
            #发送带头请求
            iSubtitle = 0x02 if abIsBit else 0x03
            return not self.sendReq(iSubtitle, btBuf, iBufIndex, 0) is None

        except Exception as e:
            util.addLog("melsec_ctrl._write_data err: %s" % str(e))
            return False
        #end try
    #end def


    '''
    按位或者字读出软元件
    协议详见：《FX3U-ENET-ADP用户手册》第7章
    @param astrSoft 软元件名字和编号，如“M100”
    @param auCount 读取的软元件个数
    @param abIsBit 为true时按位处理，否则按字处理
    @return 成功返回读取的数组，失败返回None
    '''
    def __read_data(self, astrSoft, auCount, abIsBit):
        try:
            btBuf = bytearray(1024 * 8)
            #填写字符命令
            iBufIndex = melsec_ctrl._write_str_cmd(astrSoft, auCount, btBuf, 0)
            iSubtitle = 0x00
            iResponseLen = 0
            if abIsBit:
                #按位读
                iResponseLen = auCount // 2
                if (auCount % 2) != 0: iResponseLen += 1
            else:
                #按字读
                iSubtitle = 0x01
                iResponseLen = 2 * auCount
            #end if
            #获取响应
            btBuf = self.sendReq(iSubtitle, btBuf, iBufIndex, iResponseLen)
            if btBuf is None:
                raise Exception("sendReq failed")
            #end if
            #解析响应
            iBufIndex, oResult = melsec_ctrl._read_soft_data(btBuf, 0, auCount, abIsBit)
            return oResult

        except Exception as e:
            util.addLog("melsec_ctrl.__read_data err: %s" % str(e))
            return None
        #end try
    #end def

    '''
    short写入buf，小头顺序
    '''
    @staticmethod
    def _write_word(abtBuf, aiBufIndex, aiValue):
        #TODO: python不能指针操作，不知道有没有更快的实现方法
        abtBuf[aiBufIndex] = aiValue & 0xff                 #L
        abtBuf[aiBufIndex + 1] = (aiValue >> 8) & 0xff      #H
        return aiBufIndex + 2
    #end def

    '''
    int写入buf，小头顺序
    '''
    @staticmethod
    def _write_int(abtBuf, aiBufIndex, aiValue):
        #TODO: python不能指针操作，不知道有没有更快的实现方法
        abtBuf[aiBufIndex] = aiValue & 0xff                 #L
        abtBuf[aiBufIndex + 1] = (aiValue >> 8) & 0xff
        abtBuf[aiBufIndex + 2] = (aiValue >> 16) & 0xff
        abtBuf[aiBufIndex + 3] = (aiValue >> 24) & 0xff     #H
        return aiBufIndex + 4
    #end def

    '''
    从buf读出short，小头顺序
    '''
    @staticmethod
    def _read_word(abtBuf, aiBufIndex):
        #TODO: python不能指针操作，不知道有没有更快的实现方法
        #这里做安全性编码，防止abtBuf不是byte数组的情况
        iValue = (abtBuf[aiBufIndex] & 0xff) | ((abtBuf[aiBufIndex + 1] << 8) & 0xff00)
        return (aiBufIndex + 2, iValue)
    #end def

    '''
    从buf读出int，小头顺序
    '''
    @staticmethod
    def _read_int(abtBuf, aiBufIndex):
        #TODO: python不能指针操作，不知道有没有更快的实现方法
        #这里做安全性编码，防止abtBuf不是byte数组的情况
        iValue = ( (abtBuf[aiBufIndex] & 0xff) | 
                   ((abtBuf[aiBufIndex + 1] << 8) & 0xff00) |
                   ((abtBuf[aiBufIndex + 2] << 16) & 0xff0000) |
                   ((abtBuf[aiBufIndex + 3] << 24) & 0xff000000)
                 )
        return (aiBufIndex + 4, iValue)
    #end def

#end def class


