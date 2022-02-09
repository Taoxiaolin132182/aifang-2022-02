#coding=utf-8
import json
import math
import sys
import time
import os
import signal
from concurrent.futures import ThreadPoolExecutor
import requests
import copy
from PIL import Image


START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, "..","..","ai-melsec-ctrl", "python"))
import config_armz as aiCottonConfig
import RPi.GPIO as GPIO
import cv2
from count_down_latch import count_down_latch
from image2world import image_points_to_world_plane
from background_areas_detect import detect_background
START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]

sys.path.append(os.path.join(START_PY_PATH, "..","..", "ai-device-ctrl", "python"))
del START_PY_PATH
if aiCottonConfig.CAMERA_ON:
    from AIDeviceCtrl.tiscamera_ctrl import tiscamera_ctrl

from AIDeviceCtrl.ai_encoder_device import *
from AIDeviceCtrl.ai_encoder_device import ai_encoder_device
import logging
from logger1 import get_logger

#添加包路径
START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, "..",".."))
#需要导入的类
from base import log
from base.timer_thread import simple_task_thread
from save_take_photo import take_photo_context
from save_take_photo import save_take_photo
from save_image_record import image_record_context
from save_image_record import save_image_record
from save_point_record import point_record_context
from save_point_record import save_point_record

logger = get_logger("Send_to_PLC")
logger2 = get_logger("Produce_and_remove")
logger3 = get_logger("show_message")
logger4 = get_logger("point_record")

log.init_log("save_db")
log.info("===================================")
# logging.basicConfig()
# log = logging.getLogger()
# log.setLevel(logging.INFO)

from melsec_ctrl.melsec_ctrl import melsec_ctrl
import queue
import threading

'''
123--high
20200927,对宇新羊毛进行预写（同无锡远纺，1组相机带2套抓手）
20201031，现场测试完成，相机触发和回调，与PLC通讯正常，读取写入都正常
2020_1203,数据库录入（简单版）成功，访问成功，4G ip同网段下 192.168.2.150：8089
'''




class AiHjRunService:

    def __init__(self):
        self.__oPoolForRaster = ThreadPoolExecutor(3, "PoolForRasters")
        self.lock = threading.RLock()#队列线程锁，读写互斥，仅能进行一项
        self.bool_lock_time = False  # 读取PLC时间优先级判断
        self.lock_bmq = threading.Lock()#编码器线程锁
        self.record_queue = queue.Queue(maxsize=80)
        self.record_queue2 = queue.Queue(maxsize=40)  # -----抓手等待时，循环刷入此队列
        self.currentHomingCount = 0  # 手1抓取次数计数
        self.currentHomingCount2 = 0  # 手2抓取次数计数
        self._melsec_ctrl = melsec_ctrl()
        # 传送带速度
        self._conveyer_speed = aiCottonConfig.CONVEYER_SPEED
        # 抓手时间
        self._tongs_time = aiCottonConfig.TONGS_TIME
        # 抓手在横杆上的速度
        self._tongs_x_speed = aiCottonConfig.TONGS_X_SPEED
        # 设备间隔距离
        self._device_length = aiCottonConfig.DEVICE_LENTH
        # 拍照间隔时间
        self._take_photo_interval = aiCottonConfig.TAKE_PHOTO_INTERVAL

        self._count_down_latch = None
        #拍照参数
        self.cameraCtrlList = []  # 摄像机控制器列表
        self.cameraCtrlListDic = {} #全局相机拍照路径设置
        self.currentImgCount = 0  # 单次回调的照片数量
        #相机引脚号
        self.__output_pin = 18
        #GPIO初始化
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.__output_pin, GPIO.OUT, initial=GPIO.LOW)
        # #输入高低电平
        self.__gpio_value = GPIO.LOW #未改
        self.str1a = ''  # 编码器的地址，固定
        self.speed1 = 754.2
        self.speed2_K = 147.615 #编码值/mm
        self.speed2 = 0.09295 #单位M/s(覆盖的参数是mm/s)
        self.robot1 = True#抓手1可进行
        self.sleepdown1 = True  #PLC控制，生产者暂停信号
        self.dataZ1 =[]#去重数据组
        self.date_path1 = time.strftime("%Y_%m_%d",time.localtime())
        self.time_trigger = time.time()
        self.num_camera_back = 0
        self.choose_model1 = 0 #默认异纤种类（0-异纤 ，1-异纤+深黄毛 ， 2-异纤+深浅黄毛）
        self.list_zh1 = [["yixian"],["yixian", "shenhuangmao"],["qianhuangmao", "yixian", "shenhuangmao"]]
        # self.list_zh1 = [["qianhuangmao", "yixian", "shenhuangmao"], ["yixian", "shenhuangmao"], ["qianhuangmao", "yixian", "shenhuangmao"]]
        self.num_yixian1 = 0
        self.num_changeda = 0
        self.bool_xfz = False
        self.Camera_MAP = {"35024012": "A", "35024020": "C", "35024014": "B"}#左A右C中B
        self.point_start1 = 0  # 总生成点数
        self.point_start2 = 0  # 实际录入点数
        self.point_end1 = 0  # OK点数
        self.point_end2 = 0  # NG点数

        # 若要处理一些定时任务，比如自动删除旧的数据，需要开启下面定时任务线程
        self.oTaskThread = simple_task_thread("simple_task")
        self.oTaskThread.start()
        # 构造存储t_point_record操作，这个对象可以反复使用，非线程安全
        self.oSavePointRec = save_point_record()



    '''开机程序自检--PLC的读取，发送，相机触发拍照，返回，AI的返回'''
    def frist_check(self):
        try:
            print("----------开始自检----------")
            for ai1 in range(len(self.list_zh1)):
                print("类型{} ：{}".format(ai1, self.list_zh1[ai1]))

            '''PLC的读写'''
            print("-----PLC部分自检")
            name1 = aiCottonConfig.MELSEC_CODE.ZI_TEST1
            data = [123, 456, 789, 1024]
            name2 = aiCottonConfig.MELSEC_CODE.ZJ_XINHAO
            data2 = [77]
            result1 = self._melsec_ctrl.write_dword_data(name1, data)  # 写入
            if result1 is not None:
                print("数据写入PLC 成功")
                time.sleep(0.3)
                result2 = self._melsec_ctrl.read_dword_data(name1, 4)  # 读取
                if result2 is not None:
                    print("读取PLC 成功")
                    print("PLC起始地址：{}，数据为{}".format(name1, result2))
                    time.sleep(0.3)
                    data = [222, 222, 222, 222]
                    result1 = self._melsec_ctrl.write_dword_data(name1, data)  # 写入重置
                    result3 = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入重置自检信号位
                else:
                    print("无法读取PLC")
            else:
                print("数据未能写入PLC，请检查原因（IP，端口，集线器模式）")

            '''相机模块自检'''
            print("-----等待相机模块加载完成")
            time.sleep(2)
            print("-----Camera部分自检")
            image_path = self.generate_path(str(0))  # 返回图片存放路径，组
            self._count_down_latch = count_down_latch(len(aiCottonConfig.CAMERA_DEVICE_TUPLE))
            bResult = self.take_photo(image_path)
            if not bResult:
                print("相机拍照超时，take photo timeout!")
                print("请检查相机ID  触发参数")
                data2 = [11]
                self.write_signal(data2)
            else:
                '''相机对应的光源检测'''
                print("-----相机对应的光源检测")
                for key in self.cameraCtrlListDic:
                    value_grey1 = self.find_grey_value1(self.cameraCtrlListDic[key])
                    print("图片：{}---灰度值为：{}".format(key, value_grey1))
                    if value_grey1 is None:
                        print("读取图片或运算失败")
                    else:
                        if value_grey1 < 90:
                            print("图片亮度过低")
                        else:
                            print("图片亮度正常")

                '''AI模块自检————调用ai识别'''
                print("-----AI服务部分自检")
                ai_result = {}
                ai_status = True
                for key in self.cameraCtrlListDic:
                    position = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[key]  # 相机对应的位置
                    res = self.call_ai_service(self.cameraCtrlListDic[key])  # 调用ai服务，#返回字符串
                    if res is None:
                        ai_status = False
                        break
                    ai_result[position] = self.processAiData(res.get("data").get("0"), position)
                    # 返回像素点坐标，相机位置，世界坐标的字典 的列表
                if not ai_status:
                    print('AI 返回为None，AI服务出错')
                    data2 = [22]
                    self.write_signal(data2)
                else:
                    print("ai_result ----", ai_result)
                    data2 = [88]
                    self.write_signal(data2)
                    print("----------完成自检----------")
        except Exception as e:
            print(f"err---frist_check: {e}")

