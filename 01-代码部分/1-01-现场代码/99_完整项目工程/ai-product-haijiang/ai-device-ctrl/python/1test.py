import os
import cv2
import time
from AIDeviceCtrl import util
from AIDeviceCtrl.ai_device_ctrl import *
from AIDeviceCtrl.ai_image_tool import ai_calc_bmp_color

#确保取到真正的脚本目录，不要用sys.path[0]
TASK_PY_PATH = os.path.split(os.path.realpath(__file__))[0]


#测试控制的回调类
class test_ctrl_callback(ai_device_ctrl_callback):
    #---------------- LED回调 BEGIN ----------------
    '''
    调用ai_device_ctrl.async_send_led_cmd操作结果回调
    @param aiTransId 调用ai_device_ctrl.async_send_led_cmd时传递的transId
    @param abResult 操作成功传递True
    '''
    def on_send_led_cmd_result(self, aiTransId, abResult):
        print("收到LED回调，将调用父类：")
        super().on_send_led_cmd_result(aiTransId, abResult)
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
        if abIsChanged:
            #有变化时打印出来
            print("%s: 收到光栅回调，当前%s，状态%s，用户数据[%s]" % 
                  (time.time(), "遮光" if abIsCovered else "通光", "改变" if abIsChanged else "未变", aoUserData))
            super().on_read_raster_data(abIsCovered, abIsChanged, aoUserData)
        #end if
    #end def

    '''
    光栅错误处理回调，回调一旦发生光栅设备通讯已经被关闭，需要自己后续重新打开
    @param astrErr 错误描述
    @param aoUserData 调用open_raster_serial时传递的用户自定义数据
    '''
    def on_raster_error(self, astrErr, aoUserData):
        print("光栅读取出错[%s]，需重新打开，用户数据[%s]" % (astrErr, aoUserData))
        super().on_raster_error(astrErr, aoUserData)

        #此处失败后可以重新打开，假设aoUserData传递的就是ai_device_ctrl本身
        #bResult = aoUserData.open_raster_serial("COM1", aoUserData)
        #print("重新打开结果:" + bResult)
    #end def

    #---------------- 光栅回调 END ----------------

#end class

#测试串口LED光源控制
def testSerialForLED():
    oCtrl = ai_device_ctrl()
    oCtrl.set_callback(test_ctrl_callback()) #设置一个处理回调的对象

    try:
        oSerialList = oCtrl.list_serial_port()
        print("当前可用串口：")
        for oInfo in oSerialList:        
            print("name: %s, device: %s, description: %s" % (oInfo.name, oInfo.device, oInfo.description))
        #end for

        #需要先确定实际的串口，这里仅做测试，以实际插入的串口和系统平台为准
        strPortName = "COM1" if util.isWindows() else "/dev/ttyUSB0"
        #打开串口
        oCtrl.set_for_4_led()
        if not oCtrl.open_led_serial(strPortName, afTimeout = 2.0):
            print("打开LED串口失败")
            return
        #end if
        print("LED串口打开成功")

        #控制灯光配置参数
        oCfgList = [
                    (100, not True),    #第1通道亮度100, 设置为亮
                    (150, not True),   #第2通道亮度150, 设置为亮
                    (200, not True),    #第3通道亮度200, 设置为亮
                    (120, not True),   #第4通道亮度120, 设置为亮
                   ]
        if True:
            #测试同步控制
            if oCtrl.send_led_cmd(oCfgList):
                print("同步发送灯光控制指令成功")
            else:
                print("同步发送灯光控制指令失败")
            #end if
        #end if
        
        if not True:
            #测试异步控制，连续5次
            for i in range(1):
                if oCtrl.async_send_led_cmd(oCfgList, 9527):
                    print("异步调用成功（不代表结果成功），i = %s" % i)
                else:
                    print("异步调度都没有成功，请求不会被执行, i = %s" % i)
                #end if
            #end for
            print("异步发送灯光控制指令完毕，等待回调结果...")
            #这里故意等一会，等回调到来，实际应用场景并不需要，否则异步操作无意义
            time.sleep(12)
        #end if

    finally:
        #无论如何最后需要关闭串口
        oCtrl.close_led_serial()

        print("do clean")
        oCtrl.clean()
        
        #可选的delete对象步骤
        print("do del")
        del oCtrl
    #end try

#end def testSerialForLED