# ####---------------主函数部分-------------
    '''生产者--记录数据'''
    def run_produce_point_data(self):#生产者（产生点数据）
        value_min, value_max = None, None
        change_model1 = False
        name2 = aiCottonConfig.MELSEC_CODE.ZJ_XINHAO
        timea1 = time.time()
        photo_n = 10
        num_cam_timeout = 0
        self.judge_speed()#使用变频器时能使用
        self.read_choose_model()#开机读取异纤选择类别
        self.write_sleep_data(2)  # 开机完成信号
        #循环开始
        while True:
            try:
                if not self.sleepdown1:#PLC控制，待机（消费者传来的参数）
                    change_model1 = True
                    time.sleep(6.5)
                    continue
                if change_model1:#暂停后启动触发读取取值模式
                    change_model1 = False
                    self.read_choose_model()  # 重新启动后读取异纤选择类别

                if self.record_queue.full():
                    print('主队列已满')
                    for ia in range(6):  # 去除主队列6个数据
                        self.record_queue.get()
                    # time.sleep(0.1)
                    continue
                '''现在的拍照逻辑不需要等待'''
                # data = self.read_data(0) #将读取的值传给新建的data字典中，键为config中
                # if data is None:
                #     print('取不到PLC值')
                #     time.sleep(0.1)
                #     continue
                # # 将时间转成毫秒为单位
                # start_time = self.time2long(data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC),
                #                             data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC))
                # if next_take_photo_time > start_time:#自第二次起每次sleep,0.1秒，间隔延迟时间
                #     time.sleep(0.1)
                #     continue
                # next_take_photo_time = start_time + self._take_photo_interval#读到的时间，加延时时间

                image_path = self.generate_path(str(photo_n + 1))#返回图片存放路径，组
                # 拍照
                timea2 = time.time()
                ct1 = timea2 - timea1
                print('第{}次-------------执行一次拍照的时间为：{}        @@@'.format(str(photo_n + 1),ct1))
                timea1 = time.time()
                #设置条件变量，3颗相机在都超时限制内返回，为正常拍照
                self._count_down_latch = count_down_latch(len(aiCottonConfig.CAMERA_DEVICE_TUPLE))

                '''读取PLC的系统时间戳，并转换'''
                data = self.read_data(0)
                start_time = self.time2long(data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC),
                                            data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC))
                #开始循环前，已经判定了传送带的速度，并传入参数
                # self.speed2 = data.get(aiCottonConfig.MELSEC_CODE.CSD_SPEED1)
                speeedas2 = copy.deepcopy(self.speed2)
                # self.time_trigger = time.time()
                # print('001')
                bResult = self.take_photo(image_path)
                photo_n += 1  # 拍照计数+1
                # print('002')
                # print(" bResult = ",bResult)
                # time_save_pic = time.time()
                # lt_save_pc = time_save_pic - self.time_trigger
                # print("触发到存完图用时：{}s".format(lt_save_pc))
                # 获取图片超时
                if not bResult:
                    num_cam_timeout += 1
                    self.num_camera_back = 0
                    # print('003')
                    print("相机拍照超时，take photo timeout!")
                    if num_cam_timeout > 3:
                        num_cam_timeout = 0
                        data2 = [11]
                        self.write_signal(data2)
                    time.sleep(0.8)
                    continue
                self.num_camera_back = 0
                num_cam_timeout = 0#到这一步证明触发OK
                # print("@@@@@@@@@@@@@@-----({})---time:{}----speed:{}".format(photo_n, start_time, speeedas2))
                '''相机对应的光源检测'''
                num_test_light = photo_n % 50
                if num_test_light == 1:
                    print("------------------------------------------相机对应的光源检测******")
                    for key in self.cameraCtrlListDic:
                        value_grey1 = self.find_grey_value1(self.cameraCtrlListDic[key])
                        print("图片：{}---灰度值为：{}".format(key, value_grey1))
                        if value_grey1 is None:
                            print("读取图片或运算失败")
                        else:
                            if value_grey1 < 100:
                                print("图片亮度过低")
                            else:
                                print("图片亮度正常")
                            if value_min is None:
                                value_min = value_grey1
                            else:
                                value_min = min(value_min, value_grey1)
                            if value_max is None:
                                value_max = value_grey1
                            else:
                                value_max = max(value_max, value_grey1)
                    value_fd = value_max - value_min
                    print("最大的灰度值为：{}\n最小的灰度值为：{}\n浮动值为：{}".format(value_max, value_min, value_fd))
                # 调用ai识别
                ai_result = {}
                ai_status = True
                # time_AI_start = time.time()
                # print('006')
                for key in self.cameraCtrlListDic:
                    # print('010')
                    position = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[key]#相机对应的位置
                    res = self.call_ai_service(self.cameraCtrlListDic[key])#调用ai服务，#返回字符串
                    if res is None:
                        ai_status = False
                        break
                    # print('011')
                    ai_result[position] = self.processAiData(res.get("data").get("0"), position)
                    # 返回像素点坐标，相机位置，世界坐标的字典 的列表
                # time_AI_end = time.time()
                # lt_ai1 = time_AI_end - time_AI_start
                # print("AI调用到返回结果用时：{}".format(lt_ai1))
                # lt_ai2 = time_AI_end - time_save_pic
                # print("从发送数据给PLC到AI返回结果用时：{}".format(lt_ai2))
                # print('007')
                if not ai_status:
                    data2 = [22]
                    self.write_signal(data2)
                    print('AI 返回为None，AI服务出错')
                    continue
                # print("ai_result ----", ai_result)
                if ai_result is not None:
                    point_arr = self.caculate_nearly_point(ai_result)#舍去相机重合点
                    # print('point_arr',point_arr)
                    if point_arr is not None:
                        datapiont1 = self.remove_point2(point_arr,start_time,speeedas2)
                        # print("@@@@@@@@@@@@@@-----({})---time:{}----speed:{}".format(photo_n,start_time,speeedas2))
                        # self.put_record2queue(point_arr,start_time)#将点写入队列（生产者调用）
                        self.put_record2queue(datapiont1, start_time,speeedas2,photo_n)  # 将点写入队列（生产者调用）
                data2 = [88]
                self.write_signal(data2)
                # result3 = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入自检信号位
                # time.sleep(0.2)
                # print(" end produce ")
            except Exception as e:
                print(f"err---produce: {e}")
                time.sleep(0.8)

    '''消费者-消费数据'''
    def run_consume_point_record(self):  # 消费者（使用点数据）---抓手1+2
        zhua_a = 1 #用于锁定抓手
        zhua_b = 0 #用于判断读取抓手状态
        numzhua1_status, numzhua2_status = 0, 0
        numsleep1_status = 0
        time.sleep(0.4)  # 生产者调试对应
        t5 = None
        bool_t60 = True
        time1_t60 = time.time()
        onemoretime = True
        twomoretime = True
        while True:
            try:
                if self.bool_xfz:
                    print("进入抓手循环")
                    '''判断是否需要暂停，或超出单次检测时间'''
                    sleep_status1 = self.read_sleep_status()
                    if sleep_status1 == 0:#PLC需要保持为0
                        print("此时待机")
                        self.sleepdown1 = False#此时待机
                        self.record_queue.queue.clear()  # 因为要暂停，之前存在队列上的数据点就没用了
                        bool_t60 = True
                        time.sleep(5)
                        continue
                    else:
                        self.sleepdown1 = True#此时正常
                        if bool_t60:
                            bool_t60 = False
                            time1_t60 = time.time()
                        time2_t60 = time.time()
                        timelong_t60 = time2_t60 - time1_t60
                        if timelong_t60 > 1200 and onemoretime:
                            onemoretime = False
                            # self.sleepdown1 = False  # 此时待机
                            # self.record_queue.queue.clear()  # 因为要暂停，之前存在队列上的数据点就没用了
                            print("此次已检测20分钟，通知PLC转向")
                            self.write_sleep_data(1)  # 已运行20分钟，让PLC转向
                        if timelong_t60 > 2400 and twomoretime:
                            twomoretime = False
                            # self.sleepdown1 = False  # 此时待机
                            # self.record_queue.queue.clear()  # 因为要暂停，之前存在队列上的数据点就没用了
                            print("此次已检测40分钟，通知PLC换包")
                            self.write_sleep_data(3)  # 已运行40分钟，让PLC换包

                        if timelong_t60 > 120000:
                            self.sleepdown1 = False  # 此时待机
                            self.record_queue.queue.clear()  # 因为要暂停，之前存在队列上的数据点就没用了
                            print("此次已检测20分钟，暂停，更换检测品")
                            self.write_sleep_data(0)  # 60s无异纤，让PLC提醒
                            time.sleep(5)
                            continue

                    '''判断已经抓取次数'''
                    if self.currentHomingCount >= 100:  # 当抓手1运动计数超过次数，让抓手回原点
                        print("高处模组---抓手1---发送归位")
                        # self.record_queue2.put(point_record)
                        bResult = self.write_homing_data(1)  # 写入缓冲，返回socket响应的数据
                        # self.record_queue.queue.clear()  # 因为要暂停，之前存在队列上的数据点就没用了
                        self.currentHomingCount = 0
                        if bResult:  # 回原点确定
                            self.currentHomingCount = 0  # 计数值清零
                        time.sleep(0.1)
                        continue
                    if self.currentHomingCount2 >= 100:  # 当抓手1运动计数超过次数，让抓手回原点
                        print("高处模组---抓手2---发送归位")
                        # self.record_queue2.put(point_record)
                        bResult = self.write_homing_data(2)  # 写入缓冲，返回socket响应的数据
                        # self.record_queue.queue.clear()  # 因为要暂停，之前存在队列上的数据点就没用了
                        self.currentHomingCount2 = 0
                        if bResult:  # 回原点确定
                            self.currentHomingCount2 = 0  # 计数值清零
                        time.sleep(0.1)
                        continue

                    '''读取判断抓手1的状态'''
                    tong_status = self.read_tongs_status(1)  # X轴抓取中#X轴归位中
                    # print('tong_status', tong_status)
                    # print(" 抓手1--抓取中(状态):", tong_status.get(aiCottonConfig.MELSEC_CODE.TONGS_STATUS1))
                    # print(" 抓手1--归位中(状态):", tong_status.get(aiCottonConfig.MELSEC_CODE.HOMING_STATUS1))
                    # print(" 抓手2--抓取中(状态):", tong_status.get(aiCottonConfig.MELSEC_CODE.TONGS_STATUS2))
                    # print(" 抓手2--归位中(状态):", tong_status.get(aiCottonConfig.MELSEC_CODE.HOMING_STATUS2))
                    '''读取判断抓手1的状态'''
                    if not zhua_b == 2:  # 若是没被抓手2没锁定
                        bool_zs1_1 = tong_status.get(aiCottonConfig.MELSEC_CODE.TONGS_STATUS1)#抓取中
                        bool_zs1_2 = tong_status.get(aiCottonConfig.MELSEC_CODE.HOMING_STATUS1)#归位中
                        # print(" 抓手1--抓取中(状态):", tong_status.get(aiCottonConfig.MELSEC_CODE.TONGS_STATUS1))
                        # 抓手1忙碌时
                        if tong_status is None or bool_zs1_1 == 1 or bool_zs1_2 == 1:
                            zhua_a, zhua_b = 0, 0  # 不取队列，无比较动作(无脑解锁，清零)
                                # time.sleep(0.1)
                        else:
                            zhua_a, zhua_b = 1, 1  # 进入抓手1比较部分，并锁定
                    '''读取判断抓手2的状态'''
                    if not zhua_b == 1:  # 若是没被抓手1没锁定
                        bool_zs2_1 = tong_status.get(aiCottonConfig.MELSEC_CODE.TONGS_STATUS2)  # 抓取中
                        bool_zs2_2 = tong_status.get(aiCottonConfig.MELSEC_CODE.HOMING_STATUS2)  # 归位中
                        # print(" 抓手2--抓取中(状态):", tong_status.get(aiCottonConfig.MELSEC_CODE.TONGS_STATUS2))
                        # 抓手2忙碌时
                        if tong_status is None or bool_zs2_1 == 1 or bool_zs2_2 == 1:
                            zhua_a, zhua_b = 0, 0  # 不取队列，无比较动作(无脑解锁，清零)
                            time.sleep(0.3)#抓手1/2都在忙碌，等待一会儿
                        else:
                            zhua_a, zhua_b = 2, 2 # 进入抓手2比较部分，并锁定

                    '''准备取队列上的数据'''
                    if not zhua_a == 0: #锁定成抓手1/2（起码有一个抓手空闲）
                        zhua_b = 0  # 解锁
                        bool_read_point1 = True  # 读取队列信号，为了处理不合适时直接读取队列里的下一个数据点
                        while bool_read_point1:
                            bool_read_point1 = False
                            # 队列为空时休眠
                            if self.record_queue.empty() and self.record_queue2.empty():
                                '''判断是否长时间无异纤，并通知PLC暂停'''
                                t4 = time.time()
                                if t5 != None:
                                    time_l1 = t4 - t5
                                    if time_l1 > 6000:
                                        self.sleepdown1 = False  # 此时待机
                                        print("已有60s无异纤，休眠程序及抓手！")
                                        self.write_sleep_data(0)  # 60s无异纤，让PLC提醒
                                time.sleep(0.6)#无数据，可以停久一点
                                continue
                            t5 = time.time()
                            point_record = self.choose_point1(zhua_a)
                            # print("消费者1--point_record", point_record)
                            start_time = point_record.get("start_time")  # 从取到PLC和AI的值后开始计时
                            speed_bmq1 = point_record.get("speed")   # -----传送带速度#----mm/s
                            x = point_record.get("worldX") - aiCottonConfig.DIFF_X  # X值加减参数
                            y = point_record.get("worldY") - aiCottonConfig.LEFT_DIFF_Y
                            # ------------------------------------------------------------------------------------
                            if zhua_a == 1:
                                zhua_b = 0  # 一但进入判断，就解锁（不论抓不着还是去抓取）
                                y = y + 0 - 5 - 40  # 抓手1现场补偿值加大0mm,-5mm(加了连接板5mm)
                                '''读取PLC参数'''
                                data = self.read_data(1)#最后读取PLC系统时间，保证时间的准确性
                                # X轴当前速度
                                current_speed_x = data.get(aiCottonConfig.MELSEC_CODE.TONGS_X_SPEED1)
                                # print("消费者1--current_speed_x", current_speed_x)
                                current_speed_x = 520 #mm/s
                                current_x1 = data.get(aiCottonConfig.MELSEC_CODE.TONG_CURRENT_COORDINATES1)  # X轴当前坐标,mm
                                # print("消费者1--current_x1", current_x1)
                                will_time1 = abs(current_x1 - x) / current_speed_x + 0.3 #抓手从空闲位到抓到异纤的预测时间,s
                                '''---抓手到位预定长度'''
                                will_length = speed_bmq1 * will_time1  # 预计抓手移动需要的时间 mm
                                # 当前的时间点s*1000
                                current_time = self.time2long(data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC),
                                                              data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC))
                                # print("消费者1--current_time", current_time)
                                # 已经花费的时间s*1000
                                spend_time = current_time - start_time
                                '''---此刻异纤运动长度'''
                                spend_length = speed_bmq1 * spend_time/1000  # 传送带速度*时间=# 传送带走的距离
                                # print("------------------------------------------------------------------------------------")
                                '''筛选是否可以抓得到'''
                                if float(spend_length + will_length) < y:  # 此时，传送带未走到位，才有抓到的条件
                                    # 总时间
                                    total_time = ((y / speed_bmq1) - 0.3)*1000  # 总时间（点到Y轴的时间）
                                    # 下抓时间
                                    end_time = total_time - self._tongs_time + start_time
                                    sec, mill_sec = self.long2time(end_time)  # 毫秒转时间
                                    print("------1---@@@@--------秒：{} 毫秒：{}".format(int(sec), int(mill_sec)))
                                    print('point_record', point_record)
                                    self.write_data(int(sec), int(mill_sec), int(x), 0, 0, 1)
                                    bool_read_point1 = False#跳出循环取队列
                                    # logger.info("1----piont_message---{}".format(point_record))
                                    self.currentHomingCount += 1
                                    self.point_end1 += 1
                                    logger4.info("===总：{} 使用：{} 舍去：{}--------该点传给PLC：{}".format(
                                        int(self.point_end1 + self.point_end2), self.point_end1, self.point_end2,
                                        point_record))
                                    list_point = [point_record.get("ID_tp"), point_record.get("position"),
                                                  point_record.get("speed"), point_record.get("x_max"),
                                                  point_record.get("y_max"), point_record.get("x_min"),
                                                  point_record.get("y_min"), point_record.get("worldX"),
                                                  point_record.get("worldY"), 4]
                                    self.write_mysql1(list_point)
                                    time.sleep(0.1)
                                else:
                                    self.record_queue2.put(point_record)

                                    # bool_zs2_12 = tong_status.get(aiCottonConfig.MELSEC_CODE.TONGS_STATUS2)  # 抓取中
                                    # bool_zs2_22 = tong_status.get(aiCottonConfig.MELSEC_CODE.HOMING_STATUS2)  # 归位中
                                    # # 抓手2忙碌时
                                    # if tong_status is None or bool_zs2_12 == 1 or bool_zs2_22 == 1:
                                    #     pass
                                    #     # bool_read_point1 = False#跳出循环取队列，， #抓手2忙碌时存入次队列，等待之后空闲
                                    # else:
                                    #     print("小循环--抓手2状态：{}---{}".format(bool_zs2_12, bool_zs2_22))
                                    #     zhua_a = 2  #进行小循环，进入抓手2，及时取到次队列

                            # --------------------------------------------------------------------------------
                            elif zhua_a == 2:
                                zhua_b = 0  # 一但进入判断，就解锁（不论抓不着还是去抓取）
                                y = y + 607 + 5 - 30 #抓手2与抓手1相距607mm+5mm(加了连接板5mm)
                                '''读取PLC参数'''
                                data = self.read_data(2)
                                # X轴当前速度
                                current_speed_x = data.get(aiCottonConfig.MELSEC_CODE.TONGS_X_SPEED2)  # X轴当前速度
                                # print("消费者2--current_speed_x", current_speed_x)
                                current_speed_x = 520
                                current_x1 = data.get(aiCottonConfig.MELSEC_CODE.TONG_CURRENT_COORDINATES2)  # X轴当前坐标
                                # print("消费者2--current_x1", current_x1)
                                will_time1 = abs(current_x1 - x) / current_speed_x + 0.1
                                '''---抓手到位预定长度'''
                                will_length = speed_bmq1 * will_time1  # 预计抓手移动需要的时间
                                # 当前的时间
                                current_time = self.time2long(data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC),
                                                              data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC))
                                # print("消费者1--current_time", current_time)
                                # 已经花费的时间
                                spend_time = current_time - start_time
                                '''---此刻异纤运动长度'''
                                spend_length = speed_bmq1 * spend_time/1000  # 传送带速度*时间=# 传送带走的距离
                                '''筛选是否可以抓得到'''
                                if float(spend_length + will_length) < y:  # 此时，传送带未走到位，才有抓到的条件
                                    # 总时间
                                    total_time = (y / speed_bmq1-0.3)*1000  # 总时间（点到Y轴的时间）
                                    end_time = total_time - self._tongs_time + start_time  # 下抓时间
                                    sec, mill_sec = self.long2time(end_time)  # 毫秒转时间
                                    # print("2-----start_time ----", start_time)
                                    # print("2-----end_time ----", end_time)
                                    # print("2-----sec ----", sec)
                                    # print("2-----mill_sec ----", mill_sec)
                                    # print("2-----x ------", x)
                                    self.write_data(int(sec), int(mill_sec), int(x), 0, 0, 2)
                                    print("------2---@@@-----------秒：{} 毫秒：{}".format(int(sec),  int(mill_sec)))
                                    print('point_record', point_record)
                                    bool_read_point1 = False  # 跳出小循环，重新读抓手1/2状态
                                    # logger.info("2----piont_message---{}".format(point_record))
                                    self.currentHomingCount2 += 1
                                    self.point_end1 += 1
                                    logger4.info("===总：{} 使用：{} 舍去：{}--------该点传给PLC：{}".format(
                                        int(self.point_end1 + self.point_end2), self.point_end1, self.point_end2,
                                        point_record))
                                    list_point = [point_record.get("ID_tp"), point_record.get("position"),
                                                  point_record.get("speed"), point_record.get("x_max"),
                                                  point_record.get("y_max"), point_record.get("x_min"),
                                                  point_record.get("y_min"), point_record.get("worldX"),
                                                  point_record.get("worldY"), 4]
                                    self.write_mysql1(list_point)
                                    time.sleep(0.1)
                                else:
                                    #该点对于抓手2还是不合格，重新大循环，不管抓手1的状态了
                                    print("2-----由于超出极限，抓手把该点抛掉")
                                    self.point_end2 += 1
                                    logger4.info(
                                        "+++总：{} 使用：{} 舍去：{}--------该点舍去：{}".format(
                                            int(self.point_end1 + self.point_end2),
                                            self.point_end1, self.point_end2,
                                            point_record))
                                    list_point = [point_record.get("ID_tp"), point_record.get("position"),
                                                  point_record.get("speed"), point_record.get("x_max"),
                                                  point_record.get("y_max"), point_record.get("x_min"),
                                                  point_record.get("y_min"), point_record.get("worldX"),
                                                  point_record.get("worldY"), 5]
                                    self.write_mysql1(list_point)
                                    # bool_zs2_11 = tong_status.get(aiCottonConfig.MELSEC_CODE.TONGS_STATUS1)  # 抓取中
                                    # bool_zs2_21 = tong_status.get(aiCottonConfig.MELSEC_CODE.HOMING_STATUS1)  # 归位中
                                    # # 抓手2忙碌时
                                    # if tong_status is None or bool_zs2_11 == 1 or bool_zs2_21 == 1:
                                    #     pass
                                    #     # bool_read_point1 = False#跳出循环取队列，， #抓手2忙碌时存入次队列，等待之后空闲
                                    # else:
                                    #     print("小循环--抓手1状态：{}---{}".format(bool_zs2_11, bool_zs2_21))
                                    #     zhua_a = 1  # 进行小循环，重新从抓手1开始（此时抓手1、2都空闲，点不合适）
                                    # time.sleep(0.1)
                else:
                    print("正在自检，或等待传送带开启")
                    time.sleep(3)
            except Exception as e:
                print(f"err---+++++++: {e}")
                quit()

    '''计算图片的灰度值'''
    def find_grey_value1(seil, imgpath):
        try:
            img1 = Image.open(imgpath)
            img1.thumbnail((1, 1))
            avg_color = img1.getpixel((0, 0))
            grey_value = round(0.3 * avg_color[0] + 0.6 * avg_color[1] + 0.1 * avg_color[2])
            print('grey_value', grey_value)
            # if grey_value < 90:
            #     print("现场光源亮度过低")
            return grey_value
        except Exception as ex:
            print(ex)
            print('ERROR: light_detection fault')
            return None


    '''循环自增数，1~100，给PLC发送变化数据，自证连接正常'''
    def num_changed1(self):
        self.num_changeda += 1
        if self.num_changeda > 100:
            self.num_changeda = 1
        return self.num_changeda

    '''判断传送带的速度是否稳定'''
    def judge_speed(self):
        bool_jud_sp1 = True
        old_speed = None
        name2 = aiCottonConfig.MELSEC_CODE.ARM_XINHAO

        while bool_jud_sp1:

            cds_speed = self.read_speed().get(aiCottonConfig.MELSEC_CODE.CSD_SPEED1)  # 取PLC上的传送带速度
            # cds_speed = 2300
            if cds_speed < 500:
                print("读取的传送带的速度值太低")
                data2 = [self.num_changed1()]
                print("自增数：{}".format(str(data2[0])))
                result3 = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入自检信号位-断连状态
                time.sleep(1.5)
                continue
            print('cds_speed', cds_speed)
            if old_speed is not None:  # 开始时old_speed为空，避免第1次
                if cds_speed - old_speed < 50:  # 前后2次速度，趋于稳定#1102数值改写
                    # self.speed2 = cds_speed  # 写入速度
                    self.speed2 = self.transform_conveyer_speed(cds_speed) # 写入速度
                    print("检测到现在传送带速度为：{} mm/s".format(self.speed2))
                    if self.speed2 > 400:
                        print("检测到传送带速度过快")
                    self.bool_xfz = True
                    bool_jud_sp1 = False  # 关闭循环
            if cds_speed is not None and cds_speed > 0:  # 取到速度值且不是静止
                old_speed = copy.deepcopy(cds_speed)
                time.sleep(0.5)

    '''去重___前后拍照数据筛选'''
    def remove_point2(self, pointZ1, time01, speeda1):
        i, k = 0, 0

        for pa1 in pointZ1:
            if len(pa1) > 0:  # 单个点里有值
                k += 1

        if k > 0:  # =0时，说明传过来的是空值，不进行操作
            dataZ2 = copy.deepcopy(self.dataZ1)
            pointZ2 = copy.deepcopy(pointZ1)
            # logger2.info("now_point_or---:{},,s:{},t:{}".format(pointZ1, speeda1, time01))

            if not len(dataZ2) == 0:  # 当存储器有值时，进行对比
                for pointZC in dataZ2:  # dataZ2=[[],[],[]]------pointZC=[time,[{},{},{}]]
                    key1 = pointZC[0]
                    # 对比存储器中的个时间点组（超限-舍去，不超-对比）
                    if time01 - key1 > ((570 / speeda1) + 2.2) * 1000:
                        # print('点的时间超过限制：{}'.format(pointZC))
                        self.dataZ1.remove(pointZC)  # 去掉超出限制的点
                    else:
                        for pointb2 in pointZ2:  # 最新的点组pointZ2=[{},{},{}] , pointb2={}=value1
                            for value1 in pointZC[1]:  # pointZC=[time,[{},{},{}]], #value1字典{X， Y，position,WX,WY}
                                if abs(value1["worldX"] - pointb2["worldX"]) < 40:  # 先对比X，若不同，应该不是同一个点
                                    l1 = round(speeda1 * (time01 - key1) / 1000, 2)  # 2组数据实际的距离
                                    l2_rm1 = max(35, abs(round((time01 - key1)/1000, 2)) * 13.2) #随时间跨度而增加的Y方向重合限制，起始值35
                                    if abs(float(value1["worldY"] - pointb2[
                                        "worldY"]) - l1) < l2_rm1:  # 新点pointb2 +l1 == 旧点value1
                                        # print('点的位置重复：\n保留点--{}\n去除点--{}'.format(value1, pointb2))

                                        pointZ1.remove(pointb2)
            if len(pointZ1) > 0:
                self.dataZ1.append([time01, pointZ1])
                logger2.info("Save_pool---:{}".format(self.dataZ1))
                # for q in range(len(self.dataZ1)):
                # print('========={}--{}'.format(q + 1, self.dataZ1[q]))
                # print('此次传出的数据-------------------{}'.format(pointZ1))
                return pointZ1
            else:
                return None
        else:
            return None

    '''写入数据库'''

    def write_mysql1(self, list1):
        # 现在演示插入新记录到t_point_record
        oPointRecordContext = point_record_context()
        oPointRecordContext.take_photo_id = int(list1[0])  # 拍照编号
        oPointRecordContext.image_id = int(list1[1])  # 图片编号
        oPointRecordContext.speed = int(list1[2])  # 传送带速度
        oPointRecordContext.point_xmax = int(list1[3])  # 点的最大x坐标
        oPointRecordContext.point_ymax = int(list1[4])  # 点的最大y坐标
        oPointRecordContext.point_xmin = int(list1[5])  # 点的最小x坐标
        oPointRecordContext.point_ymin = int(list1[6])  # 点的最小y坐标
        oPointRecordContext.point_xcenter = int(list1[7])  # 点的中心x坐标
        oPointRecordContext.point_ycenter = int(list1[8])  # 点的中心y坐标
        oPointRecordContext.state = int(list1[9])  # 状态[1:新增;2;超出边缘;3:重复;4:成功抓取;5:来不及抓取]
        if not self.oSavePointRec.execute(oPointRecordContext):
            print("插入t_point_record失败")
            return
        # end if
        print("插入t_point_record成功，记录ID为：%s" % oPointRecordContext.point_id)


    '''存入队列'''
    def put_record2queue(self,point_arr,start_time,speed1,num_tp):#将点写入队列（生产者调用）
        # print( " point_arr ",point_arr)
        if point_arr is not None:
            num_tp_i = 0
            for item in point_arr:
                item["speed"] = speed1
                item["start_time"] = start_time  # 在每组坐标的字典上添加开始时间的对应组
                num_tp_i += 1
                self.point_start1 += 1
                item["ID_tp"] = num_tp
                item["ID_point"] = str(num_tp) + "_" + str(num_tp_i)
                if not self.record_queue.full():
                    # print(" put to queue ")
                    self.record_queue.put(item)  # 放到队列里
                    self.point_start2 += 1
                else:
                    break
            if num_tp_i > 0:
                logger4.info("第{}次,本轮生成{}个点-----累计生成{}个点，成功录入{}个点".format(num_tp, num_tp_i, self.point_start1,
                                                                          self.point_start2))

    '''读取队列'''

    '''读取队列'''
    def choose_point1(self,numAB):
        #抓手1只读主队列，抓手2读次队列
        bool_chpo1 = True
        while bool_chpo1:
            if numAB == 1:
                if self.record_queue.empty():
                    rePP1 = None
                else:
                    rePP1 = self.record_queue.get()

                # if rePP1 is None:
                #     time.sleep(0.2)
                #     continue
                # else:
                #     bool_chpo1 = False
                # return rePP1
            else:
                if self.record_queue2.empty():
                    if self.record_queue.empty():
                        rePP1 = None
                        # print('no--取到队列数据', rePP1)
                    else:
                        rePP1 = self.record_queue.get()
                        # print('取到队列1数据', rePP1)
                else:
                    rePP1 = self.record_queue2.get()
                    # print('取到队列二数据', rePP1)
            if rePP1 is None:
                time.sleep(0.2)
                continue
            else:
                bool_chpo1 = False

        return rePP1


# ####---------------读写PLC-------------
    '''读取PLC的系统时间'''
    def read_data(self, zs_numb2):  # （生产者，消费者各调用2次，读取PLC的返回数据）
        if zs_numb2 == 0:
            # print("主程序调用PLC通讯")
            self.bool_lock_time = True
        self.lock.acquire()  # 线程加锁
        try:
            if zs_numb2 == 0 or zs_numb2 == 8:

                # name01 = aiCottonConfig.MELSEC_CODE.CSD_SPEED1
                # bReadData = self._melsec_ctrl.read_dword_data(name01, 1)
                # print("jr1")
                result = self._melsec_ctrl.read_dword_data(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC, 2)  # 返回数组
                name2 = aiCottonConfig.MELSEC_CODE.ARM_XINHAO
                data2 = [self.num_changed1()]
                # print('写入自检信号位-断连状态', data2)
                result3 = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入自检信号位-断连状态
                # print('result',result)
                # print("jr2")
                if result is not None:  # 有值
                    data = {
                            aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC: result[0],
                            aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC: result[1]
                            # name01: bReadData[0]
                    }
                    return data  # 将读取的值传给新建的data字典中，键为config中
                else:
                    return None
            else:
                if zs_numb2 == 1:
                    name3 = [aiCottonConfig.MELSEC_CODE.TONGS_X_SPEED1,
                             aiCottonConfig.MELSEC_CODE.TONGS_ORIGIN_COORDINATES1,
                             aiCottonConfig.MELSEC_CODE.TONS_LIMIT_AFTER_COORDINATES1,
                             aiCottonConfig.MELSEC_CODE.TONS_LIMIT_PRE_COORDINATES1,
                             aiCottonConfig.MELSEC_CODE.TONG_CURRENT_COORDINATES1]
                else:
                    name3 = [aiCottonConfig.MELSEC_CODE.TONGS_X_SPEED2,
                             aiCottonConfig.MELSEC_CODE.TONGS_ORIGIN_COORDINATES2,
                             aiCottonConfig.MELSEC_CODE.TONS_LIMIT_AFTER_COORDINATES2,
                             aiCottonConfig.MELSEC_CODE.TONS_LIMIT_PRE_COORDINATES2,
                             aiCottonConfig.MELSEC_CODE.TONG_CURRENT_COORDINATES2]
                result = self._melsec_ctrl.read_dword_data(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC, 2)  # 返回数组
                result1 = self._melsec_ctrl.read_dword_data(name3[0], 5)  # 返回数组
                if result is not None:  # 有值
                    data = {
                        aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC: result[0],
                        aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC: result[1],
                        name3[0]: result1[0],
                        name3[1]: result1[1],
                        name3[2]: result1[2],
                        name3[3]: result1[3],
                        name3[4]: result1[4]
                    }
                    return data  # 将读取的值传给新建的data字典中，键为config中

            return None
        finally:
            self.bool_lock_time = False
            self.lock.release()

    '''写入信号位'''
    def write_signal(self,data3):
        while self.bool_lock_time:
            time.sleep(0.1)
        else:
            self.lock.acquire()
            try:
                name2 = aiCottonConfig.MELSEC_CODE.ZJ_XINHAO
                # data2 = [22]
                result3 = self._melsec_ctrl.write_dword_data(name2, data3)  # 写入自检信号位
                time.sleep(0.2)
                # data3 = [88]
                # result3 = self._melsec_ctrl.write_dword_data(name2, data3)  # 写入自检信号位
                return result3
            finally:
                self.lock.release()



    '''读取抓手状态（忙碌/空闲）'''
    def read_tongs_status(self,zs_numb): #在消费者中被调用
        while self.bool_lock_time:
            time.sleep(0.1)
        else:
            self.lock.acquire()#线程锁
            try:
                name1 = aiCottonConfig.MELSEC_CODE.TONGS_STATUS1
                name2 = aiCottonConfig.MELSEC_CODE.HOMING_STATUS1
                name3 = aiCottonConfig.MELSEC_CODE.TONGS_STATUS2
                name4 = aiCottonConfig.MELSEC_CODE.HOMING_STATUS2
                bReadData1 = self._melsec_ctrl.read_bit_data(name1, 3)#返回2组值
                # print('bReadData1',bReadData1)
                bReadData2 = self._melsec_ctrl.read_bit_data(name3, 3)  # 返回2组值
                # print('bReadData2', bReadData2)
                if bReadData1 is not None and bReadData2 is not None:
                    data = {
                        name1: bReadData1[0],
                        name2: bReadData1[2],
                        name3: bReadData2[0],
                        name4: bReadData2[2]
                    }
                    # print("抓手状态".format(data))
                    return data##X轴抓取中#X轴归位中
                return None
            finally:
                self.lock.release()

    '''读取抓手状态（是否需要待机）'''
    def read_sleep_status(self):  # 在消费者中被调用
        while self.bool_lock_time:
            time.sleep(0.1)
        else:
            self.lock.acquire()  # 线程锁
            try:
                name01 = aiCottonConfig.MELSEC_CODE.STOP_ALL1
                bReadData = self._melsec_ctrl.read_bit_data(name01, 1)  # 返回
                if bReadData is not None:
                    data = {
                        name01: bReadData[0]
                    }
                    return data
                return None
            finally:
                self.lock.release()

    '''读取传送带的速度'''
    def read_speed(self):
        '''在所有PLC通讯之前，不必加优先级线程锁信号'''
        self.lock.acquire()  # 线程锁
        try:
            name01 = aiCottonConfig.MELSEC_CODE.CSD_SPEED1
            bReadData = self._melsec_ctrl.read_dword_data(name01, 1)  #
            if bReadData is not None:
                data = {
                    name01: bReadData[0]
                }
                return data
            return None
        finally:
            self.lock.release()

    '''读取异纤识别种类'''
    def read_choose_model(self):
        '''在所有PLC通讯之前，或是当时刚重新开始启动'''
        self.lock.acquire()  # 线程锁
        try:

            name01 = aiCottonConfig.MELSEC_CODE.CHOOSE_MODEL
            # print('name01',name01)
            bReadData = self._melsec_ctrl.read_dword_data(name01, 1)  #
            # print('bReadData',bReadData)
            if bReadData is not None:
                data = {
                    name01: bReadData[0]
                }
                self.choose_model1 = bReadData[0]
                print('data',data)
                return data

            return None
        finally:
            self.lock.release()

    '''写入抓取时间和坐标等数据'''
    def write_data(self,sec,millsec,x,feedback_x,feedback_speed,zs_numb3):#最后2个，反馈x,反馈速度（消费者调用）
        while self.bool_lock_time:
            time.sleep(0.1)
        else:
            self.lock.acquire()
            try:
                if zs_numb3 ==1:
                    name4 = aiCottonConfig.MELSEC_CODE.GRAB_TIME_SEC1
                else:
                    name4 = aiCottonConfig.MELSEC_CODE.GRAB_TIME_SEC2
                data = [sec,millsec,x,feedback_x,feedback_speed]
                result1 = self._melsec_ctrl.write_dword_data(name4,data)#抓取时间戳
                #result2 = self._melsec_ctrl.write_dword_data(aiCottonConfig.MELSEC_CODE.GRAB_TIME_MILLSEC, [millsec])
                if result1 is not None:
                    return True
                return False
            finally:
                self.lock.release()

    '''抓手回原点'''
    def write_homing_data(self,zs_numb1):#（消费者调用）
        while self.bool_lock_time:
            time.sleep(0.1)
        else:
            self.lock.acquire()
            try:
                if zs_numb1 == 1:
                    name2 = aiCottonConfig.MELSEC_CODE.TONGS_HOMING1
                else:
                    name2 = aiCottonConfig.MELSEC_CODE.TONGS_HOMING2
                return self._melsec_ctrl.write_bit_data(name2,[1])
            finally:
                self.lock.release()

    '''向PLC写入休眠信号'''
    def write_sleep_data(self,num_onemt):#（消费者调用）(向PLC写入休眠信号)
        while self.bool_lock_time:
            time.sleep(0.1)
        else:
            self.lock.acquire()
            try:
                if num_onemt == 0:
                    name3 = aiCottonConfig.MELSEC_CODE.SLEEP_PLC
                elif num_onemt == 2:
                    print("写入M50，1")
                    name3 = aiCottonConfig.MELSEC_CODE.START_OK
                elif num_onemt == 3:
                    name3 = aiCottonConfig.MELSEC_CODE.CHANGE_OK
                else:
                    name3 = aiCottonConfig.MELSEC_CODE.DO_ONE_TIME_PLC
                self._melsec_ctrl.write_bit_data(name3, [1])
                if num_onemt == 2:
                    return True
                else:
                    time.sleep(0.1)
                    return self._melsec_ctrl.write_bit_data(name3, [0])
            finally:
                self.lock.release()