#测试光栅控制
def testSerialForRaster():

    oCtrl = ai_device_ctrl()
    oCtrl.set_callback(test_ctrl_callback()) #设置一个处理回调的对象

    try:
        oSerialList = oCtrl.list_serial_port()
        print("当前可用串口：")
        for oInfo in oSerialList:        
            print("name: %s, device: %s, description: %s" % (oInfo.name, oInfo.device, oInfo.description))
        #end for

        #需要先确定实际的串口，这里仅做测试，以实际插入的串口和系统平台为准
        strPortName = "COM1" if util.isWindows() else "/dev/ttyS0"
        #打开串口
        print("准备打开光栅串口...")
        if not oCtrl.open_raster_serial(strPortName, "user data123"):
            print("打开光栅串口失败")
            return
        #end if

        print("光栅串口打开成功，处理60秒后关闭")
        time.sleep(60)

    finally:
        #无论如何最后需要关闭串口
        oCtrl.close_raster_serial()
        
        print("do clean")
        oCtrl.clean()
        
        #可选的delete对象步骤
        print("do del")
        del oCtrl
    #end try

#end def testSerialForRaster


#测试英美金摄像头软触发
def testTheImageSource():

    from AIDeviceCtrl.tiscamera_ctrl import tiscamera_ctrl

    class TestCallback:
        def __init__(self):
            self.start_time = 0.0
        #end def
        
        def on_new_image(self, astrSerial, aoImage):
            end_time = time.time()
            use_time = (end_time - self.start_time) * 1000.0
            print("TestCallback::on_new_image: %s, use time: %sms" % (astrSerial, use_time))
            
            # import cv2
            # strSaveName = "%s.png" % astrSerial
            # print("%s: save '%s'..." % (time.time(), strSaveName))
            # cv2.imwrite(strSaveName, aoImage)
            # print("%s: save '%s' done" % (time.time(), strSaveName))
            
        #end def
    #end class

    iWidth = 2448
    iHeight = 2048
    strDeviceId = "35024020"
    oCtrl = tiscamera_ctrl(iWidth, iHeight)
    oAllDeviceInfo = oCtrl.get_device_list()
    print("oAllDeviceInfo = %s" % oAllDeviceInfo)
    
    oTestCallback = TestCallback()
    bResult = oCtrl.open_device(strDeviceId, oTestCallback)
    print("open device %s: %s" % (strDeviceId, bResult))
    
    strPropNames = ["Trigger Delay (us)", "Trigger Activation", "Trigger Source", "Trigger Mode"]
    for strName in strPropNames:
        strValue = oCtrl.get_property(strName)
        print("%s = %s" % (strName, strValue))
    #end for
    oCtrl.set_property("Exposure Auto", "Off")
    oCtrl.set_property("Exposure", 1800)
    # oCtrl.set_property("Trigger Activation", "FallingEdge")
    # oCtrl.set_property("Trigger Mode", "Off")
    print("try to set Trigger Mode Off: %s" % oCtrl.set_property("Trigger Mode", "Off"))
    print("after set, Trigger Mode = %s" % oCtrl.get_property("Trigger Mode"))
    print("try to set Trigger Mode On: %s" % oCtrl.set_property("Trigger Mode", "On"))
    print("after set, Trigger Mode = %s" % oCtrl.get_property("Trigger Mode"))
    print("\n---------------------\n")
    
    print("will call start_capture")
    bResult = oCtrl.start_capture()
    print("oCtrl.start_capture() = %s" % bResult)
    for i in range(1000):
        print("第{}次软触发".format(i + 1))
        oTestCallback.start_time = time.time()
        bResult = oCtrl.software_trigger()
        # print("%s: call software_trigger: %s" % (oTestCallback.start_time, bResult))
        time.sleep(5.2)

    print("\n------------------------\n")

    oTestCallback.start_time = time.time()
    bResult = oCtrl.software_trigger()
    print("%s: call software_trigger: %s" % (oTestCallback.start_time, bResult))
    time.sleep(1)
    
    print("will call stop_capture")
    #可以直接调用close_device，会先关闭图像捕获
    #oCtrl.stop_capture()
    
    print("will call close_device")
    oCtrl.close_device()
    
    print("do del")
    del oCtrl

#end def testTheImageSource



def test_main():
    #测试计算图片黑白值
    if not True:
        fBeginTime = time.time()
        strBmpFile = os.path.join(TASK_PY_PATH, "test.bmp")
        iBlackNum, iWhiteNum = ai_calc_bmp_color(strBmpFile)
        print("%s\n黑色： %s，白色：%s，合计：%s" % (strBmpFile, iBlackNum, iWhiteNum, iBlackNum + iWhiteNum))

        fEndTime = time.time()
        print("耗时：%ss" % (fEndTime - fBeginTime))
        
        return
    #end if

    #测试串口LED光源控制
    # testSerialForLED()

    #测试光栅控制
    #testSerialForRaster()

    #测试英美金摄像头软触发
    testTheImageSource()
#end def


if __name__ == '__main__':
    test_main()
#end if