# ####---------------相机拍照/相机回调/图片存放-------------

    '''拍照并等待相机返回'''
    def take_photo(self, cameraCtrlListDic):
        self.currentImgCount = 0
        self.cameraCtrlListDic = cameraCtrlListDic
        self.takePhoto()
        # print("wait take_photo")
        # startTime = time.time()
        bResult = self._count_down_latch.wait_with_timeout(2)#超时等待3组
        return bResult

    '''触发拍照-电平触发-上升沿'''
    def takePhoto(self):
        tp11 = 1
        if tp11 == 1:
            GPIO.output(self.__output_pin, GPIO.HIGH)#触发低电平
            time.sleep(0.0001) #sleep 0.1ms
            GPIO.output(self.__output_pin, GPIO.LOW)#触发高电平
        else:
            for i in range(20):
                print("{}".format(2 * i))
                GPIO.output(self.__output_pin, GPIO.LOW)
                time.sleep(2)
                print("{}".format(2 * i + 1))
                GPIO.output(self.__output_pin, GPIO.HIGH)
                time.sleep(2)
    '''相机回调--相机有图像传回来时，相机自己调用，且回将print显示在主程序命令行中'''
    def on_new_image(self, astrSerial, aoImage):
        '''
        拍照回调方法
        astrSerial 设备序列号
        aoImage 内存中的图
        '''
        # self.num_camera_back += 1
        # if self.num_camera_back > 2:
        #     time_back_camera = time.time()
        #     lt_cam = time_back_camera - self.time_trigger
        #     print("相机触发返回时间：{}s".format(lt_cam))
        # print("start recive image ", astrSerial)

        imageSaveName = self.cameraCtrlListDic.get(astrSerial)#返回字典里‘astrSerial’键的值
        if imageSaveName != None:
            # save_pic_1 = time.time()
            isSaveImageSuccess = self.saveImageFile(astrSerial, aoImage, imageSaveName)#存图片
            # save_pic_2 = time.time()
            # lt_save_pic = save_pic_2 - save_pic_1
            # print("{} ：{}".format(astrSerial,lt_save_pic))
            # self.currentImgCount += 1
            self._count_down_latch.count_down()
            # print("isSaveImageSuccess: ", isSaveImageSuccess, " imagePath:", imageSaveName)

    '''保存图片(相机调用部分)'''
    def saveImageFile(self, astrSerial, aoImage, asaveImgAddrss):#存图片，底行代码
        if aiCottonConfig.MOCK_SAVE_IMAGE:
            time.sleep(aiCottonConfig.MOCK_SAVE_IMAGE_RESULT_TIME)#sleep时间
            return True
        isSaveImageSuccess = True
        # start = time.time()
        try:
            cv2.imwrite(asaveImgAddrss, aoImage)#保存图片名，路径
            isSaveImageSuccess = True
        except Exception as e:
            print("cv2.imwrite strSaveName:%s, aoImage:%s" % (asaveImgAddrss, aoImage))
            isSaveImageSuccess = False
        return isSaveImageSuccess

    '''图片存放路径'''
    def generate_path(self,num_tp):#返回图片存放路径，组#（生产者调用）
        camera_path = {}  # 存放相机号对应的路径
        '''确保路径存在'''
        if int(num_tp) < 2:
            path_save_date01 = "/mnt/data/"
            if not os.path.exists(path_save_date01):
                os.makedirs(path_save_date01)
            path_save_date02 = path_save_date01 + "data/"
            if not os.path.exists(path_save_date02):
                os.makedirs(path_save_date02)
            path_save_date03 = path_save_date02 + "image_original/"
            if not os.path.exists(path_save_date03):
                os.makedirs(path_save_date03)

        path_save_date1 = "/mnt/data/data/image_original/img_" + self.date_path1 + "/"
        path_time_Hm1 = time.strftime("%H_%M", time.localtime())
        for deviceItem in aiCottonConfig.CAMERA_DEVICE_TUPLE:  # deviceItem为设备号
            cam_n = self.Camera_MAP[deviceItem]
            relativePath = "%s_%s_%s.jpg" % (cam_n, path_time_Hm1, num_tp)
            if not os.path.exists(path_save_date1):
                os.makedirs(path_save_date1)
            path = path_save_date1 + relativePath
            camera_path[deviceItem] = path

        return camera_path

# ####---------------AI返回/数据处理-------------
    '''调用ai处理'''
    def call_ai_service(self,image_path):
        try:
            response = requests.get(aiCottonConfig.AI_INFER_ADDRESS, params={'imagePath': image_path})#返回的是一个包含服务器资源的Response对象

            response.content.decode("utf-8")#response.content返回的类型是bytes，可以通过decode()方法将bytes类型转为str类型
            strs = json.loads(response.text)
            return strs
        except Exception as e:
            return None

    '''将AI返回值换算成世界坐标'''
    '''
    @@--1----res_data:{'boxes': [[572.4351806640625, -3.299999952316284, 1054.1461181640625, 335.8999938964844], 
                                [627.5390625, 401.0, 1032.510986328125, 886.2000122070312], 
                                [627.5390625, 1564.0999755859375, 1150.1297607421875, 1968.7000732421875], 
                                [1885.7249755859375, 770.4000244140625, 2340.900146484375, 1220.0]],
                      'scores': [0.7993741035461426, 0.6471705436706543, 0.4785524904727936, 0.4358397126197815], 
                      'labels': ['kongqiangmao', 'kongqiangmao', 'shenhuangmao', 'kongqiangmao'],
                      'class_scores': [], 
                      'img_exist': 1}
    @@--2----res_data:{'boxes': [[585.703125, -53.60000228881836, 1181.4468994140625, 526.0], 
                                [69.8062515258789, 1469.0, 619.171875, 2057.400146484375]], 
                       'scores': [0.6386441588401794, 0.6301180124282837], 
                       'labels': ['kongqiangmao', 'kongqiangmao'], 
                       'class_scores': [], 
                       'img_exist': 1}
    @@--3----res_data:{'boxes': [[1922.5406494140625, 1384.5999755859375, 2407.359375, 2055.400146484375], 
                                [1267.62890625, -19.399999618530273, 1736.9085693359375, 677.4000244140625], 
                                [1361.1024169921875, 1611.0, 1756.272705078125, 2021.0], 
                                [72.67500305175781, 1249.0, 582.3562622070312, 1869.4000244140625]], 
                      'scores': [0.7632113695144653, 0.7357710599899292, 0.7287100553512573, 0.7156181335449219], 
                      'labels': ['kongqiangmao', 'kongqiangmao', 'kongqiangmao', 'kongqiangmao'], 
                      'class_scores': [], 
                      'img_exist': 1}
    '''
    def processAiData(self, res_data, position):#返回像素点坐标，相机位置，世界坐标的字典 的列表#（生产者调用）
        bool_choose1 = 1
        num_choose1 = 0
        if bool_choose1 == 1:
            list_choose1 = []#要舍去的标签类型，下标数列表
            list_choose2 = []
            # list_zh1 = ["qianhuangmao", "yixian", "kongqiangmao", "shenhuangmao"]
            # list_zh1 = ["yixian", "kongqiangmao", "shenhuangmao"]
            ch_data = res_data["labels"]
            # print(1234)
            # print('int(self.choose_model1)',int(self.choose_model1))
            # print('self.list_zh1',self.list_zh1)
            # print('list_zh1',self.list_zh1[int(self.choose_model1)])
            for in_data in ch_data:
                num_choose1 += 1
                if in_data not in self.list_zh1[int(self.choose_model1)]:#某点的标签不在需求表上，说明这点要舍去，记下此下标值
                    list_choose1.append(num_choose1)
                elif in_data == "yixian":
                    list_choose2.append(num_choose1)

        else:
            list_choose1 = []  # 要舍去的标签类型，下标数列表
            list_choose2 = []
        #
        # print('@@--{}----res_data:{}'.format(position, res_data))
        data = res_data["boxes"]#预计是 字典键“boxes”对应的值
        arr = []
        num_choose2 = 0
        for list in data:#AI取到的点数据
            num_choose2 += 1
            if num_choose2 in list_choose1:#此点下标值在舍去表里，舍去
                # print("此点为空腔毛，舍去")
                continue
            elif num_choose2 in list_choose2:
                self.num_yixian1 += 1
                print("此点为异纤，共计{}个".format(self.num_yixian1))
            # print(11)
            if list[1] < 50 or list[3] > 2000:#Y方向，靠近边缘，极有可能是识别不全，舍去
                continue
            if list[0] < 100 or list[2] > 2348:#X方向，靠近边缘，极有可能是识别不全，舍去(相邻相机重合370pix)
                continue
            x = (list[0] + list[2]) / 2#图片中的像素坐标
            # print("Y:--list[1]:{}   ,list[3]:{}".format(list[1],list[3]))
            y = (list[1] + list[3]) / 2
            worldx,worldy,worldz = image_points_to_world_plane(x,y,int(position))#换算过后的世界坐标
            if int(position) == 1:
                if worldx > 779 + 0:
                    continue
            if int(position) == 2:
                if worldx < 1463 - 0:
                    continue
            # print("world_x !!!!!!!!!!", worldx, worldy)
            map = {"x": x, "y": y, "position": position, "worldX": abs(worldx), "worldY": abs(worldy), "x_min": list[0],
                   "x_max": list[2], "y_min": list[1], "y_max": list[3]}
            arr.append(map)

        return arr

    '''计算最近的异纤距离'''
    def caculate_nearly_point(self,ai_result):#计算是否是相机重复取同一点，或相近点
        # print(" caculate_nearly_point enter")
        result1 = ai_result.get("1")
        result2 = ai_result.get("2")
        result3 = ai_result.get("3")#3是中间相机（此设备的特例）
        real_point_arr = []

        if len(result3) == 0:#若相机3没有返回的数据
            for data1 in result1:
                if self.X_cutting1(data1):
                    real_point_arr.append(data1)  # 不相近，则录入
            for data2 in result2:
                if self.X_cutting1(data2):
                    real_point_arr.append(data2)  # 不相近，则录入
        else:
            i,j = 0,0
            l1 = []
            for data2 in result2:
                i +=1
                # print('相机C',i)
                for data3 in result3:
                    j += 1
                    # print('相机C', j)
                    # 对比所有result3上的点，若是相近，删掉result2上的某点
                    if self.checkPoint(data2,data3,aiCottonConfig.REAL_POINT_LIMIT):
                        l1.append(data2)#重合时暂存入L1，并跳出循环
                        break
                if data2 not in l1:
                    if self.X_cutting1(data2):
                        real_point_arr.append(data2) #不相近，则录入
            i, j = 0, 0
            for data1 in result1:
                i += 1
                # print('相机A', i)
                for data3 in result3:
                    j += 1
                    # print('相机A', j)
                    if self.checkPoint(data1,data3,aiCottonConfig.REAL_POINT_LIMIT):
                        l1.append(data1)  # 重合时暂存入L1，并跳出循环
                        break
                if data1 not in l1:
                    if self.X_cutting1(data1):
                        real_point_arr.append(data1)

            real_point_arr.extend(result3)#一次性添加多个值

        # print(" real_point_arr ",real_point_arr)
        if len(real_point_arr) == 0:
            return None
        else:
            num_pointk = 0
            for kj in range(len(real_point_arr)):
                num_pointk += len(real_point_arr[kj])
            if num_pointk == 0:
                return None
        # sorted(real_point_arr,key=attrgetter("worldY") )
        new_s = sorted(real_point_arr, key=lambda e: e.__getitem__('worldY'))#按Y排序
        # print(" after sort real_point_arr ",new_s)
        return new_s

    '''同步拍照时，各相机之间去重'''
    def checkPoint(self, pointOne, pointTwo, limit):  # （消费者调用，内部）
        return (abs(pointOne.get("worldX") - pointTwo.get("worldX")) < limit + 55) and (
                    abs(pointOne.get("worldY") - pointTwo.get("worldY")) < limit)

    '''针对于抓手和传送带的X值的限制'''
    def X_cutting1(self,data1):#基于设备的参数限制
        x1a =float(data1.get("worldX"))
        print('此时X的值为:{}'.format(x1a))
        # if x1a < 223 or x1a > 2003: #(395 + 20),,,(0+395+1820-15)
        if x1a < 363 or x1a > 1863:
            # print('------------X超限位，{}'.format(x1a))
            return False
        else:
            return True

    '''传送带速度转换'''
    #2020.10.31 1hz = 6.53mm/s,PLC的值1005，是10.05hz
    def transform_conveyer_speed(self,hz_speed):
        return round(hz_speed*0.0653,3)

    '''时间转毫秒'''
    def time2long(self,sec,mill_sec):
        return sec * 1000 + mill_sec

    '''毫秒转时间'''
    def long2time(self,num):
        sec = num // 1000
        mill_sec = num % 1000
        return sec,mill_sec


# ####---------------暂不使用-------------

    '''未使用'''
    def read_tongs_speed(self):#（未使用）
        self.lock.acquire()
        try:
            speed = self._melsec_ctrl.read_dword_data(aiCottonConfig.MELSEC_CODE.TONGS_X_SPEED1, 1)
            if speed is not None:
                return speed[0]
            return 0
        finally:
            self.lock.release()

    '''测试拍照'''
    def test_camera1(self):
        for i in range(20):
            self.takePhoto()
            time.sleep(0.3)
        time.sleep(3)
        pass

    '''关闭相机'''
    def closeCamera(self):
        """ 
        关闭相机  
        """
        if aiCottonConfig.CAMERA_ON:
            if self.cameraCtrlList is not None:
                for oCtrl in self.cameraCtrlList:
                    oCtrl.close_device()
                    del oCtrl

    '''陈红测试用'''
    def detect_background_test(self):

        def show_img(img, wd_name="", zoom=0.5):
            H, W = img.shape[0], img.shape[1]
            if zoom:
                img = cv2.resize(img, (int(zoom * W), int(zoom * H)), interpolation=cv2.INTER_CUBIC)
            cv2.imshow(wd_name, img)
        while True:
            image_path = self.generate_path()
            # 拍照
            print("start take photo")
            self._count_down_latch = count_down_latch(len(aiCottonConfig.CAMERA_DEVICE_TUPLE))
            bResult = self.take_photo(image_path)
            print(" bResult = ", bResult)
            # 获取图片超时
            if not bResult:
                print("take photo timeout!")
                continue
            # reset gpio value
            print("end take photo")
            img_ori_one = image_path.get(aiCottonConfig.CAMERA_DEVICE_TUPLE[0])
            img_ori_two = image_path.get(aiCottonConfig.CAMERA_DEVICE_TUPLE[2])
            img_ori_three = image_path.get(aiCottonConfig.CAMERA_DEVICE_TUPLE[1])
            start_time = time.time()
            show_image = detect_background(img_ori_one,img_ori_two,img_ori_three)
            end_time = time.time()
            print("all time is:%f"%(end_time - start_time))
            cv2.imwrite("./test.jpg", show_image)
            show_img(show_image, "delete_region", zoom=0.2)
            cv2.waitKey(1000)
            # time.sleep(5)

    '''读取编码器，换算传送带速度'''
    def read_speed23(self):
        oDevice = ai_encoder_device()  #
        oSerialList = oDevice.list_serial_port()  # 遍历列表
        print("found serial port：")
        for oInfo in oSerialList:
            print("name: %s, device: %s, description: %s" % (oInfo.name, oInfo.device, oInfo.description))
        bResult = oDevice.open("/dev/ttyUSB0")
        print("oDevice.open: ", bResult)
        if not bResult:
            return
        try:
            # 先读取参数
            strAddress, strParams = oDevice.read_params()
            if strAddress is None:
                print("oDevice.read_params()失败")
                return
            # end if
            print("oDevice.read_params: addr = %s" % strAddress)
            # 打印参数描述
            print("oDevice.read_params: params = %s" % ai_encoder_device.param_desc(strParams))

            # 设置为被动模式
            if oDevice.set_passive_mode(strAddress):
                print("oDevice.set_passive_mode OK")
            else:
                print("oDevice.set_passive_mode FAILED")
            # end if

            # 设置地址
            if oDevice.set_address(strAddress, 78):
                print("oDevice.set_address to 78 OK")
                # 测试读取数据
                iData = oDevice.read_data(78)
                print("oDevice.read_data(from 78) = %s" % iData)

                if oDevice.set_address(78, strAddress):
                    print("oDevice.set_address 78 to default OK")
                else:
                    print("oDevice.set_address FAILED")
                # end if
            else:
                print("oDevice.set_address FAILED")
            # end if

            # 测试读取数据
            # for i in range(100):
            speed_ori1 = 0
            while True:

                iData1 = oDevice.read_data(strAddress)
                timeb1 = time.time()
                time.sleep(2)#逻辑不严谨（与生产者，消费者）
                iData2 = oDevice.read_data(strAddress)
                timeb2 = time.time()
                ts1 = timeb2 - timeb1
                L_pt1 = iData2 - iData1 #编码器绝对值之差
                if L_pt1 < 0:#跳0时的处理
                    L_pt1 += 1000000
                L_pt2 = L_pt1/1000#计算圈数
                # speeda1 = L_pt2/ts1*250#每圈代表的长度
                # speeda1 = L_pt1/ts1 * 250  # 每个分辨率代表的长度
                speeda1 = L_pt1 / ts1 /self.speed2_K # 每个分辨率代表的长度（mm/s）
                if speeda1 > 5 and speeda1 < 300:
                    if abs(speeda1-speed_ori1) <5:#速度相差小于3mm/s，等效于传送带正常
                        self.speed2 = speeda1#92.95
                        # print('现在的传送带速度为：{}'.format(self.speed2))
                    else:
                        self.speed2 = speeda1  # 92.95
                        print('传送带处于加速期，速度差为：{}mm/s'.format( abs(speeda1-speed_ori1)))
                else:
                    self.speed2 = speeda1  # 92.95
                    print("编码器读取有误，该值为：{}".format(speeda1))
                speed_ori1 = copy.deepcopy(speeda1)
        finally:
            oDevice.close()
            del oDevice

# ####---------------程序初始化-------------

    '''程序开始'''
    def start(self):
        # 开机程序自检，PLC的读取，发送，相机触发拍照，返回，AI的返回
        self.frist_check()
        # 提交线程，运行（从PLC取数据，触发拍照，调用AI，换算坐标，去重，放到队列）
        self.__oPoolForRaster.submit(self.run_produce_point_data)
        self.__oPoolForRaster.submit(self.run_consume_point_record)
        # self.__oPoolForRaster.submit(self.read_speed23)

    '''初始化时-设置相机参数'''
    def set_camera_param(self,oCtrl,sn):#实例及标号#（初始化调用）
        if sn == aiCottonConfig.CAMERA_DEVICE_TUPLE[0]:
            oParam = aiCottonConfig.A_CAMERA_PARAMETER  # 相机参数
        elif sn == aiCottonConfig.CAMERA_DEVICE_TUPLE[1]:
            oParam = aiCottonConfig.C_CAMERA_PARAMETER  # 相机参数
        else:
            oParam = aiCottonConfig.B_CAMERA_PARAMETER  # 相机参数

        # oParam = aiCottonConfig.CAMERA_PARAMETER#相机参数

        for strName in oParam:
            strValue = oCtrl.get_property(strName)
            print("strName ---",strName,"  strValue ----",strValue)

            if strValue is not None:
                # 这个相机参数存在
                # if (strName == "Exposure" and sn == "35024012"):
                #     oCtrl.set_property(strName, 3800)
                #     continue
                print(" oParam[strName] -----",oParam[strName])
                oCtrl.set_property(strName, oParam[strName])

    '''初始化相机'''
    def initCamera(self):
        """
        初始化相机参数，启动相机捕捉画面
        :return 是否全部初始化成功
        """
        print("初始化相机")
        sys.stdout.flush()
        isAllCameraInited = True
        cameraCtrlList = []
        for deviceItem in aiCottonConfig.CAMERA_DEVICE_TUPLE:#相机设备元组
            if aiCottonConfig.CAMERA_ON:
                oCtrl = tiscamera_ctrl(aiCottonConfig.CAMERA_CTRL_WIDTH, aiCottonConfig.CAMERA_CTRL_HEIGHT)#某个相机实例
                bResult = oCtrl.open_device(deviceItem, self)#打开相机设备，调用函数，返回False
                if bResult:
                    bResult = oCtrl.start_capture()#开始拍摄，准备好就返回true
                    if not bResult:
                        isAllCameraInited = False
                        break
                else:
                    isAllCameraInited = False
                    break
                self.set_camera_param(oCtrl,deviceItem)#设置某个相机（实例及标号）#刷入相机取像参数
                cameraCtrlList.append(oCtrl)#都添加到相机列表
        # end for
        self.cameraCtrlList = cameraCtrlList

        return isAllCameraInited#相机已经准备好

    '''连接PLC的IP及端口，初始化相机'''
    def init_service(self):
        # modbus的IP和端口
        bool_plc1 = True
        num_plc1 = 0
        while bool_plc1:
            bResult = self._melsec_ctrl.open((aiCottonConfig.MELSEC_SERVER_IP, aiCottonConfig.MELSEC_SERVER_PORT))
            if not bResult:
                print("打开设备连接失败")
                num_plc1 += 1
                time.sleep(2)
                if num_plc1 > 300:
                    sys.exit(1)
                    return
            else:
                bool_plc1 = False
        print("PLC is ok")
        sys.stdout.flush()
        service.initCamera()

    def test_init_service(self):
        # modbus的IP和端口
        bool_plc1 = True
        num_plc1 = 0
        while bool_plc1:
            bResult = self._melsec_ctrl.open((aiCottonConfig.MELSEC_SERVER_IP, aiCottonConfig.MELSEC_SERVER_PORT))
            if not bResult:
                print("打开设备连接失败")
                num_plc1 += 1
                time.sleep(2)
                if num_plc1 > 300:
                    sys.exit(1)
                    return
            else:
                bool_plc1 = False
        print("PLC is ok")
        # service.initCamera()

    def test_initCamera(self):
        """
        初始化相机参数，启动相机捕捉画面
        :return 是否全部初始化成功
        """
        isAllCameraInited = True
        cameraCtrlList = []
        for deviceItem in aiCottonConfig.CAMERA_DEVICE_TUPLE:#相机设备元组
            if aiCottonConfig.CAMERA_ON:
                oCtrl = tiscamera_ctrl(aiCottonConfig.CAMERA_CTRL_WIDTH, aiCottonConfig.CAMERA_CTRL_HEIGHT)#某个相机实例
                bResult = oCtrl.open_device(deviceItem, self)#打开相机设备，调用函数，返回False
                if bResult:
                    bResult = oCtrl.start_capture()#开始拍摄，准备好就返回true
                    if not bResult:
                        isAllCameraInited = False
                        break
                else:
                    isAllCameraInited = False
                    break
                self.set_camera_param(oCtrl,deviceItem)#设置某个相机（实例及标号）#刷入相机取像参数
                cameraCtrlList.append(oCtrl)#都添加到相机列表
        # end for
        self.cameraCtrlList = cameraCtrlList

        return isAllCameraInited#相机已经准备好

    def test_runPLC(self):
        try:
            for ju in range(1,10):
                print("---------------------------------------")
                print("第{}次读取时间".format(ju))
                data = self.read_data(0)
                print('data',data)
                start_time = self.time2long(data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC),
                                            data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC))
                print("时间戳是：{}".format(start_time))
                end_time = 3500 + start_time  # 下抓时间
                end_time2 = 4500 + start_time  # 下抓时间
                print("发送时间戳是：{}".format(end_time))
                sec, mill_sec = self.long2time(end_time)  # 毫秒转时间
                sec2, mill_sec2 = self.long2time(end_time2)  # 毫秒转时间
                x = 2000 - ju*180
                print("发送数据为：{} - {} ，@{}".format(sec, mill_sec, x))
                # print("2-----start_time ----", start_time)
                # print("2-----end_time ----", end_time)
                # print("2-----sec ----", sec)
                # print("2-----mill_sec ----", mill_sec)
                # print("2-----x ------", x)
                self.write_data(int(sec), int(mill_sec), int(x - 30), 0, 0, 1)
                time.sleep(1)
                self.write_data(int(sec2), int(mill_sec2), int(x + 30), 0, 0, 2)
                time.sleep(7)
        except Exception as e:
            print(f"err---frist_check: {e}")

    def test_readPLC(self):
        try:
            print("----------开始自检----------")

            '''PLC的读写'''
            test_a = 1
            if test_a == 1:
                print("读取传送带速度")
                namesp = aiCottonConfig.MELSEC_CODE.CSD_SPEED1
                resultsp = self._melsec_ctrl.read_dword_data(namesp, 1)  # 读取
                if resultsp is not None:
                    print("读取PLC 成功")
                    print("参数值：{}".format(resultsp))#返回值是resultsp = [1000]
                else:
                    print("无法读取PLC")
            time.sleep(100)
            print("-----PLC部分自检")
            name1 = aiCottonConfig.MELSEC_CODE.ZI_TEST1
            data = [123, 456, 789, 1024]
            name2 = aiCottonConfig.MELSEC_CODE.ZJ_XINHAO
            data2 = [77]
            result1 = self._melsec_ctrl.write_dword_data(name1, data)  # 写入
            print('result1',result1)
            if result1 is not None:
                if result1:
                    print("数据写入PLC 成功")
                else:
                    print("数据写入PLC 失败")
                time.sleep(0.3)
                result2 = self._melsec_ctrl.read_dword_data(name1, 4)  # 读取
                if result2 is not None:
                    print("读取PLC 成功")
                    print("PLC起始地址：{}，数据为{}".format(name1, result2))
                    time.sleep(0.3)
                    data = [222, 222, 222, 222]
                    result1 = self._melsec_ctrl.write_dword_data(name1, data)  # 写入重置
                    result3 = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入重置自检信号位
                else:
                    print("无法读取PLC")
            else:
                print("数据未能写入PLC，请检查原因（IP，端口，集线器模式）")

        except Exception as e:
            print(f"err---frist_check: {e}")


    def test_takepic(self):
        try:
            print("----------开始自检----------")

            '''PLC的读写'''


            '''相机模块自检'''
            print("-----等待相机模块加载完成")
            time.sleep(2)
            print("-----Camera部分自检")
            for jn in range(1,40000):
                # time.sleep(1)
                print("第{}次拍照".format(jn))
                image_path = self.generate_path(str(jn))  # 返回图片存放路径，组
                self._count_down_latch = count_down_latch(len(aiCottonConfig.CAMERA_DEVICE_TUPLE))
                bResult = self.take_photo(image_path)
                if not bResult:
                    print("相机拍照超时，take photo timeout!")
                    print("请检查相机ID  触发参数")
                    # data2 = [11]
                    # result3 = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入自检信号位
                else:
                    time.sleep(1.2)
                    '''AI模块自检————调用ai识别'''
                    # print("-----AI服务部分自检")
                    # ai_result = {}
                    # ai_status = True
                    # for key in self.cameraCtrlListDic:
                    #     position = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[key]  # 相机对应的位置
                    #     res = self.call_ai_service(self.cameraCtrlListDic[key])  # 调用ai服务，#返回字符串
                    #     if res is None:
                    #         ai_status = False
                    #         break
                    #     ai_result[position] = self.processAiData(res.get("data").get("0"), position)
                    #     # 返回像素点坐标，相机位置，世界坐标的字典 的列表
                    # if not ai_status:
                    #     print('AI 返回为None，AI服务出错')
                    #     # data2 = [22]
                    #     # result3 = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入自检信号位
                    # else:
                    #     print("ai_result ----", ai_result)
                    #     # data2 = [88]
                    #     # result3 = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入自检信号位
                    #     print("----------完成自检----------")
        except Exception as e:
            print(f"err---frist_check: {e}")



    def test_print(self):
        for i in range(100):
            print("测试，第{}次---".format(i+1))
            time.sleep(2)

# SIGINT信号处理
def sigint_handler(signum, frame):
    GPIO.cleanup()
    sys.exit(0)

if __name__ == '__main__':
    # 设置信号处理
    run_or_test1 = 11 #1：正常运行，非1：测试
    signal.signal(signal.SIGINT, sigint_handler)#中断进程
    signal.signal(signal.SIGTERM, sigint_handler)#软件终止信号
    if run_or_test1 == 1:
        service = AiHjRunService()
        service.init_service()#调用函数（初始化modbus,及相机）
        service.start()
    else:
        service = AiHjRunService()
        PLC_or_camare1 = 33 #22：PLC  33：Camera 44:一起初始化
        if PLC_or_camare1 == 22:
            service.test_init_service()
            test_b = 1  # 1：读取PLC测试
            if test_b == 11:
                service.test_readPLC()
            else:
                service.test_runPLC()
        elif PLC_or_camare1 == 33:
            service.test_initCamera()
            test_a = 1 # 1：拍照测试
            if test_a == 1:
                service.test_takepic()
        elif PLC_or_camare1 == 44:
            service.test_init_service()
            service.test_initCamera()
        else:
            service.test_print()
