# coding=utf-8
import sys
import time
import os
import signal
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.dummy import Pool as processPool
import copy
import queue
import threading
import requests
import logging.config
import cv2
import json
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!This is probably because you need superuser privileges.")
from count_down_latch import count_down_latch
from image2world import image_points_to_world_plane
from utils import transform_conveyer_speed, time2long, long2time, find_grey_value, caculate_nearly_point
from utils import write_mysql, write_mysql2, write_mysql3, write_mysql4, write_mysql5, write_mysql6, call_ai_service
import config_armz as aiCottonConfig
from point_deal_record import point_record


# 添加包路径
START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, "..", "..", "ai-melsec-ctrl", "python"))
sys.path.append(os.path.join(START_PY_PATH, "..", "..", "ai-device-ctrl", "python"))
sys.path.append(os.path.join(START_PY_PATH, "..", ".."))
# sys.path.append(os.path.join(START_PY_PATH, "..", "call_code"))
del START_PY_PATH
# 需要导入的类
# from aimodel.config import *
# from aimodel.cameraModel import *
# from aimodel.aiModel import *
# from aimodel.tritonserver import *

from AIDeviceCtrl.tiscamera_ctrl import tiscamera_ctrl
from melsec_ctrl.melsec_ctrl import melsec_ctrl
from base import log
from base.timer_thread import simple_task_thread


logger = logging.getLogger('main')
logger2 = logging.getLogger('remover')
logger4 = logging.getLogger('recorder')
logger5 = logging.getLogger('rtemp')
logger6 = logging.getLogger('sql')
logger7 = logging.getLogger('needrecoed')
log.init_log("save_db")
log.info("===================================")


'''
2021-06-04---调用AI服务拍照+4抓手改造
2021-0702---调用AI、拍照类
2021-07-30 --再增加老式的拍照调用模式
'''


class AiHjRunService:
    def __init__(self):

        self.bool_check_process_PLC = False  # 05-19 自检过程中，和PLC保持通讯
        self.bool_start_signal_PLC = False  # 05-19 向PLC写入开始信号(传送带转起来)
        self.bool_get_batch_PLC = False  # 05-19 获取批次号
        self.bool_get_speed_PLC = False  # 05-19 获取传送带速度
        self.bool_get_label_PLC = False  # 05-19 获取识别种类
        self.bool_circulation_process_PLC = False  # 05-20 循环过程中，和PLC保持通讯
        self.bool_circulation_qp_PLC = False  # 05-20 循环过程中，和PLC保持通讯
        self.bool_read_claw_state = False  # 06-08 读取抓手状态
        self.num_claw_state = 2  # 06-08 默认为2抓手数量
        # self.list_claw_state = [[1, 1], [1, 1], [1, 1], [1, 1]]  # 06-08 抓手状态列表，默认为1
        self.list_claw_state = [1, 1, 1, 1, 1, 1, 1, 1]  # 06-08 抓手状态列表，默认为空
        self.bool_read_plc_time_1 = False  # 06-08 读取PLC时间戳
        self.bool_read_plc_time_2 = False  # 06-08 读取PLC时间戳
        self.time_plc = None  # 06-08 PLC时间戳
        self.time_arm = None  # 06-08 读取PLC时刻的arm时间戳
        self.send_toPLC_list = []  # 06-08 发送PLC抓取时刻的信息表
        self.bool_send_toPLC_claw = False  # 06-08 发送PLC抓取时刻
        self.bool_claw_goback = False  # 06-08 发送PLC归零--信号
        self.num_plc_goback = 0  # 06-08 发送PLC归零--抓手编号1-4

        self.pq_list = [0] * 60  # 05-20 喷嘴号对应时常
        self.pqlist_queue = queue.Queue(maxsize=10)  # 05-21异纤优先队列
        self.photo_n = 0  # 05-21全局拍照计数
        self.bool_ctrl_stop = False  # 05-21PLC控制的暂停信号
        self.if_need_stop = 1 # 05-21PLC控制的暂停信号-值，初始为1，表示正常运行
        self.before_point_data = None  #  05-21 前后2帧的去重数据
        self.produce_point_is_OK = True  # 05-21 生产者确认上次循环中的数据已经处理好了，否则等待，不等待会数据覆盖
        self.bool_save_pic = True  # 05-30 多线程中保存图片完成信号
        self.bool_ai_infer = 0  # 05-30 多线程中AI识别完成信号
        self.ai_point_data = []  # ai点信息  # 04-19 并行调用AI
        # [触摸屏IP(需要通讯时),第1抓取模组,第2抓取模组  2021-06-05
        self.PLC_ctrl = [melsec_ctrl(), melsec_ctrl(), melsec_ctrl()]
        self.choose_mechine_model = 0
        # [0]:AI识别所有的点数量
        # [1]:符合选取类别的点数量
        # [2]:筛掉图片边缘+传送带边缘，后的点数量
        # [3]:同步去重后的点数量
        # [4]:异步去重后的点数量(存入队列的点数量)
        # [5]:所有抓手抓取的数量
        # [6]:被抓手放弃的点的数量
        # [7]:进入队列时，由于满队列，而被放弃的点  理论：[4] = [5] + [6] + [7] + [8]
        # [8]:清空队列时放弃的点的数量
        self.num_point = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # 点信息的统计 2021-06-23

        self.cameraModel = None  # 2021-06-18  全局变量--相机类
        self.detectionModel = None  # 2021-06-18  全局变量--AI类

        # 路径相关 2021-07-07
        self.havebox_path = None
        self.nobox_path = None
        self.upload_path = None
        self.date_path1 = time.strftime("%Y_%m_%d", time.localtime())
        self.save_pic_aipath = "/mnt/data/data/image_original/img_" + self.date_path1

        self.__oPoolForRaster1 = ThreadPoolExecutor(9, "PoolForRasters")  # 线程池 2021-07-06
        self.__oPoolForRaster2 = processPool(8)  # 进程池 2021-07-06

        self.lock = threading.RLock()#队列线程锁，读写互斥，仅能进行一项
        self.bool_lock_time = False  # 读取PLC时间优先级判断
        self.ai_point_record = point_record() #计数对象，引用

        # 2021-07-02--新建5*3个队列
        self.queue_first = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
        self.queue_second = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
        self.queue_third = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
        self.queue_fourth = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
        self.queue_fifth = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
        self.list_zh1 = {}  # 2021-07-02 重制限制类别列表

        self.sql_point_queue = queue.Queue(maxsize=30)  # 点数据的存放队列
        #相机引脚号
        self.__output_pin = 18
        #GPIO初始化
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.__output_pin, GPIO.OUT, initial=GPIO.LOW)
        # #输入高低电平
        self.__gpio_value = GPIO.LOW #未改

        self.speed2 = 200 #单位M/s(覆盖的参数是mm/s)
        self.dataZ1 =[]#去重数据组
        self.choose_model1 = 0 #默认异纤种类（#0,异纤  1，异纤+脏棉）
        self.num_changeda = 0
        self.bool_xfz = False
        self.num_err_record = 0 #异常记录通讯更新标记 12_16
        self.times_queue2 = 0
        # 若要处理一些定时任务，比如自动删除旧的数据，需要开启下面定时任务线程
        self.oTaskThread = simple_task_thread("simple_task")
        self.oTaskThread.start()
        self.batch_cotton = ""
        self.save_pic_name1 = [] # 存图的路径+名称

    # ----2021-07-30 --新增老式生产者调用所需参数---
        self.oCtrl1 = [None, None, None]
        # 拍照参数
        self.cameraCtrlList = {}  # 摄像机控制器列表
        self.cameraCtrlListDic = {}  # 全局相机拍照路径设置
        self.currentImgCount = 0  # 单次回调的照片数量
        self.Camera_MAP = aiCottonConfig.CAMERA_SAVE_IMAGE
        self.cam_num2 = [aiCottonConfig.CAMERA_DEVICE_TUPLE[0],
                         aiCottonConfig.CAMERA_DEVICE_TUPLE[1],
                         aiCottonConfig.CAMERA_DEVICE_TUPLE[2]]
        self.bool_camera_err = False
        self.num_camera_err = 0




    # ---------------初始化部分-------------
    '''--------2021-06-05 由配置选择要连接的PLC----------'''
    def connect_plc(self):  # 2021-06-05 由配置选择要连接的PLC

        plc_port = aiCottonConfig.PLC_port
        plc_ctrl_list = aiCottonConfig.PLC_ctrl_choose
        plc_ip_list = [aiCottonConfig.PLC_ip_main, aiCottonConfig.PLC_ip_frist, aiCottonConfig.PLC_ip_second]

        for plc_i in range(len(plc_ctrl_list)):
            if plc_ctrl_list[plc_i] == 1:
                bool_plc1 = True
                num_plc1 = 0
                while bool_plc1:
                    time.sleep(0.001)
                    bResult = self.PLC_ctrl[plc_i].open((plc_ip_list[plc_i], plc_port))
                    if not bResult:
                        logger7.info("与PLC设备:{}--连接失败".format(plc_i))
                        num_plc1 += 1
                        time.sleep(2)
                        if num_plc1 > 300:
                            logger7.info("长时间连接不上PLC设备:{}，退出程序".format(plc_i))
                            time.sleep(2)
                            os._exit(0)
                    else:
                        logger7.info("PLC--{} is ok, ".format(plc_i))
                        bool_plc1 = False
        logger7.info("connect PLC is ok, --ctrl-plc-list is :{}".format(plc_ctrl_list))

    '''--------2021-06-05 由配置选择要重连接的PLC----------'''
    def reconnect_plc(self):  # 2021-06-05 由配置选择要重连接的PLC
        plc_ctrl_list = aiCottonConfig.PLC_ctrl_choose
        for plc_i in range(len(plc_ctrl_list)):
            if plc_ctrl_list[plc_i] == 1:
                self.PLC_ctrl[plc_i].close()
        logger7.info("PLC--closed")
        time.sleep(2)
        logger7.info("PLC--restart")
        self.connect_plc()

    '''自检PLC连接'''
    def check_PLC(self):
        logger7.info("-----PLC部分自检")
        name1 = aiCottonConfig.MELSEC_CODE.ZI_TEST1
        data = [123, 456, 789, 1024]
        name2 = aiCottonConfig.MELSEC_CODE.ZJ_XINHAO
        data2 = [88]
        result1 = self.PLC_ctrl[1].write_dword_data(name1, data)  # 写入
        if result1 is not None:
            logger7.info("数据写入PLC 成功")
            time.sleep(0.3)
            result2 = self.PLC_ctrl[1].read_dword_data(name1, 4)  # 读取
            if result2 is not None:
                logger7.info("读取PLC 成功")
                logger7.info("PLC起始地址：{}，数据为{}".format(name1, result2))
                time.sleep(0.3)
                data = [222, 222, 222, 222]
                self.PLC_ctrl[1].write_dword_data(name1, data)  # 写入重置
                self.PLC_ctrl[1].write_dword_data(name2, data2)  # 写入重置自检信号位
                logger7.info("测试数据重置 成功")
            else:
                logger7.info("无法读取PLC")
        else:
            logger7.info("数据未能写入PLC，请检查原因（IP，端口，MC协议,是否断电重启后再连接）")
        pass

    '''开线程-PLC通信'''
    def connect_PLC_thread(self):
        th1_PLC = threading.Thread(target=self.keep_connection_to_PLC, args=(), name="keep_connection_to_PLC")
        th1_PLC.start()


    '''函数--与PLC通讯'''
    def keep_connection_to_PLC(self):
        # plc_can = list_plc1["plc_list"]
        print("---------进入PLC通讯线程--------")
        plc_ctrl_list = aiCottonConfig.PLC_ctrl_choose

        name1 = aiCottonConfig.MELSEC_CODE.ARM_XINHAO
        name2 = aiCottonConfig.MELSEC_CODE.START_OK
        name3 = aiCottonConfig.MELSEC_CODE.PENQI
        name4 = aiCottonConfig.MELSEC_CODE.CSD_SPEED1
        name5 = aiCottonConfig.MELSEC_CODE.CHOOSE_MODEL
        name6 = aiCottonConfig.MELSEC_CODE.STOP_ALL1

        name7 = aiCottonConfig.MELSEC_CODE.TONGS_STATUS1
        name8 = aiCottonConfig.MELSEC_CODE.TONGS_STATUS2
        name9 = aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC

        name10 = aiCottonConfig.MELSEC_CODE.GRAB_TIME_SEC1
        name11 = aiCottonConfig.MELSEC_CODE.GRAB_TIME_SEC2

        name12 = aiCottonConfig.MELSEC_CODE.TONGS_HOMING1
        name13 = aiCottonConfig.MELSEC_CODE.TONGS_HOMING2

        name14 = aiCottonConfig.MELSEC_CODE.ZJ_XINHAO

        bool_ctrl_print = False
        while True:
            try:
                t1 = time.time()

                '''老版本的程序异常通知信号'''
                if self.bool_camera_err:
                    self.bool_camera_err = False
                    # if self.num_camera_err == 11:
                    self.PLC_ctrl[1].write_dword_data(name14, [self.num_camera_err])  # 写入自检信号位

                '''命令PLC控制喷气'''
                if self.bool_circulation_qp_PLC:  # 循环时的通知PLC喷气
                    self.bool_circulation_qp_PLC = False
                    if not self.pqlist_queue.empty():
                        # if True:
                        send_data = self.pqlist_queue.get()
                        self.PLC_ctrl[1].write_word_data(name3, send_data[1])
                        print("消费者--penqi--to-PLC:time{}--{}".format(time.time(), send_data))

                '''读取抓手状态'''
                if self.bool_read_claw_state:
                    self.bool_read_claw_state = False
                    if self.num_claw_state == 2:
                        res1 = self.PLC_ctrl[1].read_bit_data(name7, 3)
                        res2 = self.PLC_ctrl[1].read_bit_data(name8, 3)
                        # print("res1:{}   res2:{}".format(res1, res2))
                        self.list_claw_state = [res1[0], res1[2], res2[0], res2[2],
                                                1, 1, 1, 1]
                    elif self.num_claw_state == 4:
                        # print("----@@@@@@@@消费者---读取抓手状态  时间戳   ：{}".format(time.time()))
                        res1 = self.PLC_ctrl[1].read_bit_data(name7, 3)
                        res2 = self.PLC_ctrl[1].read_bit_data(name8, 3)
                        res3 = self.PLC_ctrl[2].read_bit_data(name7, 3)
                        res4 = self.PLC_ctrl[2].read_bit_data(name8, 3)
                        self.list_claw_state = [res1[0], res1[2], res2[0], res2[2],
                                                res3[0], res3[2], res4[0], res4[2]]
                '''读取PLC时间戳'''
                if self.bool_read_plc_time_1:
                    # print("----@@@@@@@@消费者---获取PLC时间戳(前)   ：{}".format(time.time()))
                    result = self.PLC_ctrl[1].read_dword_data(name9, 2)
                    # print("----@@@@@@@@消费者---获取PLC时间戳(中)   ：{}".format(time.time()))
                    self.time_arm = time.time()
                    self.time_plc = time2long(result[0], result[1])
                    self.bool_read_plc_time_1 = False  # 同样也是调用处标记
                    # print("plc_time:{}".format(result))
                    # print("plc_time:{}--{}".format(result[0], result[1]))
                    # print("----@@@@@@@@消费者---获取PLC时间戳(后)   ：{}".format(time.time()))

                if self.bool_read_plc_time_2:
                    # print("----@@@@@@@@消费者---获取PLC时间戳(2前)   ：{}".format(time.time()))
                    result = self.PLC_ctrl[2].read_dword_data(name9, 2)
                    # print("----@@@@@@@@消费者---获取PLC时间戳(2中)   ：{}".format(time.time()))
                    self.time_arm = time.time()
                    self.time_plc = time2long(result[0], result[1])
                    self.bool_read_plc_time_2 = False  # 同样也是调用处标记
                    # print("----@@@@@@@@消费者---获取PLC时间戳(2后)   ：{}".format(time.time()))
                '''写入PLC-抓取时刻'''
                if self.bool_send_toPLC_claw:

                    if self.send_toPLC_list[0] == 1:
                        # print("----@@@@@@@@消费者---抓手1---写入PLC时间戳：{}---#################".format(time.time()))
                        self.PLC_ctrl[1].write_dword_data(name10, self.send_toPLC_list[1:])
                    elif self.send_toPLC_list[0] == 2:
                        self.PLC_ctrl[1].write_dword_data(name11, self.send_toPLC_list[1:])
                    elif self.send_toPLC_list[0] == 3:
                        # print("----@@@@@@@@消费者---抓手3---写入PLC时间戳：{}---#################".format(time.time()))
                        self.PLC_ctrl[2].write_dword_data(name10, self.send_toPLC_list[1:])
                    elif self.send_toPLC_list[0] == 4:
                        self.PLC_ctrl[2].write_dword_data(name11, self.send_toPLC_list[1:])
                    self.bool_send_toPLC_claw = False
                    bool_ctrl_print = True
                '''抓手归零-重建OP信号'''
                if self.bool_claw_goback:
                    self.bool_claw_goback = False
                    if self.num_plc_goback == 1:
                        self.PLC_ctrl[1].write_bit_data(name12, [1])
                    elif self.num_plc_goback == 2:
                        self.PLC_ctrl[1].write_bit_data(name13, [1])
                    elif self.num_plc_goback == 3:
                        self.PLC_ctrl[2].write_bit_data(name12, [1])
                    elif self.num_plc_goback == 4:
                        self.PLC_ctrl[2].write_bit_data(name13, [1])

                '''循环时的PLC--心跳'''
                if self.bool_circulation_process_PLC:  # 循环时的PLC断连信号
                    data2 = [self.num_changed1()]
                    self.PLC_ctrl[1].write_word_data(name1, data2)  # 写入自检信号位-断连状态
                    self.bool_circulation_process_PLC = False
                '''向PLC写入开始信号'''
                if self.bool_start_signal_PLC:  # 05-19 向PLC写入开始信号(传送带转起来)
                    for plc_i in range(len(plc_ctrl_list)):
                        if plc_ctrl_list[plc_i] == 1:
                            self.PLC_ctrl[plc_i].write_bit_data(name2, [1])
                    self.bool_start_signal_PLC = False
                '''接受PLC 发送的暂停指令'''
                if self.bool_ctrl_stop:
                    # print("----@@@@@@@@消费者--暂停指令---时间戳：{}".format(time.time()))
                    self.if_need_stop = self.PLC_ctrl[1].read_bit_data(name6, 1)[0]  # PLC 发送的暂停指令
                    self.bool_ctrl_stop = False
                '''获取传送带速度'''
                if self.bool_get_speed_PLC:  # 05-19 获取传送带速度
                    cds_speed = self.PLC_ctrl[aiCottonConfig.Need_time_PLC].read_dword_data(name4, 1)[0]  # 根据设备情况，指定PLC

                    self.speed2 = transform_conveyer_speed(cds_speed)  # 写入速度
                    self.speed2 = 170.66  # 写入速度--对应传送带频率2300*0.0742
                    print("----@@@@第{}次拍照时，传送带速度{}--频率：{}".format(self.photo_n, self.speed2, cds_speed))
                    # self.speed2 = 1179.57
                    # self.speed2 = 500
                    # print("检测到现在传送带速度为：{} mm/s".format(self.speed2))
                    self.bool_get_speed_PLC = False
                if not self.bool_xfz:
                    '''获取批次号'''
                    if self.bool_get_batch_PLC:  # 05-19 获取批次号 用的self.PLC_ctrl[1]
                        self.get_batch(False)
                        self.bool_get_batch_PLC = False

                    '''取识别种类'''
                    if self.bool_get_label_PLC:  # 05-19 获取识别种类
                        bReadData = self.PLC_ctrl[1].read_word_data(name5, 1)
                        self.choose_model1 = bReadData[0]
                        self.choose_model1 = 3
                        print("读取异纤识别种类:{}".format(self.choose_model1))
                        self.bool_get_label_PLC = False
                    '''自检--心跳'''
                    if self.bool_check_process_PLC:  # 05-19 自检过程中，和PLC保持通讯
                        data2 = [self.num_changed1()]
                        # logger.info("自增数：{}".format(str(data2[0])))
                        print("name:{},data:{}".format(name1, data2))
                        self.PLC_ctrl[1].write_word_data(name1, data2)  # 写入自检信号位-断连状态
                        time.sleep(0.5)
                if bool_ctrl_print:
                    bool_ctrl_print = False
                    print("第{}次拍照期间，线程循环时间：{}".format(self.photo_n, time.time() - t1))
                time.sleep(0.001)
            except Exception as e:
                logger.error(f"keep_connection_to_PLC  err: {e}")
                logger.info("由于与 PLC通讯问题，退出程序")
                time.sleep(0.1)
                os._exit(0)  # PLC 写入不成功，则关闭程序

    # ---------------自检部分-------------
    '''自检总览'''
    def frist_check_AI(self):
        print("进入自检")
        logger7.info("进入自检")

        if aiCottonConfig.If_need_PLC:
            self.check_PLC()  # 自检PLC连接
            self.bool_check_process_PLC = True  # 开始和PLC通讯连接信号  --不会停止
            self.connect_PLC_thread()  # 开线程-发送PLC连接通断信号
        # print("开线程-写入点位表")
        # self.use_thread_sql1()  # 开线程-写入点位表

        # self.ai_server_start_v2()  # AI部分服务启动(模型和相机)
        # 老版本
        self.initCamera()

        self.create_file_path1()  # 创建文件路径，每日刷新，检查本地与网络时间
        # self.check_takepic_AI_v2()  # 自检拍照和AI识别
        # 老版本
        self.check_takepic_ai_old()

        if aiCottonConfig.If_need_PLC:
            self.bool_start_signal_PLC = True  # 05-19 向PLC写入开始信号(传送带转起来)
            self.bool_get_batch_PLC = True  # 05-19 获取批次号
            self.bool_get_label_PLC = True  # 05-19 获取识别种类
            self.bool_ctrl_stop = True  # 05-21 看是否需要暂停
            for f_i in range(3):
                time.sleep(1.5)
                self.bool_get_speed_PLC = True  # 05-19 获取传送带速度
        self.read_limit_label(self.choose_model1)
        print("自检完成")
        logger7.info("自检完成")

    '''AI部分服务启动(模型和相机)'''
    def ai_server_start_v2(self):
        num_camera_init = 0

        # 模型初始化
        model_path1 = aiCottonConfig.AI_model_cfg_path  # 加载配置文件路径
        model_config = load_config(model_path1)  # 加载模型路径
        # print("模型参数：{}".format(model_config))
        t0 = time.time()
        tritonserverModel = tritonserver(model_config)  # tritonserver init
        tritonserverModel.kill_tritonserver()  # 杀掉可能已经启动的tritonserver模块
        connect_flag = tritonserverModel.start_tritonserver()  # 启动算法服务模块
        if connect_flag:
            print("Triton_server is ready")
            logger7.info("Triton_server is ready")
        else:
            print("aimodelInit error Triton_server is not ready")
            logger7.info("aimodelInit error Triton_server is not ready")
            sys.exit(0)

        # 检测模型初始化
        try:
            if model_config["detectionNmae"] == "YOLO3":
                self.detectionModel = model_detection_core(model_config)
            elif model_config["detectionNmae"] == "ATSS":
                self.detectionModel = model_atss_detection(model_config)
                print("模型初始化  OK, 用时：{}".format(round(time.time() - t0, 4)))
                logger7.info("模型初始化  OK, 用时：{}".format(round(time.time() - t0, 4)))
            else:
                print("请检查模型配置.json文件, 缺失：detectionNmae")
                logger7.info("请检查模型配置.json文件, 缺失：detectionNmae")
                sys.exit(0)

            # 相机初始化
            t1 = time.time()
            self.cameraModel = camera_model(model_config)
            result_camera = self.cameraModel.cameraInit()
            print("相机初始化返回:{}".format(result_camera))
            logger7.info("相机初始化返回:{}".format(result_camera))
            if result_camera is None:
                num_camera_init += 1
                print("相机初始化--调用服务--失败")
                logger7.info("相机初始化--调用服务--失败")
                time.sleep(1)
            else:
                if int(result_camera.get("return_code")) != 0:
                    num_camera_init += 1
                    print("相机初始化--调用服务--服务内部--失败")
                    logger7.info("相机初始化--调用服务--服务内部--失败")
                    time.sleep(1)
                else:
                    print("初始化相机用时：{}s".format(round(time.time() - t1, 3)))
                    logger7.info("初始化相机用时：{}s".format(round(time.time() - t1, 3)))
            if num_camera_init > 0:
                print("相机初始化--失败 --退出程序")
                logger7.info("相机初始化--失败 --退出程序")
                os._exit(0)

        except Exception as e:
            logger7.error(f"init -error: {e}")
            time.sleep(0.25)

    '''自检拍照和AI识别'''
    def check_takepic_AI_v2(self):

        t2 = time.time()
        bool_take_pic = True  # 拍照结果--信号，False:可以进行存图、aiInfer
        self.bool_ai_infer += 11
        for i in range(2):
            # 等待一段时间(拍摄周期)
            t1 = time.time()  # 上一次循环结束的时间戳
            l_t1 = round((1 - (t1 - t2)), 3)
            if l_t1 > 0:
                time.sleep(l_t1)
            logger.info("自检-第{}次循环开始".format(str(i + 1)))

            t2 = time.time()
            # 调用拍照
            result_takepic = self.cameraModel.takePic()
            # result_takepic = self.__oPoolForRaster.map(self.take_pic_func1, [i])[0]
            print("[自检]拍照返回：{} -- 用时：{}".format(result_takepic, round(time.time() - t2, 4)))
            logger7.info("[自检]拍照返回：{} -- 用时：{}".format(result_takepic, round(time.time() - t2, 4)))
            if len(result_takepic) == len(aiCottonConfig.Camera_id):
                bool_take_pic = False
                print("[自检]第{}次到拍照结束用时：{}s".format(str(i + 1), round(time.time() - t2, 4)))
                logger7.info("[自检]第{}次到拍照结束用时：{}s".format(str(i + 1), round(time.time() - t2, 4)))
            else:
                print("相机拍照--失败 --退出程序")
                logger7.info("相机拍照--失败 --退出程序")
                os._exit(0)
            # 调用AI
            t1 = time.time()
            if not bool_take_pic:  # 拍照成功
                print("开启存图线程")
                logger7.info("开启存图线程")
                # self.call_ai_savepic_v2(i, t1)
                # list_save_pic1 = [{"tp_num": i, "tp_end_time": t1}]
                # self.__oPoolForRaster.map(self.call_ai_savepic_service_v2, list_save_pic1)
                list_save_pic1 = {"tp_num": i, "tp_end_time": t1}
                self.__oPoolForRaster1.submit(self.call_ai_savepic_service_v2, list_save_pic1)
                print("开启AIinfer线程")
                logger7.info("开启AIinfer线程")
                # self.call_ai_trigger_data1_v2(i, t1, 0, 1, result_takepic) #现在强制为True
                self.__oPoolForRaster1.submit(self.call_ai_trigger_data1_v2, i, t1, 0, 1, result_takepic)

    '''创建文件路径，每日刷新'''
    def create_file_path1(self):
        # date_today = self.check_date_time()  # 检查本地时间和网络时间
        date_today = None  # 检查本地时间和网络时间
        if date_today is not None:
            self.save_pic_aipath = "/mnt/data/data/image_original/img_" + date_today
            date_path1 = date_today
        else:
            date_path1 = time.strftime("%Y_%m%d", time.localtime())

        date_path2 = aiCottonConfig.Path_upload + date_path1
        if not os.path.exists("/mnt/data/data/image_original/"):
            os.makedirs("/mnt/data/data/image_original/")
        if not os.path.exists("/mnt/data/data/image/"):
            os.makedirs("/mnt/data/data/image/")
        if not os.path.exists("/mnt/data/data/image/havebox/"):
            os.makedirs("/mnt/data/data/image/havebox/")
        if not os.path.exists("/mnt/data/data/image/nobox/"):
            os.makedirs("/mnt/data/data/image/nobox/")
        if not os.path.exists("/mnt/data/data/upload_image/"):
            os.makedirs("/mnt/data/data/upload_image/")
        self.havebox_path = "/mnt/data/data/image/havebox/" + date_path2
        self.nobox_path = "/mnt/data/data/image/nobox/" + date_path2
        self.upload_path = "/mnt/data/data/upload_image/" + date_path2
        if not os.path.exists(self.nobox_path):
            os.makedirs(self.nobox_path)
        if not os.path.exists(self.havebox_path):
            os.makedirs(self.havebox_path)
        if not os.path.exists(self.upload_path):
            os.makedirs(self.upload_path)
        if not os.path.exists(self.save_pic_aipath):  # 图片原始路径
            os.makedirs(self.save_pic_aipath)
        logger7.info("self.save_pic_aipath：{}".format(self.save_pic_aipath))
        logger7.info("self.nobox_path：{}".format(self.nobox_path))
        logger7.info("self.havebox_path：{}".format(self.havebox_path))
        logger7.info("self.upload_path：{}".format(self.upload_path))

    '''
        不能联网时，返回None，
        不一致，输出网络日期，
        一致，输出本地日期
        '''
    '''2021-07-07  检查本机系统时间和网络时间'''
    def check_date_time(self):
        list_num1 = [0, True, 0, True]  # internet循环 计数，信号  check_time循环 计数，信号
        beijinTime = None
        now_date = None
        while list_num1[1]:
            time.sleep(0.001)
            if list_num1[0] >= 60:
                logger7.info("获取网络时间失败")
                list_num1[1] = False
                list_num1[3] = False
                continue
            list_num1[0] += 1
            try:
                hea = {'User-Agent': 'Mozilla/5.0'}  # 设置头信息，没有访问会错误400！！！
                url = r'http://time1909.beijing-time.org/time.asp'  # 设置访问地址，我们分析到的
                r = requests.get(url=url, headers=hea, timeout=2)  # 用requests get这个地址，带头信息的
                if r.status_code == 200:  # 检查返回的通讯代码，200是正确返回
                    result = r.text  # 定义result变量存放返回的信息源码
                    data = result.split(";")  # 通过;分割文本
                    year = data[1][len("nyear") + 3: len(data[1])]  # 数据文本处理：切割、取长度
                    month = data[2][len("nmonth") + 3: len(data[2])]
                    day = data[3][len("nday") + 3: len(data[3])]
                    hrs = data[5][len("nhrs") + 3: len(data[5])]
                    minute = data[6][len("nmin") + 3: len(data[6])]
                    sec = data[7][len("nsec") + 3: len(data[7])]

                    beijinTimeStr = "%s/%s/%s %s:%s:%s" % (year, month, day, hrs, minute, sec)
                    logger7.info(beijinTimeStr)
                    beijinTime = time.mktime(time.strptime(beijinTimeStr, "%Y/%m/%d %X"))  # 将beijinTimeStr转为时间戳格式
                    now_date = time.strftime("%Y_%m_%d", time.localtime(beijinTime))
                    list_num1[1] = False  # 跳出 internet 循环
            except Exception as e:
                logger7.info(f"err---internet: {e}")
                time.sleep(1)

        while list_num1[3]:  # check_time 循环信号
            time.sleep(0.001)
            if list_num1[2] >= 60:  # 失败计数
                logger7.info("本机系统时间与网络时间不同步--all")
                list_num1[3] = False
                continue
            try:
                if beijinTime is not None:
                    now_time = time.time()
                    if abs(int(beijinTime) - int(now_time)) > 3600:
                        list_num1[2] += 1
                        logger7.info("本机系统时间与网络时间不同步--匹配{}次".format(list_num1[2]))
                        time.sleep(1)
                    else:
                        logger7.info("本机系统时间与网络时间一致 -- 验证通过")
                        list_num1[3] = False
                        now_date = time.strftime("%Y_%m_%d", time.localtime())
                else:
                    logger7.info("获取网络时间失败")
                    list_num1[3] = False
            except Exception as e:
                logger7.info(f"err---check_time: {e}")
                time.sleep(1)
        logger7.info("现在日期：{}".format(now_date))
        return now_date

#------------------主体函数------------------------
    '''线程  生产者'''
    def run_produce_AI(self):
        print("进入生产者")
        logger7.info("进入生产者")
        self.bool_check_process_PLC = False

        t2 = time.time()
        time.sleep(2.5)  # 等待自检过程心跳信号完成终止
        photo_m = 0
        change_model1 = False
        self.bool_ai_infer += 11
        if aiCottonConfig.Mechine_function == "claw":
            self.choose_mechine_model = 1  # 2021-0607 抓手模式
        else:
            self.choose_mechine_model = 2  # 2021-0607 喷气模式
        # 循环开始
        while True:
            # for i in range(15):
            try:
                time.sleep(0.001)
                if aiCottonConfig.Bool_sleep_produce:
                    time.sleep(aiCottonConfig.Sleep_time_produce)
                '''被PLC暂停后的操作：保持通讯心跳，监测暂停信号的恢复'''
                # print("暂停信号：{}".format(self.if_need_stop))
                # print("传送带速度：{}".format(self.speed2))
                # self.if_need_stop = 1  # 强制为 运行 信号
                # self.speed2 = 500
                if self.if_need_stop == 0:  # PLC控制待机 0-待机，1-正常运行
                    change_model1 = True
                    self.bool_check_process_PLC = True  # 开始和PLC通讯连接信号
                    self.bool_ctrl_stop = True  # 05-21 看是否需要暂停
                    time.sleep(0.6)
                    print("---生产者---PLC通知设备停机-暂停")
                    self.bool_check_process_PLC = False  # 开始和PLC通讯连接信号

                    # 需要清空所有队列 self.record_queue.queue.clear()
                    continue
                '''暂停消除后，等待传送带速度起来'''
                if change_model1:  # 暂停后启动触发读取取值模式
                    change_model1 = False
                    for f_i in range(4):
                        time.sleep(1.5)
                        self.bool_get_speed_PLC = True  # 05-19 获取传送带速度
                    self.bool_get_label_PLC = True  # 重新启动后读取异纤选择类别
                    self.bool_get_batch_PLC = True  # 重新启动后读取 大小批次

                self.photo_n += 1  # 拍照计数
                if self.photo_n > 20000:
                    self.photo_n = 1
                    photo_m += 1

                bool_take_pic = True
                logger.info("-------@@@@@@点信息状态：{}".format(self.num_point))
                t1 = time.time()  # 上一次循环结束的时间戳
                l_t1 = round((0.6 - (t1 - t2)), 3)
                if l_t1 > 0:
                    time.sleep(l_t1)

                logger.info("生产者-第{}次--循环时间为：-----------{}-----------".format(self.photo_n - 1,
                                                                              round(time.time() - t2, 3)))

                # 上一帧的 存图，aiinfer 不影响下一帧
                t2 = time.time()  # 开始拍摄的时间戳
                # result_takepic = self.__oPoolForRaster.map
                result_takepic = self.cameraModel.takePic()
                # print("拍照返回：{}".format(result_takepic))
                # print("第{}次到拍照结束- 真实-用时：{}s".format(str(self.photo_n), round(time.time() - t2, 3)))
                if len(result_takepic) == len(aiCottonConfig.Camera_id):
                    bool_take_pic = False
                    print("第{}次到拍照结束用时：{}s".format(str(self.photo_n), round(time.time() - t2, 3)))
                    # logger.info("第{}次到拍照结束用时：{}s".format(str(self.photo_n), round(time.time() - t2, 3)))
                else:
                    print("拍照服务返回信息:{}".format(result_takepic))
                    print("相机拍照--失败 --退出程序")
                    # logger.info("拍照服务返回信息:{}".format(result_takepic))
                    # logger.info("相机拍照--失败 --退出程序")
                    os._exit(0)

                if True:
                    list_5 = [self.batch_cotton, t2, 1]
                    id5_take_photo = write_mysql5(list_5)  # 拍照表主键ID
                    # logger.info("拍照表主键ID：{}".format(id5_take_photo))
                t3 = time.time()
                print("第{}次-存拍照表-用时：{}s".format(str(self.photo_n), round(time.time() - t2, 4)))
                if not bool_take_pic:  # 拍照成功-存图，

                    if aiCottonConfig.AI_save_pic_bool:
                        list_save_pic1 = {"tp_num": self.photo_n, "tp_end_time": t3}
                        self.bool_save_pic = False  # 准备及保存图片过程中，信号为False
                        self.__oPoolForRaster1.submit(self.call_ai_savepic_service_v2, list_save_pic1)  # 存图

                    if self.bool_ai_infer > len(aiCottonConfig.Camera_id) - 1:  # 当前帧判断：要是前一帧还在识别，则跳过当前帧
                        self.__oPoolForRaster1.submit(self.call_ai_trigger_data1_v2, self.photo_n, t3, photo_m,
                                                      id5_take_photo, result_takepic)
                    else:
                        self.bool_ai_infer = 3  # # 这一帧跳过时，强制给再下一帧AIinfer
            except Exception as e:
                logger.error(f"err---produce: {e}")
                time.sleep(0.25)

    '''调用存图线程'''
    def call_ai_savepic_v2(self, num_tp, t3):
        list_save_pic1 = {"tp_num": num_tp, "tp_end_time": t3}
        th2 = threading.Thread(target=self.call_ai_savepic_service_v2, args=(list_save_pic1,),
                               name="call_ai_savepic_service_v2")
        th2.start()

    '''调用存图函数'''
    def call_ai_savepic_service_v2(self, list_save_pic2):
        self.save_pic_name1 = []  # 清空
        num_sp = list_save_pic2["tp_num"]
        t4 = list_save_pic2["tp_end_time"]
        # print("存图线程开始启动时间：{}".format(round(time.time() - t4, 3)))
        if aiCottonConfig.AI_save_pic_bool:
            # t5 = time.time()
            res = self.cameraModel.savePic(self.save_pic_aipath)  # res = {}
            # print("res:{}".format(res))
            # print("第{}次，存图线程完成时间-真实：{}".format(num_sp, round(time.time() - t5, 3)))
            if len(res) == len(aiCottonConfig.Camera_id):
                self.bool_save_pic = True
                self.save_pic_name1.append(res)
            else:
                print("存图-调用服务--失败")
                # logger.info("存图-调用服务--失败")
        print("第{}次，存图线程完成时间：{}".format(num_sp, round(time.time() - t4, 3)))

    '''move图片'''
    def move_pic1(self,list_move_pic3):
        try:
            list_pic_name1 = list_move_pic3["list_pic_name"]
            # print("存图名称：{}".format(list_pic_name1))
            for i in range(len(list_pic_name1)):
                pic_path_abs2 = os.path.join(self.save_pic_aipath, list_pic_name1[i])
                copy_path_no1 = "mv -f " + pic_path_abs2 + " " + self.nobox_path + "/"  # 每日刷新nobox 路径
                os.system(copy_path_no1)  # 复制到nobox,不做记录
        except Exception as e:
            logger.error(f"err---move_nobox_pic: {e}")

    '''
    # @list_pic_name=[0pic-name,1pic-name,2pic-name] 
    ['camera39024076_2021_07_16_15_56_34_538084.jpg', 
    'camera48024027_2021_07_16_15_56_34_538084.jpg', 
    'camera48024034_2021_07_16_15_56_34_538084.jpg']
    # @point_world={"1":[{},{}],}
    self.__oPoolForRaster.submit(self.save_pic_message, list_pic_name, point_world)
    '''
    '''生成.txt文件，move 图片'''
    def save_pic_message(self, list_move_pic1):
        try:
            if self.havebox_path is not None:
                list_pic_name1 = []
                list_pic_name2 = list_move_pic1["list_pic_name"]
                for list_cam in aiCottonConfig.Camera_id:
                    for name_pic in list_pic_name2:
                        if list_cam[0] in name_pic:
                            list_pic_name1.append(name_pic)
                            continue

                point_world1 = list_move_pic1["point_world"]
                # print("存图名称：{}".format(list_pic_name1))
                for i in range(len(list_pic_name1)):
                    pic_path_abs = os.path.join(self.save_pic_aipath, list_pic_name1[i])
                    if str(i+1) in point_world1.keys():
                        path_ = list_pic_name1[i]  # 最后的图片名
                        txt_name1 = path_.replace("jpg", "txt")  # 点信息txt文件
                        copy_path_have = "mv -f " + pic_path_abs + " " + self.havebox_path + "/"  # 每日刷新havebox 路径
                        point_data_ori = point_world1[str(i+1)]  # 点数据，原始 #[{},{}]
                        if len(point_data_ori) > 0:  # 此图有点信息时
                            # print("copy_path_have",copy_path_have)
                            os.system(copy_path_have)  # 有点信息的图片直接存havebox/xxxx-日期/图片
                            # 写.txt文件
                            tf1 = open(self.havebox_path + "/" + txt_name1, 'a')

                            list_message1 = []  # 单张图片中的点信息列表
                            # bool_pic_label1 = [True] * len(self.label_path)  # 单张图中的label是否加过
                            for point_message1 in point_data_ori:  # 单张图中的每一个点信息
                                # if point_message1["score"] >= aiCottonConfig.Classification_threshold:
                                #     level_point = "havebox"
                                # else:
                                #     level_point = "suspected"
                                # if bool_record1 > 0:
                                #     for i in range(len(self.label_path)):  # point -label 计数记录 -需要间隔
                                #         if bool_pic_label1[i] and point_message1["label"] == self.label_path[i]:
                                #             self.list_num_label[i] += 1
                                #             bool_pic_label1[i] = False
                                #             bool_record1 += 1
                                point_re_mess1 = {"leftTopX": point_message1["x_min"], "leftTopY": point_message1["y_min"],
                                                  "rightBottomX": point_message1["x_max"],
                                                  "rightBottomY": point_message1["y_max"],
                                                  "labelType": point_message1["label"], "labelMap": {
                                        "level": point_message1["level"], "score": point_message1["score"]
                                    }
                                                  }
                                # print("图中的每个点：{}".format(point_re_mess1))
                                list_message1.append(point_re_mess1)
                                # 开始存信息
                            # print("写入文件时的点信息：{}".format(json.dumps(list_message1)))
                            tf1.write(json.dumps(list_message1))
                            tf1.close()
                        pass
                    else:
                        # remove_path = "rm -f " + pic_path_abs  # 删除原始图片路径
                        copy_path_no = "mv -f " + pic_path_abs + " " + self.nobox_path + "/"  # 每日刷新nobox 路径
                        os.system(copy_path_no)  # 复制到nobox,不做记录
                        pass
        except Exception as e:
            logger.error(f"err---move_deal_pic: {e}")


    '''调用AI识别-内部使用进程'''
    def call_ai_trigger_data1_v2(self, num_tp, start_time, num_mtp, tp_id, list_pic_name1):  # 计数，拍照时间戳，大循环计数
        # print("进入AIinfer--thread")
        self.bool_ai_infer = 0  # AI开始时：0, 完成后置为3
        self.ai_point_data = []
        list_arg1 = [{"num_cam": i, "num_tp": num_tp, "start_time": start_time} for i in
                     range(len(aiCottonConfig.Camera_id))]
        # self.__oPoolForRaster2.map(self.call_ai_1_v2, list_arg1)
        self.call_ai_1_v2(list_arg1[0])  # 串行调用
        self.call_ai_1_v2(list_arg1[1])
        self.call_ai_1_v2(list_arg1[2])
        # self.__oPoolForRaster1.submit(self.call_ai_1_v2, list_arg1[0]) # 线程池 并行调用
        # self.__oPoolForRaster1.submit(self.call_ai_1_v2, list_arg1[1])
        # self.__oPoolForRaster1.submit(self.call_ai_1_v2, list_arg1[2])
        list_tp_num1 = {"num_tp": num_tp, "start_time": start_time, "num_mtp": num_mtp,
                        "tp_id": tp_id, "list_pic_name1": list_pic_name1}
        # self.__oPoolForRaster.map(self.wait_deal_data1, list_tp_num1)
        self.wait_deal_data1(list_tp_num1)

    '''调用AI识别-函数'''
    def call_ai_1_v2(self, list_arg2):
        try:
            # print("进入AIinfer")
            num_cam, num_tp, start_time = list_arg2["num_cam"], list_arg2["num_tp"], list_arg2["start_time"]
            sn = aiCottonConfig.Camera_id[num_cam][0]  # 指定的相机号
            img = self.cameraModel.cameraData[sn][2]  # 处理后的图片
            oriImg = self.cameraModel.cameraData[sn][0]  # oriImg 原始图片数据
            img_name = self.cameraModel.cameraData[sn][1]  # 当前预测的图片
            # print("sn:{}--拿到对应图像".format(sn))
            # print("sn:{}--img_name:{}".format(sn, img_name))
            # print("sn:{}--img:{}".format(sn, img))
            # print("sn:{}--oriImg:{}".format(sn, oriImg))
            res = self.detectionModel.aiInfer(oriImg, img, img_name)  # AI识别  res ={}
            # print("第{}次到AI识别结束用时-真实：{}s".format(str(num_tp), round(time.time() - start_time, 3)))
            # print("AI识别--返回：{}".format(res))
            if len(res["labels"]) > 0:  # 有识别才录入
                list_data_name = [num_cam + 1, res]
                self.ai_point_data.append(list_data_name)  # [[1,{box...}],[2,,{box...}]]
            self.bool_ai_infer += 1  # AI识别完成信号
            print("第{}次到AI识别结束用时：{}s".format(str(num_tp), round(time.time() - start_time, 3)))
        except Exception as e:
            logger.error(f"aiinfer -error: {e}")

    '''等待AI返回，及后续处理'''
    def wait_deal_data1(self, tp_num2):
        num_tp = tp_num2["num_tp"]
        start_time = tp_num2["start_time"]
        num_mtp = tp_num2["num_mtp"]
        tp_id = tp_num2["tp_id"]
        list_pic_name1 = tp_num2["list_pic_name1"]
        bool_check_ai = True
        t_wait_ai = time.time()
        while self.bool_ai_infer < len(aiCottonConfig.Camera_id):  # < 3
            if time.time() - t_wait_ai > 0.6:
                bool_check_ai = False
                break
            time.sleep(0.001)
        if bool_check_ai:
            ai_data_list = copy.deepcopy(self.ai_point_data)
            if aiCottonConfig.AI_draw_pic_bool:  # 根据AI返回，直接画图
                list_draw_ai = [{"ai_data_list": ai_data_list}]
                self.__oPoolForRaster2.map(self.draw_pic_for_ai, list_draw_ai)
            if aiCottonConfig.Mechine_function == "gas":  # 处理喷气类的点信息
                self.point_deal_gas(ai_data_list, start_time, num_mtp, num_tp)
            elif aiCottonConfig.Mechine_function == "claw":  # 处理抓手类的点信息
                while not self.produce_point_is_OK:  # 在上一帧的点数据处理过程中，等待 当False时正在执行上一轮，等待
                    time.sleep(0.001)
                self.point_deal_claw(ai_data_list, start_time, self.speed2, num_mtp, num_tp,
                                     tp_id, list_pic_name1)  # ai_data_list =[[1,{box...}],[2,{box...}]]
        else:
            logger.info("第{}次点处理跳过，AI未全部返回：当前AI返回数量：{}".format(num_tp, self.bool_ai_infer))
    '''2021-06-07---点的数据处理'''
    def point_deal_claw(self, ai_result, start_time, speeedas2, photo_m, photo_n, id5_take_photo, list_pic_name):
        self.produce_point_is_OK = False
        t5 = time.time()
        print("第{}次---进入点位处理--抓手".format(photo_n))
        # print("AI返回的原始数据，ai_result:{}".format(ai_result))
        if len(ai_result) > 0:  # [[1,{box...}],[2,,{box...}]]
            point_world = {}
            for point_data1 in ai_result:
                w_point1 = self.processAiData(point_data1[1], point_data1[0])  # 生成世界坐标{"1":}
                # [] or [{},{}]  会有空值
                if len(w_point1) > 0:
                    point_world[str(point_data1[0])] = w_point1  # point_world = {"1":[{},{}],}
            # logger7.info("第{}次，世界坐标数据，point_world:{}".format(photo_n, point_world))
            # @list_pic_name=[0pic-name,1pic-name,2pic-name]
            # @point_world={"1":[{},{}],}
            if aiCottonConfig.AI_save_pic_bool:
                list_move_pic = [{"list_pic_name": list_pic_name, "point_world": point_world}]
                self.__oPoolForRaster2.map(self.save_pic_message, list_move_pic)
            if len(point_world) > 0:  # 当转换后的点 存在时
                point_arr = caculate_nearly_point(point_world)  # 舍去相机重合点 #走到这一步，必有点
                if point_arr is not None:
                    # print("the checked result is {}".format(point_arr))
                    # print("start_time:{}  speeedas2:{}".format(start_time, speeedas2))
                    self.num_point[3] += len(point_arr)  # 同步去重后的点数量
                    datapiont1 = self.remove_point2(point_arr, start_time, speeedas2)
                    # print("@@@@@@@@@@@@@@-----({})---time:{}----speed:{}".format(photo_n,start_time,speeedas2))
                    logger7.info("第{}次，异步去重后-筛选后结果：{}".format(photo_n, datapiont1))
                    if datapiont1 is not None:
                        self.put_record2queue(datapiont1, start_time, speeedas2, photo_n,
                                              id5_take_photo)  # 将点写入队列（生产者调用）
        else:
            if aiCottonConfig.AI_save_pic_bool:
                list_move_pic2 = [{"list_pic_name": list_pic_name}]
                self.__oPoolForRaster2.map(self.move_pic1, list_move_pic2)
        print("第{}次仅点数据处理用时：{}s".format(photo_n, round(time.time() - t5, 3)))
        print("第{}次-从拍完照--存入队列 用时：{}s".format(photo_n, round(time.time() - start_time, 3)))
        self.produce_point_is_OK = True
#------------------基础函数------------------------
    '''循环自增数，1~100，给PLC发送变化数据，自证连接正常'''
    def num_changed1(self):
        self.num_changeda += 1
        if self.num_changeda > 500:
            self.num_changeda = 1
        return self.num_changeda

    '''去重___前后拍照数据筛选'''

    def remove_point2(self, pointZ1, time01, speeda1):
        i, k = 0, 0
        for pa1 in pointZ1:  # pointZ1 = [{},{}]
            if len(pa1) > 0:  # 单个点里有值
                k += 1
        if k > 0 and speeda1 > 20:  # =0时，说明传过来的是空值，不进行操作
            dataZ2 = copy.deepcopy(self.dataZ1)
            pointZ2 = copy.deepcopy(pointZ1)
            # logger2.info("now_point_or---:{},,s:{},t:{}".format(pointZ1, speeda1, time01))

            if not len(dataZ2) == 0:  # 当存储器有值时，进行对比

                for pointZC in dataZ2:  # dataZ2=[[],[],[]]------pointZC=[time,[{},{},{}]]
                    key1 = pointZC[0]
                    # 对比存储器中的个时间点组（超限-舍去，不超-对比）
                    if time01 - key1 > (570 / int(abs(speeda1) + 1) + 2.2):
                        if pointZC in self.dataZ1:
                            self.dataZ1.remove(pointZC)  # 去掉超出限制的点
                    else:
                        for pointb2 in pointZ2:  # 最新的点组pointZ2=[{},{},{}] , pointb2={}=value1
                            for value1 in pointZC[1]:  # pointZC=[time,[{},{},{}]], #value1字典{X， Y，position,WX,WY}
                                if abs(value1["worldX"] - pointb2["worldX"]) < 40:  # 先对比X，若不同，应该不是同一个点
                                    l1 = round(speeda1 * (time01 - key1), 2)  # 2组数据实际的距离
                                    l2_rm1 = max(55, abs(round(time01 - key1, 2)) * 28)  # 随时间跨度而增加的Y方向重合限制，起始值35
                                    if abs(float(value1["worldY"] - pointb2[
                                        "worldY"]) - l1) < l2_rm1:  # 新点pointb2 +l1 == 旧点value1
                                        if pointb2 in pointZ1:
                                            pointZ1.remove(pointb2)

            # logger7.info("去重后的点：{}".format(pointZ1))
            if len(pointZ1) > 0:
                # 当点的数量大于限定数量时，根据优先级，置信度来排序
                limit_piont_count = 5
                if len(pointZ1) > limit_piont_count:
                    new_point_list = self.get_good_point_list(pointZ1, limit_piont_count)
                    self.dataZ1.append([time01, new_point_list])
                    return new_point_list
                else:
                    self.dataZ1.append([time01, pointZ1])
                    # logger2.info("Save_pool---:{}".format(pointZ1))
                    return pointZ1
            else:
                return None
        else:
            return None

    # new_s = sorted(real_point_arr, key=lambda e: e.__getitem__('worldY'))  # 按Y排序
    # # print(" after sort real_point_arr ",new_s)
    # return new_s  # new_s = [{},{}...]
    def get_good_point_list(self, before_list, limit_count):
        new_point_list, back_list = [], []
        now_count = [0, 0]  # [0]之前累加列表元素和，[1]当前累加列表元素和
        list_label = [[], [], [], [], []]  # 分类别存点，方便统计
        list_back = [[], [], [], [], []]
        for point_b in before_list:  # 先分类别存点
            for ip in range(len(list_label)):
                if point_b["level"] == ip + 1:
                    list_label[ip].append(point_b)
        # print("3:{}".format(list_label))
        for il in range(len(list_label)):  # 依次从各列表中取出点
            now_count[1] += len(list_label[il])  # 把现在的这个列表里的点个数加上 计数
            if now_count[1] > limit_count:  # 现有计数值大于 限定值时 当前列表要排序
                list_back[il] = sorted(list_label[il], key=lambda e: e.__getitem__('score'), reverse=True)  # 按分数排序 or score
                now_list_num = limit_count - now_count[0]  # 当前列表应该截取的长度
                new_point_list.extend(list_back[il][:now_list_num])
            else:
                new_point_list.extend(list_label[il])  # 因为总个数不足5个，当前表直接加在输出表述上
            if now_count[1] >= limit_count:  # 现有计数值大于等于 限定值时 跳出循环
                break
            now_count[0] += len(list_label[il])
        back_list = sorted(new_point_list, key=lambda e: e.__getitem__('worldY'))  # 按分数排序 or score
        return back_list


    '''存入队列'''
    def put_record2queue(self, point_arr, start_time, speed1, num_tp, id5_take_photo):  # 将点写入队列（生产者调用）
        try:
            if point_arr is not None:
                num_tp_i = 0
                # while len(self.after_pic_path) != 3:
                #     pass
                # logger4.info(" point_arr {}".format(point_arr))
                for item in point_arr:
                    # logger4.info("进入该点信息")
                    num_tp_i += 1  # 单帧里 有效点的个数
                    self.num_point[4] += 1  # 实际存入队列 点 总数
                    item["speed"] = speed1  # 速度
                    item["start_time"] = start_time  # 在每组坐标的字典上添加开始时间的对应组
                    item["id_tp"] = id5_take_photo  # 拍照表ID
                    item["ID_point"] = str(num_tp) + "_" + str(num_tp_i)  # 点的ID(给自己分析用的)
                    item["times_judge"] = 0  # 判别是经过几个抓手了(给自己分析用的)

                    # logger4.info("该点信息-biaoji1")
                    # logger4.info("self.after_pic_path:{}".format(self.after_pic_path))
                    # logger4.info("item-position:{}".format(item["position"]))
                    # item["id_pic"] = self.after_pic_path[str(item["position"])]
                    item["id_pic"] = 123
                    # logger4.info("该点信息-已赋值")
                    # item["time_arm"] = time.time()
                    if item["level"] == 1:
                        num_OK, num_NG = self.real_put_point_record(self.queue_first[0], item, "异纤优先-第一梯队")
                    elif item["level"] == 2:
                        num_OK, num_NG = self.real_put_point_record(self.queue_second[0], item, "色绒优先-第一梯队")
                    elif item["level"] == 3:
                        num_OK, num_NG = self.real_put_point_record(self.queue_third[0], item, "脏绒+羊屎-第一梯队")
                    elif item["level"] == 4:
                        num_OK, num_NG = self.real_put_point_record(self.queue_fourth[0], item, "异纤常规-第一梯队")
                    else:
                        num_OK, num_NG = self.real_put_point_record(self.queue_fifth[0], item, "色绒常规-第一梯队")
                if num_tp_i > 0:
                    logger4.info("第{}次,本轮生成{}个点--耗时：{}".format(num_tp, num_tp_i, round(time.time() - start_time, 3)))
        except Exception as e:
            logger.error(f"err--put.queue_first---+++++++: {e}")

    '''向PLC --获取批次号 '''
    def get_batch(self, sign2):  # 获得批次号
        result_big, result_small = self.read_batch(sign2)
        self.batch_cotton = result_big + "-" + result_small
        logger.info("+++++++++++此时批次号为：{}".format(self.batch_cotton))

    '''读取批次号--PLC通讯'''
    def read_batch(self, sign1):  # 初始化时 sign1=Fasle ，
        logger.info('读取批次号--PLC通讯--1')
        result1_char1, result2_char1 = None, None
        sign2 = True  # 默认去读写
        if sign1:
            result_sign = self.PLC_ctrl[1].read_bit_data(aiCottonConfig.MELSEC_CODE.SIGN_BATCH, 1)
            if result_sign[0] == 0:  # 当信号位为0，表示无变化时，不去读取大小批次
                sign2 = False
        logger.info('读取批次号--PLC通讯--2')
        if sign2:
            result1_ascii = self.PLC_ctrl[1].read_word_data(aiCottonConfig.MELSEC_CODE.BIG_BATCH, 5)
            result1_char1 = self.ascii_to_char(result1_ascii)
            result2_ascii = self.PLC_ctrl[1].read_word_data(aiCottonConfig.MELSEC_CODE.SMALL_BATCH, 8)
            result2_char1 = self.ascii_to_char(result2_ascii)
        logger.info('result1_char1：{}， result2_char1：{}'.format(result1_char1, result2_char1))
        return result1_char1, result2_char1

    def ascii_to_char(self, list_int):
        char_batch1 = ""

        for j in range(len(list_int)):
            if list_int[j] == 0:
                continue
            if list_int[j] < 256:  # 2的8次方，8位
                result_b = chr(list_int[j])  # ASCII码 转成 字符
                # print("ASCII码:{} 转成 字符:{}".format(list_int[j], result_b))
                char_batch1 += result_b
            else:
                code_ascii = bin(list_int[j])
                # print('code_ascii:{}'.format(code_ascii))
                int1 = code_ascii[-8:]
                int2 = code_ascii[:-8]
                char_a = [int1, int2]
                for i in range(len(char_a)):
                    # print('2-code{}：{}'.format(i + 1, char_a[i]))
                    test_b2 = int(char_a[i], 2)
                    result_b = chr(test_b2)  # ASCII码 转成 字符
                    # print("ASCII码:{} 转成 字符:{}".format(test_b2, result_b))

                    char_batch1 += result_b
        # print('char_batch1:{}'.format(char_batch1))
        return char_batch1

    '''选取点类别'''
    def read_limit_label(self, num_now):
        num_limit_label = aiCottonConfig.Choose_label
        all_limit_label = aiCottonConfig.Choose_type
        if num_limit_label >= 10:  # 小于10时，强制赋值取数
            time.sleep(3)  # 保证能取到 num_now = self.choose_model1
            num_limit_label = num_now + 1
        for i in range(num_limit_label):
            for dict_p1 in all_limit_label[i]:
                self.list_zh1.update(dict_p1)
        print("此次运行，选择的类别：{}".format(self.list_zh1))
        logger7.info("此次运行，选择的类别：{}".format(self.list_zh1))
    # self.queue_first = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
    # self.queue_second = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
    # self.queue_third = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
    # self.queue_fourth = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
    # self.queue_fifth = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
    '''读取队列'''
    def choose_point1(self, numAB):
        # 抓手1只读第一梯队队列，抓手2读第一、二梯队队列，抓手3、4读第一、二、三梯队队列
        if numAB > 3:
            numAB = 3
        rePP1 = None
        for i in range(numAB):
            j = numAB - i - 1
            if not self.queue_first[j].empty():
                rePP1 = self.queue_first[j].get()
                logger4.debug('抓手{}取到 第{}梯队 异纤优先 点数据 {}'.format(numAB, j + 1, rePP1))
                break  # 依次取， 一旦有取到值，跳出for循环
            elif not self.queue_second[j].empty():
                rePP1 = self.queue_second[j].get()
                logger4.debug('抓手{}取到 第{}梯队 色绒优先 点数据 {}'.format(numAB, j + 1, rePP1))
                break  # 依次取， 一旦有取到值，跳出for循环
            elif not self.queue_third[j].empty():
                rePP1 = self.queue_third[j].get()
                logger4.debug('抓手{}取到 第{}梯队 脏绒+羊屎 点数据 {}'.format(numAB, j + 1, rePP1))
                break  # 依次取， 一旦有取到值，跳出for循环
            elif not self.queue_fourth[j].empty():
                rePP1 = self.queue_fourth[j].get()
                logger4.debug('抓手{}取到 第{}梯队 异纤常规 点数据 {}'.format(numAB, j + 1, rePP1))
                break  # 依次取， 一旦有取到值，跳出for循环
            elif not self.queue_fifth[j].empty():
                rePP1 = self.queue_fifth[j].get()
                logger4.debug('抓手{}取到 第{}梯队 色绒常规 点数据 {}'.format(numAB, j + 1, rePP1))
                break  # 依次取， 一旦有取到值，跳出for循环

        return rePP1

    '''判断第1、2、3梯队的 队列是否为空'''
    def judge_empty_third_queue(self):
        return self.queue_first[0].empty() and self.queue_second[0].empty() and self.queue_third[0].empty() and \
               self.queue_fourth[0].empty() and self.queue_fifth[0].empty() and \
               self.queue_first[1].empty() and self.queue_second[1].empty() and self.queue_third[1].empty() and \
               self.queue_fourth[1].empty() and self.queue_fifth[1].empty() and \
               self.queue_first[2].empty() and self.queue_second[2].empty() and self.queue_third[2].empty() and \
               self.queue_fourth[2].empty() and self.queue_fifth[2].empty()

    '''判断第1、2梯队的 队列是否为空'''
    def judge_empty_second_queue(self):
        return self.queue_first[0].empty() and self.queue_second[0].empty() and self.queue_third[0].empty() and \
               self.queue_fourth[0].empty() and self.queue_fifth[0].empty() and \
               self.queue_first[1].empty() and self.queue_second[1].empty() and self.queue_third[1].empty() and \
               self.queue_fourth[1].empty() and self.queue_fifth[1].empty()

    '''判断第1梯队的 队列是否为空'''
    def judge_empty_first_queue(self):
        return self.queue_first[0].empty() and self.queue_second[0].empty() and self.queue_third[0].empty() and \
               self.queue_fourth[0].empty() and self.queue_fifth[0].empty()

    '''将点信息 存入队列，若满即删并记录'''
    def real_put_point_record(self, queue_put, point_message, name_queue):
        ai_point_all31 = 0
        if queue_put.full():
            throw1 = queue_put.get()
            logger4.info("get the record from full queue")
            list_point = [throw1.get("id_tp"), throw1.get("id_pic"),
                          throw1.get("speed"), throw1.get("x_max"),
                          throw1.get("y_max"), throw1.get("x_min"),
                          throw1.get("y_min"), throw1.get("worldX"),
                          throw1.get("worldY"), 5, throw1.get("label"),
                          throw1.get("score"), throw1.get("level")]
            ai_point_all31 += 1  # 统计AI识别到的点--存入队列 但因满队列而删掉的点
            # write_mysql(list_point)
            if not self.sql_point_queue.full():
                self.sql_point_queue.put(list_point)
            self.num_point[7] += 1
            logger4.info("舍去：{}队列舍去最早入队的点：{}".format(name_queue, throw1))
        queue_put.put(point_message)  # 放到队列里
        ai_point_all32 = 1  # 统计AI识别到的点--最后存入队列的
        logger4.info("存入：{}队列存入点：{}".format(name_queue, point_message))
        return ai_point_all32, ai_point_all31



#--------------------喷气相关---------------------

    '''喷气--选喷气孔'''
    def X_classify(self,x):
        all_gas_hole = 60 #气嘴数量,PLC分为4组[0-14,15-29,30-44,45-59]
        list_zu = [[0,15],[15,30],[30,45],[45,60]]
        list_num = [[0,0,0,0],[False,False,False,False]]
        length_csd = 1200
        len_hole = int(length_csd/all_gas_hole) #每个气嘴管控的宽度
        num_gas_hole = x // len_hole
        list_01 = [0] * all_gas_hole  # 生成对应喷嘴的0列表
        if num_gas_hole > 0 and num_gas_hole < all_gas_hole:
            list_01[num_gas_hole-1: num_gas_hole+1] = 1, 1, 1 #对应喷嘴号 ，及相邻喷嘴写成1
            for ni in range(len(list_zu)):
                if num_gas_hole-1 in range(list_zu[ni][0],list_zu[ni][1]):
                    list_num[1][ni] = True
                elif num_gas_hole in range(list_zu[ni][0],list_zu[ni][1]):
                    list_num[1][ni] = True
                elif num_gas_hole + 1 in range(list_zu[ni][0], list_zu[ni][1]):
                    list_num[1][ni] = True
        elif num_gas_hole == 0:
            list_01[:2] = 1, 1
            list_num[1][0] = True
        else:
            list_01[-2:] = 1, 1
            list_num[1][3] = True
        for zi in range(len(list_num[1])):
            if list_num[1][zi]:
                list_num[0][zi] = self.list_to_int(list_zu[zi],list_01)
        return list_num[0]

    '''处理列表分组，并转成int型'''
    def list_to_int(self,num, n_list): #处理列表分组，并转成int型
        list_d = n_list[num[0]:num[1]]
        list_d.reverse()
        list_d_a = [str(i) for i in list_d]
        str_d = "".join(list_d_a)
        list_num = int(str_d, 2)
        return list_num

    def point_zu_record(self, point_arr, start_time, speed1, num_tp):  # 将点写入队列（生产者调用）
        logger.info(" point_arr {}".format(point_arr))
        if point_arr is not None:
            num_tp_i = 0
            list_pic_up = [[],[],[]]
            list_pic_down = [[],[],[]]
            for item in point_arr:
                self.ai_point_record.real_all_piont_put += 1  # 实际存入队列 点 总数
                if item["y"] >= 1024:
                    if len(list_pic_up[0]) == 0:
                        item["speed"] = speed1
                        item["start_time"] = start_time  # 在每组坐标的字典上添加开始时间的对应组
                        num_tp_i += 1
                        item["ID_tp"] = num_tp
                        item["ID_point"] = str(num_tp) + "_" + str(num_tp_i)
                        item["times_judge"] = 0
                        list_pic_up[0].append(item)
                    list_pic_up[1] = item["worldX"]
                    list_pic_up[2] = item["worldY"]
                else:
                    if len(list_pic_down[0]) == 0:
                        item["speed"] = speed1
                        item["start_time"] = start_time  # 在每组坐标的字典上添加开始时间的对应组
                        num_tp_i += 1
                        item["ID_tp"] = num_tp
                        item["ID_point"] = str(num_tp) + "_" + str(num_tp_i)
                        item["times_judge"] = 0
                        list_pic_down[0].append(item)
                    list_pic_down[1] = item["worldX"]
                    list_pic_down[2] = item["worldY"]
            # for i in range(len(list_pic_up[2])):
            #     #列表求和
            #
            #     # item["time_arm"] = time.time()
            #     # if item["level"] == 1:
            #     num_OK, num_NG = self.real_put_point_record(self.queue_first[0], item, "异纤优先-第一梯队")
            #     self.ai_point_record.real_fiber_priority_put += num_OK  # 实际存入队列 异纤 优先
            #     self.ai_point_record.real_fiber_priority_throw += num_NG  # 异纤 优先 存入时因队列满删掉的点数
                # elif item["level"] == 2:
                #     num_OK, num_NG = self.real_put_point_record(self.record_queue, item, "其他-主")
                #     self.ai_point_record.real_other_label_put += num_OK  # 实际存入队列 其他异常点
                #     self.ai_point_record.real_other_label_throw += num_NG  # 其他异常点 存入时因队列满删掉的点数
                # else:
                #     num_OK, num_NG = self.real_put_point_record(self.fiber_seemingly_queue, item, "异纤-疑似-主")
                #     self.ai_point_record.real_fiber_seemingly_put += num_OK  # 实际存入队列 异纤 疑似
                #     self.ai_point_record.real_fiber_seemingly_throw += num_NG  # 异纤 疑似 存入时因队列满删掉的点数
            if num_tp_i > 0:
                logger4.info("第{}次,本轮生成{}个点--耗时：{}".format(num_tp, num_tp_i, time.time() - start_time))

# --------------------暂未用到---------------------
    '''PLC通讯——异常报错记录_12_16'''
    def record_err(self):
        while self.bool_lock_time:
            time.sleep(0.1)
        else:
            self.lock.acquire()#线程锁
            try:
                name11 = aiCottonConfig.MELSEC_CODE.ERR_STATUS  # "D112"#PLC 异常记录更新位（有变化才写入）2020——1212
                name12 = aiCottonConfig.MELSEC_CODE.ERR_RECORD  # "M500"#PLC 异常记录初始位2020——1212
                list_char = aiCottonConfig.ERR_LIST
                result12 = self._melsec_ctrl.read_word_data(name11, 1)  # 读取
                print('result12', result12)
                status_send = int(result12[0])
                if status_send != self.num_err_record:
                    self.num_err_record = copy.deepcopy(status_send)
                    result13 = self._melsec_ctrl.read_bit_data(name12, 33)  # 读取
                    print('result13', result13)
                    num_id = 0
                    for id_record in result13:
                        num_id += 1
                        if int(id_record) == 1:
                            record_code = list_char.get(str(num_id))
                            print('record_code', record_code)
                            list_err_record = [num_id, time.time(), record_code]
                            write_mysql2(list_err_record)
            finally:
                self.lock.release()

    '''测试PLC--抓手获取时间戳和X位置'''
    def test_send(self):  # 单独循环测试ARM2抓手3的抓取
        self.connect_PLC_thread()  # 开线程-发送PLC连接通断信号
        time.sleep(3)
        self.num_claw_state = 4  # 抓手个数
        list_x1 = [400, 1600, 800, 1400, 1200, 1000, 600, 1750]
        for i in range(10000):
            if i % 30 == 29:
                self.bool_circulation_process_PLC = True  # PLC通讯心跳
            '''读取+判断 抓手状态'''
            while self.bool_send_toPLC_claw:  # 等上一次的发送成功后，或上次无发送
                time.sleep(0.001)
            self.list_claw_state = []  # 清空上一次的抓手状态

            self.bool_read_claw_state = True  # 读取+判断 抓手状态
            while len(self.list_claw_state) < 1:
                time.sleep(0.001)

            if self.list_claw_state[4] == 0 and self.list_claw_state[5] == 0:
                print("第{}次--抓手3空闲".format(i))  # 进入抓手3比较部分
            else:
                time.sleep(2)
                continue
            self.bool_read_plc_time_2 = True  # 读取PLC--模块2--时间戳
            while self.bool_read_plc_time_2:
                pass
            print("self.time_plc:{}".format(self.time_plc))
            end_time = self.time_plc + 5000
            print("end_time:{}".format(end_time))
            sec, mill_sec = long2time(end_time)  # 毫秒转时间
            j = i % 8
            x1 = list_x1[j]
            self.send_toPLC_list = [3, int(sec), int(mill_sec), int(x1)]
            self.bool_send_toPLC_claw = True
            time.sleep(8)

######2021-05-19----喷气部分------------#########
    '''处理AI的点信息，筛选点'''
    def choose_point_from_AI(self, ai_data_list2, photo_m, photo_n, t2):
        # ai_data_list2 =[1,{"boxes":[]----},2,{----}]
        if len(ai_data_list2) == 0:
            photo_nm = str(photo_m) + "_" + str(photo_n)
            return photo_nm, None
        else:
            ai_point = {}
            for point_i in range(len(ai_data_list2)):
                num_cam = ai_data_list2[point_i][0]
                data_cam = ai_data_list2[point_i][1]
                ai_point[num_cam] = self.processAiData(data_cam, num_cam)
                # {"1":[{点信息},{点信息}],"2":[{点信息}]}
            print("生产者--点信息筛选完:{}".format(round(time.time() - t2, 3)))

            photo_nm = str(photo_m) + "_" + str(photo_n)
            return photo_nm, ai_point

    '''对前后2帧图像上的点进行去重'''
    def remove_same_point(self, point_name_dict, starttime1, num_str):
        # print("进入--去重")
        now_data = copy.deepcopy(point_name_dict)  # 现帧的备份点集 -now
        if self.before_point_data is not None:  # 开始时为none,直接复制和返回
            fore_time = self.before_point_data[0]
            if starttime1 - fore_time < 0.4:  # 相隔太长，不做对比，直接复制和返回
                fore_data = self.before_point_data[1]
                for key1, vaule1 in point_name_dict.items():  # 分相机-now
                    point_list = fore_data[key1]  # 对应相机中的点列表 -before
                    '''先举出now中的点，去一次对比before的每个点'''
                    for num_x in range(len(vaule1)):  # 分每个点 -now
                        point_x = vaule1[num_x].get("worldX")  # -now
                        point_y = vaule1[num_x].get("worldY")  # -now
                        for num_xf in range(len(point_list)):
                            bf_point_x = point_list[num_xf].get("worldX")  # -before
                            bf_point_y = point_list[num_xf].get("worldY")  # -before
                            if abs(point_x - bf_point_x) < 20:
                                speed_len1 = round(self.speed2 * (starttime1 - fore_time), 2)
                                if abs(point_y - bf_point_y - speed_len1) < 100:
                                    logger5.info("点重合：T:{} and {}  P:{} and {}".format(fore_time, starttime1,
                                                                                       point_list[num_xf],
                                                                                       vaule1[num_x]))
                                    '''如果重合，删掉备份中的该点，并跳过该点'''
                                    if vaule1[num_x] in now_data[key1]:
                                        now_data[key1].remove(vaule1[num_x])
                                    break  # 跳出对now该点的数次before点的循环，进入下一个now点

        self.before_point_data = [starttime1, now_data]
        print("生产者-第{}次--点去重完:{}".format(num_str, round(time.time() - starttime1, 3)))
        return now_data

    '''处理喷气对应点数据'''
    def deal_with_point(self, point_name_dict, starttime1, num_str):
        # {"1":[{点信息},{点信息}],"2":[{点信息}]}
        # print("进入--处理喷气对应点数据")
        x_list = []
        y_list = []
        point_dict = {}
        point_list = []
        result_point = None
        for key1, vaule1 in point_name_dict.items():

            for num_x in range(len(vaule1)):
                point_x = vaule1[num_x].get("worldX")
                point_y = vaule1[num_x].get("worldY")
                r_x_list = self.X_choose_hole(point_x)  # [x1,x2] 或者[x1]
                for x_a in r_x_list:
                    if x_a not in x_list:  # 单张x去重
                        x_list.append(x_a)
                        point_dict[str(x_a)] = point_y
                    else:
                        if point_y > point_dict[str(x_a)]:  # 同喷气孔 远处覆盖近处
                            point_dict[str(x_a)] = point_y
                y_list.append(point_y)
        if len(y_list) > 0:
            min_y = min(y_list)  # 一次拍照后的最小y值(最近值)
            for key2, vaule2 in point_dict.items():
                num_pq1 = int(float(key2))
                l_y = vaule2 - min_y
                if l_y < 200:
                    point_list.append([num_pq1, 250])
                elif l_y < 400:
                    point_list.append([num_pq1, 410])
                else:
                    point_list.append([num_pq1, 550])
                # [[喷嘴号，时长]，[喷嘴号，时长]，[喷嘴号，时长]]
            result_point = [starttime1, min_y, point_list, num_str]  # [时间戳，最近距离，喷气列表,拍照次数]
        # print("{}次拍照-点数据处理结果:{}".format(num_str, result_point))
        print("生产者-第{}次--点合并处理完:{}".format(num_str, round(time.time() - starttime1, 3)))
        #  0_1次拍照-点数据处理结果:[1622012660.7516744, 858.9695983852196, [[13, 140], [17, 140], [16, 140]], '0_1']
        return result_point

    '''对X值处理-喷气空的选择'''
    def X_choose_hole(self, x):
        x_list = []

        if x <= 15:
            x_list.append(0)
        elif x >= 1185:
            x_list.append(59)
        else:
            num_hole = x // 20  # 喷气孔号，20为喷气间隔宽度(0-59,60)
            x_list.append(num_hole)
            throw_x = x % 20  # 剩余距离
            if throw_x > 15:
                x_list.append(num_hole + 1)
            elif throw_x < 5:
                x_list.append(num_hole - 1)
        return x_list

    def point_deal_gas(self, ai_data_list1, t2, photo_m, photo_n):
        self.produce_point_is_OK = False
        photo_nm, ai_point = self.choose_point_from_AI(ai_data_list1, photo_m, photo_n, t2)
        # self.bool_ai_infer += 11 #表示上1帧的AI数据已经使用完成
        if ai_point is not None:
            point_now = self.remove_same_point(ai_point, t2, photo_nm)  # 前后帧去重
            point_result1 = self.deal_with_point(point_now, t2, photo_nm)  # 处理点数据，
            if point_result1 is not None:
                if self.fiber_queue.full():
                    point_throw = self.fiber_queue.get()
                    logger5.info("{}次拍照-队列已满，删除数据:{}".format(photo_nm, point_throw))
                self.fiber_queue.put(point_result1)
                print("生产者-第{}次，点信息存入队列,耗时：{}".format(photo_nm, round(time.time() - t2, 3)))
        else:
            print("生产者-第{}次--点处理--AI识别图中--无异常,耗时：{}".format(photo_nm, round(time.time() - t2, 3)))
        self.produce_point_is_OK = True

    def wait_send_PLC(self, y_l, time0):
        wait_time1 = round(y_l / self.speed2 - (time.time() - time0) - 0.04 - aiCottonConfig.PQ_T, 3)
        print("消费者--wait_time1:{}--现在时间戳：{}".format(wait_time1, time.time()))
        if wait_time1 > 0:
            time.sleep(wait_time1)
            self.bool_circulation_qp_PLC = True  # 发送给PLC 喷气指令-信号

    def get_queue(self):
        if self.fiber_queue.empty():
            time.sleep(0.01)
            return None
        else:
            point = self.fiber_queue.get()
            return point

    def consume_gas_injection1(self):  # 消费者-喷气模块

        # 05-12 假设喷气频率0.2s
        self.bool_check_process_PLC = False
        arm_ctrl = aiCottonConfig.ARM_number
        label_list1 = [0, 0]  # 计数保存位置
        print("进入消费者")
        while True:
            try:
                time.sleep(0.001)
                '''暂停后，会因为生产者无队列录入，而卡住循环(相当于暂停)  '''
                if self.photo_n % 30 == 29:
                    if self.photo_n != label_list1[0]:  # 当在29计数时间段内，确保指执行1次
                        self.bool_circulation_process_PLC = True  # PLC通讯心跳
                        label_list1[0] = copy.deepcopy(self.photo_n)
                    self.bool_ctrl_stop = True  # 读取是否需要暂停
                elif self.photo_n % 100 == 99:
                    if self.photo_n != label_list1[1]:
                        self.bool_get_speed_PLC = True  # 监测传送带速度
                        label_list1[1] = copy.deepcopy(self.photo_n)
                # print("消费者--去队列前一步")
                '''此步骤会等待，至队列中有元素'''
                point_message1 = self.get_queue()  # [时间戳，最近距离，喷气列表,拍照次数]
                if point_message1 is None:
                    continue
                # print("get-point")
                pq_list = [0] * 60
                x_list = point_message1[2]
                print("消费者--x_list:{}".format(x_list))
                for num_pq in x_list:  # [[num, l_t],] 0-59
                    pq_list[59 - num_pq[0]] = num_pq[1] + aiCottonConfig.PQ_X  # 修正后的喷嘴号
                # 队列满了就等待，要维持 某次的等待时间和发送数据的对应，不能错位
                print("消费者存入PLC读取队列：{}".format(point_message1[3]))
                self.pqlist_queue.put([point_message1[3], pq_list])
                time_00 = point_message1[0]
                y = point_message1[1] + aiCottonConfig.PQ_Y
                print("消费者--总距离：{}，原来剩余时间：{}，现在经过时间：{}".format(y, y / self.speed2, time.time() - time_00))
                self.__oPoolForRaster1.submit(self.wait_send_PLC, y, time_00)  # 1600/1200 = 1.33 /0.24 =6 会同时存在6个
                # th1_wait_p = threading.Thread(target=self.wait_send_PLC, args=(y, time_00,),
                #                               name="wait_send_PLC")
                # th1_wait_p.start()
                pass
            except Exception as e:
                logger.error(f"consume_gas_injection  err: {e}")
                time.sleep(1)



    # ####---------------AI返回/数据处理-------------

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

    # list_zh1:
    # {'yixian': [[0.32, 0.4], [800, 800]],
    # 'serong': [[0.25, 0.5], [800, 2500]],
    # 'zangmian': [[0.25, 0.5], [800, 2500]],
    # 'yangshi': [[0.25, 0.25], [800, 800]],
    # 'mpg': [[0.25, 0.25], [800, 800]]}
    '''像素坐标 换算 世界坐标'''
    def processAiData(self, res_data, position):  # 返回像素点坐标，相机位置，世界坐标的字典 的列表#（生产者调用）
        arr = []
        data_label = res_data["labels"]
        if len(data_label) > 0:  # 为空列表时，可以直接返回 arr = []
            data_score = res_data["scores"]
            data_point = res_data["boxes"]
            for i_point in range(len(data_label)):  # 分每个点
                self.num_point[0] += 1  # 计数 AI 识别总数
                if data_label[i_point] in self.list_zh1.keys():  # 当 label 是在PLC传来的分类列表中
                    self.num_point[1] += 1  # 计数 AI中 所有符合分类的点
                    # 先判断 点的位置
                    if data_point[i_point][1] < 50 or data_point[i_point][3] > 2000:  # Y方向，靠近边缘，极有可能是识别不全，舍去
                        continue
                    if data_point[i_point][0] < 100 or data_point[i_point][2] > 2348:  # X方向，靠近边缘，极有可能是识别不全，舍去(相邻相机重合370pix)
                        continue
                    # 判断分数
                    if float(data_score[i_point]) <= self.list_zh1[data_label[i_point]][0][0]:
                        continue
                    # 判断面积
                    length_x = int(data_point[i_point][2] - data_point[i_point][0])
                    length_y = int(data_point[i_point][3] - data_point[i_point][1])
                    point_area = abs(length_x * length_y)
                    if point_area <= self.list_zh1[data_label[i_point]][1][0]:
                        continue
                    # self.ai_point_record.ai_pix_main += 1  # 计数 AI 符合分类、不在边缘处 的点
                    x = (data_point[i_point][0] + data_point[i_point][2]) / 2  # 图片中的像素坐标
                    y = (data_point[i_point][1] + data_point[i_point][3]) / 2
                    worldx, worldy, worldz = image_points_to_world_plane(x, y, int(position))  # 换算过后的世界坐标
                    if worldx < aiCottonConfig.Min_value_X or worldx > aiCottonConfig.Max_value_X:
                        continue
                    # if int(position) == 1: #对A相机的画面的截断（与B相机的点重合）
                    #     if worldx > 779 + 0:
                    #         continue
                    # if int(position) == 2: #对C相机的画面的截断（与B相机的点重合）
                    #     if worldx < 1463 - 0:
                    #         continue
                    # 点的等级 -- 非兼容
                    # 队列 1-异纤优先、2-色绒优先、3-脏绒（羊屎）、4-异纤常规、5-色绒常规
                    bool_score = float(data_score[i_point]) > self.list_zh1[data_label[i_point]][0][1]
                    bool_area = point_area > self.list_zh1[data_label[i_point]][1][1]
                    if data_label[i_point] == "yixian":
                        if bool_score and bool_area:
                            point_level = 1
                        else:
                            point_level = 4
                    elif data_label[i_point] == "serong" or data_label[i_point] == "zangmian":
                        if bool_score and bool_area:
                            point_level = 2
                        else:
                            point_level = 5
                    else:
                        if bool_score and bool_area:
                            point_level = 3
                        else:
                            continue

                    map = {"position": position, "label": data_label[i_point], "score": data_score[i_point],
                           "level": point_level, "x": x, "y": y, "worldX": abs(worldx), "worldY": abs(worldy),
                           "x_min": data_point[i_point][0], "x_max": data_point[i_point][2],
                           "y_min": data_point[i_point][1], "y_max": data_point[i_point][3]}
                    self.ai_point_record.ai_first_filtrate += 1  # 计数 AI 初步筛选的点
                    self.num_point[2] += 1
                    arr.append(map)
        return arr  # [] or [{},{}]


# --------------抓手--消费者--------------------
    '''消费者部分'''
    def consume_claw_injection1(self): #消费者-抓手模块

        #06-08 假设喷气频率0.2s
        self.bool_check_process_PLC = False
        arm_ctrl = aiCottonConfig.ARM_number
        # label_list1=[PLC通讯心跳, 监测传送带速度, 读取是否需要暂停, 清空所有队列]
        label_list1 = [0, 0, 0, 0]  # 计数保存位置
        plc_ctrl_list = aiCottonConfig.PLC_ctrl_choose
        if plc_ctrl_list[2] == 1:
            self.num_claw_state = 4  # 抓手个数
        else:
            self.num_claw_state = 2
        zhua_a = 0
        x_limit_list = aiCottonConfig.speed_to_x_list
        x_speed_list = aiCottonConfig.speed_PLC_X
        # self.bool_xfz = True
        print("进入消费者")
        while True:
            try:
                '''  '''
                time.sleep(0.001)
                t5 = time.time()
                if self.if_need_stop == 0:  # PLC控制待机 0-待机，1-正常运行
                    if self.photo_n != label_list1[3]:  # 此时 self.photo_n 不会增加
                        self.num_point[8] += self.count_queue_num()  # 清空队列前，所有队列中剩余的点个数

                        #  清空所有队列
                        for iq in range(3):
                            self.queue_first[iq].queue.clear()
                            self.queue_second[iq].queue.clear()
                            self.queue_third[iq].queue.clear()
                            self.queue_fourth[iq].queue.clear()
                            self.queue_fifth[iq].queue.clear()
                        label_list1[3] = copy.deepcopy(self.photo_n)
                    time.sleep(1)
                    continue
                    pass
                if self.photo_n % 30 == 29:
                    if self.photo_n != label_list1[0]:  #当在29计数时间段内，确保指执行1次
                        self.bool_circulation_process_PLC = True  #PLC通讯心跳
                        label_list1[0] = copy.deepcopy(self.photo_n)
                    # self.bool_ctrl_stop = True  # 读取是否需要暂停
                elif self.photo_n % 100 == 99:
                    if self.photo_n != label_list1[1]:
                        self.bool_get_speed_PLC = True  # 监测传送带速度
                        label_list1[1] = copy.deepcopy(self.photo_n)
                elif self.photo_n % 15 == 5:
                    if self.photo_n != label_list1[2]:
                        self.bool_ctrl_stop = True  # 读取是否需要暂停
                        label_list1[2] = copy.deepcopy(self.photo_n)

                if self.choose_claw_go_back():  # 抓手回零判定
                    continue


                '''读取+判断 抓手状态'''
                while self.bool_send_toPLC_claw:  # 等上一次的发送成功后，或上次无发送
                    time.sleep(0.001)
                self.list_claw_state = []  # 清空上一次的抓手状态
                # while zhua_a == 0:
                t4 = time.time()
                self.bool_read_claw_state = True  #  读取+判断 抓手状态
                while len(self.list_claw_state) < 1:
                    time.sleep(0.001)
                # 是否需要屏蔽抓手
                if not aiCottonConfig.Bool_use_claw:  # Bool_use_claw = True 时正常
                    self.list_claw_state = aiCottonConfig.List_claw_statu
                # print("消费者---读取抓手状态 time:{}".format(time.time() - t4))
                # print("消费者---抓手状态:{}".format(self.list_claw_state))
                if self.list_claw_state[0] == 0 and self.list_claw_state[1] == 0 and not self.judge_empty_first_queue():
                    zhua_a = 1  # 进入抓手1比较部分
                elif self.list_claw_state[2] == 0 and self.list_claw_state[3] == 0 and not self.judge_empty_second_queue():
                    zhua_a = 2  # 进入抓手2比较部分
                elif self.list_claw_state[4] == 0 and self.list_claw_state[5] == 0 and not self.judge_empty_third_queue():
                    zhua_a = 3  # 进入抓手3比较部分
                elif self.list_claw_state[6] == 0 and self.list_claw_state[7] == 0 and not self.judge_empty_third_queue():
                    zhua_a = 4  # 进入抓手4比较部分
                else:
                    zhua_a = 0  # 进入休眠判断
                    time.sleep(0.1)
                    continue
                #  选择判断--取队列
                if zhua_a != 0:  # 锁定抓手1/2/3/4（起码有一个抓手空闲且对应队列有值）
                    point_record = self.choose_point1(zhua_a)
                    print("---消费者---此次循坏到此刻的：{}".format(time.time() - t5))
                    print("---消费者---取到队列时间：{}".format(time.time()- point_record.get("start_time") ))
                    if point_record is None:
                        logger.info("all record queue are empty, we can sleep")
                        time.sleep(0.5)
                        continue
                    start_time = point_record.get("start_time")  # 拍照时刻的点的时间戳(arm:s)
                    speed_bmq1 = point_record.get("speed")  # -----传送带速度#----mm/s
                    x = point_record.get("worldX")
                    y = point_record.get("worldY")
                    print("---消费者---进入抓手判断 zhua_a：{}".format(zhua_a))
                    if zhua_a == 1:
                        x += aiCottonConfig.X1_LEN1
                        y += aiCottonConfig.Y1_LEN1
                        lt1 = aiCottonConfig.T1_LEN1  # 抓手下抓的过程时间--需要在总时间内扣除
                        if x < x_limit_list[0]:
                            current_speed_x = x_speed_list[0]
                        elif x > x_limit_list[1]:
                            current_speed_x = x_speed_list[2]
                        else:
                            current_speed_x = x_speed_list[1]
                        will_time1 = abs(2200 - x) / current_speed_x + 0.1 # 抓手从空闲位到抓到异纤的预测时间,s
                        will_length = speed_bmq1 * will_time1  # 预计抓手移动需要的时间 mm
                        spend_time = time.time() - start_time
                        print("----@@@@@@@@消费者---抓手1---预判时间戳：{}---#################".format(time.time()))
                        spend_length = speed_bmq1 * spend_time  # 传送带速度*时间=# 传送带走的距离
                        print("---消费者---抓手判断 ：{}".format(["time:", spend_time, y,  "-",  lt1 * speed_bmq1, "=",will_length,spend_length]))
                        if float(spend_length + will_length) < y - lt1 * speed_bmq1:  # 此时，传送带未走到位，才有抓到的条件
                            print("---消费者---进入抓手1,计算时间戳")
                            self.bool_read_plc_time_1 = True  # 读取PLC时间戳
                            while self.bool_read_plc_time_1:
                                time.sleep(0.001)
                            print("----@@@@@@@@消费者---获取PLC时间戳(结束)   ：{}".format(time.time()))
                            end_time = self.time_plc + (
                                        y / speed_bmq1 - aiCottonConfig.T1_LEN1 - (self.time_arm - start_time)) * 1000
                            sec, mill_sec = long2time(end_time)  # 毫秒转时间
                            print(
                                "----抓手1运算此点时，点走过的路程：{}mm, \n抓手1计划的时间对应的路程: {}mm".format(spend_length, will_length))
                            self.send_toPLC_list = [zhua_a, int(sec), int(mill_sec), int(x)]
                            self.bool_send_toPLC_claw = True
                            self.num_point[5] += 1  # 抓取ok次数
                            self.ai_point_record.use_1claw_OK += 1  # 抓手1 抓取OK
                            if point_record["level"] == 1:
                                self.ai_point_record.use_1claw_OK_1 += 1  # 抓手1 抓取OK 异纤 优先
                            elif point_record["level"] == 2:
                                self.ai_point_record.use_1claw_OK_2 += 1  # 抓手1 抓取OK  -其他异常点
                            else:
                                self.ai_point_record.use_1claw_OK_3 += 1  # 抓手1 抓取OK  -异纤 疑似
                            self.ai_point_record.grab1_gohome_count += 1
                            list_point = [point_record.get("id_tp"), point_record.get("id_pic"),
                                          point_record.get("speed"), point_record.get("x_max"),
                                          point_record.get("y_max"), point_record.get("x_min"),
                                          point_record.get("y_min"), point_record.get("worldX"),
                                          point_record.get("worldY"), 4, point_record.get("label"),
                                          point_record.get("score"), point_record.get("level")]
                            # write_mysql(list_point)
                            if not self.sql_point_queue.full():
                                self.sql_point_queue.put(list_point)
                            continue
                        point_record["times_judge"] += 1
                        self.put_into_second(point_record)
                        # self.put_into_third(point_record)
                    if zhua_a == 2:
                        x += aiCottonConfig.X2_LEN1
                        y += aiCottonConfig.Y2_LEN1
                        lt1 = aiCottonConfig.T2_LEN1  # 抓手下抓的过程时间--需要在总时间内扣除
                        if x < x_limit_list[0]:
                            current_speed_x = x_speed_list[0]
                        elif x > x_limit_list[1]:
                            current_speed_x = x_speed_list[2]
                        else:
                            current_speed_x = x_speed_list[1]
                        will_time1 = abs(2200 - x) / current_speed_x + 0.1  # 抓手从空闲位到抓到异纤的预测时间,s
                        will_length = speed_bmq1 * will_time1  # 预计抓手移动需要的时间 mm
                        spend_time = time.time() - start_time
                        spend_length = speed_bmq1 * spend_time  # 传送带速度*时间=# 传送带走的距离
                        print("---消费者---抓手判断 ：{}".format(
                            ["time:", spend_time, y, "-", lt1 * speed_bmq1, "=", will_length, spend_length]))
                        if float(spend_length + will_length) < y - lt1 * speed_bmq1:  # 此时，传送带未走到位，才有抓到的条件
                            print("---消费者---进入抓手2,计算时间戳")
                            self.bool_read_plc_time_1 = True
                            while self.bool_read_plc_time_1:
                                time.sleep(0.001)

                            end_time = self.time_plc + (
                                    y / speed_bmq1 - aiCottonConfig.T2_LEN1 - (self.time_arm - start_time)) * 1000
                            sec, mill_sec = long2time(end_time)  # 毫秒转时间
                            logger4.info(
                                "----抓手2运算此点时，点走过的路程：{}mm, \n抓手2计划的时间对应的路程: {}mm".format(spend_length, will_length))
                            self.send_toPLC_list = [zhua_a, int(sec), int(mill_sec), int(x)]
                            self.bool_send_toPLC_claw = True
                            self.num_point[5] += 1  # 点舍去计数
                            self.ai_point_record.use_2claw_OK += 1  # 抓手2 抓取OK
                            if point_record["level"] == 1:
                                self.ai_point_record.use_2claw_OK_1 += 1  # 抓手2 抓取OK 异纤 优先
                            elif point_record["level"] == 2:
                                self.ai_point_record.use_2claw_OK_2 += 1  # 抓手2 抓取OK  -其他异常点
                            else:
                                self.ai_point_record.use_2claw_OK_3 += 1  # 抓手2 抓取OK  -异纤 疑似
                            self.ai_point_record.grab2_gohome_count += 1
                            list_point = [point_record.get("id_tp"), point_record.get("id_pic"),
                                          point_record.get("speed"), point_record.get("x_max"),
                                          point_record.get("y_max"), point_record.get("x_min"),
                                          point_record.get("y_min"), point_record.get("worldX"),
                                          point_record.get("worldY"), 4, point_record.get("label"),
                                          point_record.get("score"), point_record.get("level")]
                            # write_mysql(list_point)
                            if not self.sql_point_queue.full():
                                self.sql_point_queue.put(list_point)
                            if point_record.get("times_judge") > 0:
                                self.ai_point_record.use_2claw_OK_assit_all += 1  # 抓手2 抓取OK 从次队列拿到的点
                                if point_record["level"] == 1:
                                    self.ai_point_record.use_2claw_OK_assit_1 += 1  # 抓手2 抓取OK 从次队列拿到的点 异纤 优先
                                elif point_record["level"] == 2:
                                    self.ai_point_record.use_2claw_OK_assit_2 += 1  # 抓手2 抓取OK 从次队列拿到的点 其他异常点
                                else:
                                    self.ai_point_record.use_2claw_OK_assit_3 += 1  # 抓手2 抓取OK 从次队列拿到的点 -异纤 疑似
                                self.times_queue2 += 1
                                logger4.info("抓手2使用次队列点数据成功，{}次".format(self.times_queue2))
                        else:
                            logger4.info("2-----由于超出极限，抓手把该点存入第3队列")
                            point_record["times_judge"] += 1
                            self.put_into_third(point_record)
                            # self.num_point[6] += 1

                    if zhua_a == 3:
                        x += aiCottonConfig.X3_LEN1
                        y += aiCottonConfig.Y3_LEN1
                        lt1 = aiCottonConfig.T3_LEN1  # 抓手下抓的过程时间--需要在总时间内扣除
                        if x < x_limit_list[0]:
                            current_speed_x = x_speed_list[0]
                        elif x > x_limit_list[1]:
                            current_speed_x = x_speed_list[2]
                        else:
                            current_speed_x = x_speed_list[1]
                        will_time1 = abs(2300 - x) / current_speed_x + 0.1 # 抓手从空闲位到抓到异纤的预测时间,s
                        will_length = speed_bmq1 * will_time1  # 预计抓手移动需要的时间 mm
                        spend_time = time.time() - start_time
                        print("----@@@@@@@@消费者---抓手3---预判时间戳：{}---#################".format(time.time()))
                        spend_length = speed_bmq1 * spend_time  # 传送带速度*时间=# 传送带走的距离
                        print("---消费者---抓手判断 ：{}".format(["time:", spend_time, y,  "-",  lt1 * speed_bmq1, "=",will_length,spend_length]))
                        if float(spend_length + will_length) < y - lt1 * speed_bmq1:  # 此时，传送带未走到位，才有抓到的条件
                            print("---消费者---进入抓手3,计算时间戳")
                            self.bool_read_plc_time_2 = True
                            while self.bool_read_plc_time_2:
                                time.sleep(0.001)

                            end_time = self.time_plc + (
                                    y / speed_bmq1 - aiCottonConfig.T3_LEN1 - (self.time_arm - start_time)) * 1000
                            sec, mill_sec = long2time(end_time)  # 毫秒转时间
                            print(
                                "----抓手3运算此点时，点走过的路程：{}mm, \n抓手3计划的时间对应的路程: {}mm".format(spend_length, will_length))
                            self.send_toPLC_list = [zhua_a, int(sec), int(mill_sec), int(x)]
                            self.bool_send_toPLC_claw = True
                            self.num_point[5] += 1  # 点舍去计数
                            self.ai_point_record.use_3claw_OK += 1  # 抓手3 抓取OK
                            if point_record["level"] == 1:
                                self.ai_point_record.use_3claw_OK_1 += 1  # 抓手3 抓取OK 异纤 优先
                            elif point_record["level"] == 2:
                                self.ai_point_record.use_3claw_OK_2 += 1  # 抓手3 抓取OK  -其他异常点
                            else:
                                self.ai_point_record.use_3claw_OK_3 += 1  # 抓手3 抓取OK  -异纤 疑似
                            self.ai_point_record.grab3_gohome_count += 1
                            list_point = [point_record.get("id_tp"), point_record.get("id_pic"),
                                          point_record.get("speed"), point_record.get("x_max"),
                                          point_record.get("y_max"), point_record.get("x_min"),
                                          point_record.get("y_min"), point_record.get("worldX"),
                                          point_record.get("worldY"), 4, point_record.get("label"),
                                          point_record.get("score"), point_record.get("level")]
                            # write_mysql(list_point)
                            if not self.sql_point_queue.full():
                                self.sql_point_queue.put(list_point)
                            if point_record.get("times_judge") > 1:
                                self.ai_point_record.use_3claw_OK_assit_all += 1  # 抓手3 抓取OK 从3队列拿到的点
                                if point_record["level"] == 1:
                                    self.ai_point_record.use_3claw_OK_assit_1 += 1  # 抓手3 抓取OK 从3队列拿到的点 异纤 优先
                                elif point_record["level"] == 2:
                                    self.ai_point_record.use_3claw_OK_assit_2 += 1  # 抓手3 抓取OK 从3队列拿到的点 其他异常点
                                else:
                                    self.ai_point_record.use_3claw_OK_assit_3 += 1  # 抓手3 抓取OK 从3队列拿到的点 -异纤 疑似
                        else:
                            logger4.info("3-----由于超出极限，抓手把该点抛掉")
                            self.num_point[6] += 1  # 点舍去计数
                            self.ai_point_record.use_3claw_check_NG += 1  # 抓手3 舍去 -总
                            if point_record["level"] == 1:
                                self.ai_point_record.use_3claw_check_NG_1 += 1  # 抓手3 舍去  -异纤 优先
                            elif point_record["level"] == 2:
                                self.ai_point_record.use_3claw_check_NG_2 += 1  # 抓手3 舍去  -其他异常点
                            else:
                                self.ai_point_record.use_3claw_check_NG_3 += 1  # 抓手3 舍去  -异纤 疑似
                            list_point = [point_record.get("id_tp"), point_record.get("id_pic"),
                                          point_record.get("speed"), point_record.get("x_max"),
                                          point_record.get("y_max"), point_record.get("x_min"),
                                          point_record.get("y_min"), point_record.get("worldX"),
                                          point_record.get("worldY"), 5, point_record.get("label"),
                                          point_record.get("score"), point_record.get("level")]
                            # write_mysql(list_point)
                            if not self.sql_point_queue.full():
                                self.sql_point_queue.put(list_point)
                    if zhua_a == 4:
                        x += aiCottonConfig.X4_LEN1
                        y += aiCottonConfig.Y4_LEN1
                        lt1 = aiCottonConfig.T4_LEN1  # 抓手下抓的过程时间--需要在总时间内扣除
                        if x < x_limit_list[0]:
                            current_speed_x = x_speed_list[0]
                        elif x > x_limit_list[1]:
                            current_speed_x = x_speed_list[2]
                        else:
                            current_speed_x = x_speed_list[1]
                        will_time1 = abs(2200 - x) / current_speed_x + 0.1 # 抓手从空闲位到抓到异纤的预测时间,s
                        will_length = speed_bmq1 * will_time1  # 预计抓手移动需要的时间 mm
                        spend_time = time.time() - start_time
                        spend_length = speed_bmq1 * spend_time  # 传送带速度*时间=# 传送带走的距离
                        print("---消费者---抓手判断 ：{}".format(
                            ["time:", spend_time, y, "-", lt1 * speed_bmq1, "=", will_length, spend_length]))
                        if float(spend_length + will_length) < y - lt1 * speed_bmq1:  # 此时，传送带未走到位，才有抓到的条件
                            print("---消费者---进入抓手4,计算时间戳")
                            self.bool_read_plc_time_2 = True
                            while self.bool_read_plc_time_2:
                                time.sleep(0.001)

                            end_time = self.time_plc + (
                                    y / speed_bmq1 - aiCottonConfig.T4_LEN1 - (self.time_arm - start_time)) * 1000
                            sec, mill_sec = long2time(end_time)  # 毫秒转时间
                            print(
                                "----抓手4运算此点时，点走过的路程：{}mm, \n抓手4计划的时间对应的路程: {}mm".format(spend_length, will_length))
                            self.send_toPLC_list = [zhua_a, int(sec), int(mill_sec), int(x)]
                            self.bool_send_toPLC_claw = True
                            self.num_point[5] += 1  # 点舍去计数
                            self.ai_point_record.use_4claw_OK += 1  # 抓手4 抓取OK
                            if point_record["level"] == 1:
                                self.ai_point_record.use_4claw_OK_1 += 1  # 抓手4 抓取OK 异纤 优先
                            elif point_record["level"] == 2:
                                self.ai_point_record.use_4claw_OK_2 += 1  # 抓手4 抓取OK  -其他异常点
                            else:
                                self.ai_point_record.use_4claw_OK_3 += 1  # 抓手4 抓取OK  -异纤 疑似
                            self.ai_point_record.grab4_gohome_count += 1
                            list_point = [point_record.get("id_tp"), point_record.get("id_pic"),
                                          point_record.get("speed"), point_record.get("x_max"),
                                          point_record.get("y_max"), point_record.get("x_min"),
                                          point_record.get("y_min"), point_record.get("worldX"),
                                          point_record.get("worldY"), 4, point_record.get("label"),
                                          point_record.get("score"), point_record.get("level")]
                            # write_mysql(list_point)
                            if not self.sql_point_queue.full():
                                self.sql_point_queue.put(list_point)
                            if point_record.get("times_judge") > 1:
                                self.ai_point_record.use_4claw_OK_assit_all += 1  # 抓手4 抓取OK 从3队列拿到的点
                                if point_record["level"] == 1:
                                    self.ai_point_record.use_4claw_OK_assit_1 += 1  # 抓手4 抓取OK 从3队列拿到的点 异纤 优先
                                elif point_record["level"] == 2:
                                    self.ai_point_record.use_4claw_OK_assit_2 += 1  # 抓手4 抓取OK 从3队列拿到的点 其他异常点
                                else:
                                    self.ai_point_record.use_4claw_OK_assit_3 += 1  # 抓手4 抓取OK 从3队列拿到的点 -异纤 疑似
                        else:

                            logger4.info("4-----由于超出极限，抓手把该点抛掉")
                            self.num_point[6] += 1  # 点舍去计数
                            self.ai_point_record.use_4claw_check_NG += 1  # 抓手4 舍去 -总
                            if point_record["level"] == 1:
                                self.ai_point_record.use_4claw_check_NG_1 += 1  # 抓手4 舍去  -异纤 优先
                            elif point_record["level"] == 2:
                                self.ai_point_record.use_4claw_check_NG_2 += 1  # 抓手4 舍去  -其他异常点
                            else:
                                self.ai_point_record.use_4claw_check_NG_3 += 1  # 抓手4 舍去  -异纤 疑似
                            list_point = [point_record.get("id_tp"), point_record.get("id_pic"),
                                          point_record.get("speed"), point_record.get("x_max"),
                                          point_record.get("y_max"), point_record.get("x_min"),
                                          point_record.get("y_min"), point_record.get("worldX"),
                                          point_record.get("worldY"), 5, point_record.get("label"),
                                          point_record.get("score"), point_record.get("level")]
                            # write_mysql(list_point)
                            if not self.sql_point_queue.full():
                                self.sql_point_queue.put(list_point)

                # else:
                #     print("判定抓手{}状态为：{}".format(zhua_a, self.list_claw_state))
                #     time.sleep(0.6)



            except Exception as e:
                logger.error(f"consume_claw_injection1  err: {e}")
                time.sleep(1)
    '''2021-07-15  开线程使用数据库'''
    def use_thread_sql1(self):
        th1_sql = threading.Thread(target=self.write_point_to_mysql, args=(), name="write_point_to_mysql")
        th1_sql.start()

    '''2021-06-29'''
    def write_point_to_mysql(self):
        while True:
            try:
                if self.sql_point_queue.empty():
                    time.sleep(1)
                else:
                    point_list1 = self.sql_point_queue.get()
                    write_mysql(point_list1)
                    time.sleep(0.001)
            except Exception as e:
                logger.error(f"sql_write_point  err: {e}")
                time.sleep(1)

    '''2021-06-08 存入第二梯队'''
    def put_into_second(self, point_record1):
        # print("---消费者---存入第二队列")
        if point_record1["level"] == 1:
            num_OK, num_NG = self.real_put_point_record(self.queue_first[1], point_record1, "异纤优先-第二梯队")
        elif point_record1["level"] == 2:
            num_OK, num_NG = self.real_put_point_record(self.queue_second[1], point_record1, "色绒优先-第二梯队")
        elif point_record1["level"] == 3:
            num_OK, num_NG = self.real_put_point_record(self.queue_third[1], point_record1, "脏绒+羊屎-第二梯队")
        elif point_record1["level"] == 4:
            num_OK, num_NG = self.real_put_point_record(self.queue_fourth[1], point_record1, "异纤常规-第二梯队")
        else:
            num_OK, num_NG = self.real_put_point_record(self.queue_fifth[1], point_record1, "色绒常规-第二梯队")

    '''2021-06-08 存入第三梯队'''
    def put_into_third(self, point_record2):
        # print("---消费者---存入第三队列")
        if point_record2["level"] == 1:
            num_OK, num_NG = self.real_put_point_record(self.queue_first[2], point_record2, "异纤优先-第三梯队")
        elif point_record2["level"] == 2:
            num_OK, num_NG = self.real_put_point_record(self.queue_second[2], point_record2, "色绒优先-第三梯队")
        elif point_record2["level"] == 3:
            num_OK, num_NG = self.real_put_point_record(self.queue_third[2], point_record2, "脏绒+羊屎-第三梯队")
        elif point_record2["level"] == 4:
            num_OK, num_NG = self.real_put_point_record(self.queue_fourth[2], point_record2, "异纤常规-第三梯队")
        else:
            num_OK, num_NG = self.real_put_point_record(self.queue_fifth[2], point_record2, "色绒常规-第三梯队")

    '''抓手重建OP'''
    def choose_claw_go_back(self):
        if self.ai_point_record.grab1_gohome_count >= 500 and self.list_claw_state[3] == 0:
            self.bool_claw_goback = True  # 06-08 发送PLC归零--信号
            self.num_plc_goback = 1  # 06-08 发送PLC归零--抓手编号1-4
            self.ai_point_record.grab1_gohome_count = 0
            logger.info("抓手1---抓手归零位--重建OP")
            return True
        elif self.ai_point_record.grab2_gohome_count >= 500 and self.list_claw_state[1] == 0:
            self.bool_claw_goback = True  # 06-08 发送PLC归零--信号
            self.num_plc_goback = 2  # 06-08 发送PLC归零--抓手编号1-4
            self.ai_point_record.grab2_gohome_count = 0
            logger.info("抓手2---抓手归零位--重建OP")
            return True
        elif self.ai_point_record.grab3_gohome_count >= 500 and self.list_claw_state[7] == 0:
            self.bool_claw_goback = True  # 06-08 发送PLC归零--信号
            self.num_plc_goback = 3  # 06-08 发送PLC归零--抓手编号1-4
            self.ai_point_record.grab3_gohome_count = 0
            logger.info("抓手3---抓手归零位--重建OP")
            return True
        elif self.ai_point_record.grab4_gohome_count >= 500 and self.list_claw_state[5] == 0:
            self.bool_claw_goback = True  # 06-08 发送PLC归零--信号
            self.num_plc_goback = 4  # 06-08 发送PLC归零--抓手编号1-4
            self.ai_point_record.grab4_gohome_count = 0
            logger.info("抓手4---抓手归零位--重建OP")
            return True
        else:
            return False

    '''2021-06-29  统计现在队列上的点 个数'''
    def count_queue_num(self):

        count_list = [0] * 15
        for jq in range(3):
            count_list[jq * 5] = self.queue_first[jq].qsize()
            count_list[jq * 5 + 1] = self.queue_second[jq].qsize()
            count_list[jq * 5 + 2] = self.queue_third[jq].qsize()
            count_list[jq * 5 + 3] = self.queue_fourth[jq].qsize()
            count_list[jq * 5 + 4] = self.queue_fifth[jq].qsize()
        num_all = sum(count_list)
        return num_all

    '''2021-06-24  根据AI返回画图'''
    def draw_pic_for_ai(self,list_draw_ai2):

        ai_result = list_draw_ai2["ai_data_list"]
        if len(ai_result) > 0:  # [[1,{box...}],[2,,{box...}]]
            point_world = {}
            for point_data1 in ai_result:
                path_pic1 = os.path.join(self.save_pic_aipath, point_data1[1]["img_name"])
                data_ai_back = point_data1[1]
                self.draw_ai_need_pic(path_pic1, data_ai_back)

    '''2021-06-24  根据AI返回-单个画图'''
    def draw_ai_need_pic(self,pic_path,data_ai1):  # pic_path =图片路径， data_ai1 = 单张图片的原始点信息
        point_data_ori = data_ai1  # 点数据，原始
        point_box = point_data_ori["boxes"]  # [[a,b,c,d],[e,f,g,h]]
        if len(point_box) > 0:
            # print("开始画图:{}".format(pic_path))
            image_ori = pic_path  # 图片路径
            path_ = image_ori.split("/")[-1]
            img = cv2.imread(image_ori)  # 读出图片
            point_score = point_data_ori[
                "scores"]  # [0.7993741035461426, 0.6471705436706543, 0.4785524904727936, 0.4358397126197815]
            point_label = point_data_ori[
                "labels"]  # ['kongqiangmao', 'kongqiangmao', 'shenhuangmao', 'kongqiangmao']
            for j in range(len(point_box)):
                label_, score_, x_min, y_min, x_max, y_max = point_label[j], point_score[j], \
                                                             point_box[j][0], point_box[j][1], \
                                                             point_box[j][2], point_box[j][3]
                self.plot_one_box(img, [x_min, y_min, x_max, y_max], label=str(label_) + "|" + str(score_))
            cv2.imwrite(os.path.join(self.havebox_path, path_), img)
            # logger.info("havebox:{}".format(os.path.join(self.havebox_path, path_)))

    '''画框'''
    def plot_one_box(self, img, coord, label=None, color=None, line_thickness=None):
        '''
        coord: [x_min, y_min, x_max, y_max] format coordinates.
        img: img to plot on.
        label: str. The label name.
        color: int. color index.
        line_thickness: int. rectangle line thickness.
        '''
        tl = line_thickness or int(round(0.002 * max(img.shape[0:2])))  # line thickness
        # color = color or [random.randint(0, 255) for _ in range(3)]
        c1, c2 = (int(coord[0]), int(coord[1])), (int(coord[2]), int(coord[3]))
        cv2.rectangle(img, c1, c2, color, thickness=3)  # thickness=tl
        if label:
            tf = max(tl - 1, 1)  # font thickness
            t_size = cv2.getTextSize(label, 0, fontScale=float(tl) / 3, thickness=tf)[0]
            c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
            # cv2.rectangle(img, c1, c2, color, -1)  # filled
            # cv2.rectangle(img, c1, c2, color ,thickness=0)  # filled#label的框
            # cv2.putText(img, label, (c1[0], c1[1] - 2), 0, float(tl) / 3, color, thickness=tf, lineType=cv2.LINE_AA)
            cv2.putText(img, label, (c1[0], c1[1] - 2), cv2.FONT_HERSHEY_COMPLEX, float(tl) / 3, color, thickness=3,
                        lineType=cv2.LINE_AA)

    '''2021-07-05  拍照函数'''
    def take_pic_func1(self,num):
        t3 = time.time()
        result1 = self.cameraModel.takePic()
        print("第{}次拍照，用时：{}".format(num, round(time.time() - t3 , 3)))
        return result1

    '''2021-07-30---增加老版本的生产者相关函数'''

    '''初始化相机'''
    def initCamera(self):
        """
        初始化相机参数，启动相机捕捉画面
        :return 是否全部初始化成功
        """
        logger.info("初始化相机")
        isAllCameraInited = True
        cameraCtrlList = []
        i = 0
        for deviceItem in aiCottonConfig.CAMERA_DEVICE_TUPLE:  # 相机设备元组
            i += 1
            logger.info('deviceItem start: {}'.format(deviceItem))
            camera_map = {}
            if aiCottonConfig.CAMERA_ON and self.cameraCtrlList.get("deviceItem", None) is None:
                self.oCtrl1[i - 1] = tiscamera_ctrl(aiCottonConfig.CAMERA_CTRL_WIDTH,
                                                    aiCottonConfig.CAMERA_CTRL_HEIGHT)  # 某个相机实例
                camera_map["instance"] = self.oCtrl1[i - 1]
                camera_map["status"] = "inactive"
                self.cameraCtrlList[deviceItem] = camera_map
                logger.info('tiscamera_ctrl func end %s', deviceItem)
                bResult = self.oCtrl1[i - 1].open_device(deviceItem, self)  # 打开相机设备，调用函数，返回False
                logger.info('open_device finished %s', deviceItem)
                if bResult:
                    logger.info('open_device successful %s', deviceItem)
                    bResult = self.oCtrl1[i - 1].start_capture()  # 开始拍摄，准备好就返回true
                    logger.info('{} start_capture {}'.format(deviceItem, bResult))
                    if not bResult:
                        isAllCameraInited = False
                        break
                else:
                    isAllCameraInited = False
                    break
                self.set_camera_param(self.oCtrl1[i - 1], deviceItem)  # 设置某个相机（实例及标号）#刷入相机取像参数
                camera_map["status"] = "active"
                self.cameraCtrlList[deviceItem] = camera_map
                cameraCtrlList.append(self.oCtrl1[i - 1])  # 都添加到相机列表
        logger.info('cameraCtrlList {}'.format(cameraCtrlList))
        # end for

        return isAllCameraInited  # 相机已经准备好

    '''老版本自检'''

    def check_takepic_ai_old(self):
        bool_light = True
        bool_del_aimodel = False
        try:
            logger.info("----------开始自检----------")
            '''相机模块自检'''
            logger.info("-----等待相机模块加载完成")

            time.sleep(2)
            logger.info("-----Camera部分自检")
            num_light = 0
            while bool_light:
                for num in range(1, 4):

                    image_path = self.generate_path(str(num))  # 返回图片存放路径，组
                    self._count_down_latch = count_down_latch(len(aiCottonConfig.CAMERA_DEVICE_TUPLE))
                    bResult, camid = self.take_photo(image_path)
                    if not bResult:
                        logger.info("相机拍照超时，take photo timeout!")
                        logger.info("请检查相机ID  触发参数")
                        self.num_camera_err = 11
                        self.bool_camera_err = True

                    else:
                        '''相机对应的光源检测'''
                        logger.info("-----相机对应的光源检测")
                        for key in self.cameraCtrlListDic:
                            value_grey1 = find_grey_value(self.cameraCtrlListDic[key])
                            logger.info("图片：{}---灰度值为：{}".format(key, value_grey1))
                            if value_grey1 is None:
                                logger.info("{}:读取图片或运算失败".format(key))
                            else:
                                if value_grey1 < 98:
                                    bool_light = True
                                    logger.info("{}:图片亮度过低".format(key))
                                    break
                                else:
                                    bool_light = False
                                    logger.info("{}:图片亮度正常".format(key))
                        if not bool_light:
                            logger.info("所有相机图片亮度正常，光源检测ok")
                            break
                        else:
                            self.num_camera_err = 33
                            self.bool_camera_err = True
                            time.sleep(3)
                if num_light == 3 and bool_light:
                    logger.info("相机拍照故障或光源异常，系统退出")
                    os._exit(0)

                '''AI模块自检————调用ai识别'''
                logger.info("-----AI服务部分自检")
                ai_result = {}
                ai_status = True
                reties = 3
                # logger.info("cameraCtrlListDic:{}".format(self.cameraCtrlListDic))
                for key in self.cameraCtrlListDic:
                    # logger.info("key:{}".format(key))
                    position = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[key]  # 相机对应的位置
                    res = call_ai_service(self.cameraCtrlListDic[key], 90)  # 调用ai服务，#返回字符串
                    logger.info("AI-res:{}".format(res))
                    while res is None and reties > 0:
                        time.sleep(10)
                        res = call_ai_service(self.cameraCtrlListDic[key], 90)  # 若初始3次内失败，则重新调取
                        reties -= 1
                    if res is None:
                        ai_status = False
                        break
                    ai_result[position] = self.processAiData(res.get("data").get("0"), position)
                    # 返回像素点坐标，相机位置，世界坐标的字典 的列表
                if not ai_status:
                    logger.info('AI 返回为None，AI服务出错')
                    self.num_camera_err = 22
                    self.bool_camera_err = True
                else:
                    logger.info("ai_result ---- {}".format(ai_result))
                    self.num_camera_err = 88
                    self.bool_camera_err = True
                    logger.info("----------完成自检----------")
                if bool_del_aimodel:
                    path1 = "/mnt/data/data/aimodel"
                    name1 = "Awool_yolov3.pb"
                    name2 = "Bwool_yolov3.pb"

                    path_file1 = os.path.join(path1, name1)
                    path_file2 = os.path.join(path1, name2)
                    code1 = "rm -f " + path_file1 + " &"
                    code2 = "rm -f " + path_file2 + " &"
                    if os.path.exists(path_file1):
                        os.system(code1)
                    time.sleep(0.5)
                    if os.path.exists(path_file2):
                        os.system(code2)
                    bool_del_aimodel = False
                    logger.info(
                        "==========removed aimodel --{}".format(time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime())))
                    logger.info("AI原始模型 删除指令已写")
                    time.sleep(1)
        except Exception as e:
            logger.info(f"err---frist_check: {e}")

    def generate_path(self, num_tp):  # 返回图片存放路径，组#（生产者调用）
        camera_path = {}  # 存放相机号对应的路径
        # path_save_date1 = "/mnt/data/data/image_original/img_" + self.date_path1 + "/"
        path_time_Hm1 = time.strftime("%H_%M", time.localtime())
        for deviceItem in aiCottonConfig.CAMERA_DEVICE_TUPLE:  # deviceItem为设备号
            cam_n = self.Camera_MAP[deviceItem]
            relativePath = "%s_%s_%s.jpg" % (cam_n, path_time_Hm1, num_tp)
            if not os.path.exists(self.save_pic_aipath):
                os.makedirs(self.save_pic_aipath)
            path = self.save_pic_aipath + "/" + relativePath
            camera_path[deviceItem] = path

        return camera_path

    '''拍照并等待相机返回'''

    def take_photo(self, cameraCtrlListDic):
        cam_now1 = []
        self.cam_num = []
        self.currentImgCount = 0
        self.cameraCtrlListDic = cameraCtrlListDic
        self.takePhoto()
        bResult = self._count_down_latch.wait_with_timeout(2)  # 超时等待3组
        # print(11)
        for idcam in self.cam_num2:
            # print(22)
            if not idcam in self.cam_num:
                cam_now1.append(idcam)
        return bResult, cam_now1

    '''触发拍照-电平触发-上升沿'''

    def takePhoto(self):
        tp11 = 11
        if tp11 == 1:
            GPIO.output(self.__output_pin, GPIO.HIGH)  # 触发低电平
            time.sleep(0.0001)  # sleep 0.1ms
            GPIO.output(self.__output_pin, GPIO.LOW)  # 触发高电平
        else:
            for i in range(3):
                self.oCtrl1[i].software_trigger()

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

        imageSaveName = self.cameraCtrlListDic.get(astrSerial)  # 返回字典里‘astrSerial’键的值
        if imageSaveName != None:
            # save_pic_1 = time.time()
            isSaveImageSuccess = self.saveImageFile(astrSerial, aoImage, imageSaveName)  # 存图片
            # save_pic_2 = time.time()
            # lt_save_pic = save_pic_2 - save_pic_1
            # print("{} ：{}".format(astrSerial,lt_save_pic))
            # self.currentImgCount += 1
            self._count_down_latch.count_down()
            self.cam_num.append(str(astrSerial))
            # logger5.info("camera: {} isSaveImageSuccess: {} imagePath: {}".format(astrSerial,
            #                                                                      isSaveImageSuccess, imageSaveName))

    '''保存图片(相机调用部分)'''

    def saveImageFile(self, astrSerial, aoImage, asaveImgAddrss):  # 存图片，底行代码
        if aiCottonConfig.MOCK_SAVE_IMAGE:
            time.sleep(aiCottonConfig.MOCK_SAVE_IMAGE_RESULT_TIME)  # sleep时间
            return True
        isSaveImageSuccess = True
        # start = time.time()
        try:
            cv2.imwrite(asaveImgAddrss, aoImage)  # 保存图片名，路径
            isSaveImageSuccess = True
        except Exception as e:
            logger.info("camera %s cv2.imwrite strSaveName:%s, aoImage:%s" % (astrSerial, asaveImgAddrss, aoImage))
            isSaveImageSuccess = False
        return isSaveImageSuccess

    '''生产者--记录数据'''

    def run_produce_old(self):  # 生产者（产生点数据）
        print("进入生产者")
        logger7.info("进入生产者")
        self.bool_check_process_PLC = False
        bool_light = False
        timea1 = time.time()
        time.sleep(2.5)  # 等待自检过程心跳信号完成终止
        photo_m = 0
        num_cam_timeout = 0
        light_alarm_num = 0
        change_model1 = False
        # self.bool_ai_infer += 11
        # if aiCottonConfig.Mechine_function == "claw":
        #     self.choose_mechine_model = 1  # 2021-0607 抓手模式
        # else:
        #     self.choose_mechine_model = 2  # 2021-0607 喷气模式
        # 循环开始
        while True:
            # for i in range(15):
            try:
                time.sleep(0.001)
                if aiCottonConfig.Bool_sleep_produce:
                    time.sleep(aiCottonConfig.Sleep_time_produce)
                '''被PLC暂停后的操作：保持通讯心跳，监测暂停信号的恢复'''
                # print("暂停信号：{}".format(self.if_need_stop))
                # print("传送带速度：{}".format(self.speed2))
                # self.if_need_stop = 1  # 强制为 运行 信号
                # self.speed2 = 500
                if self.if_need_stop == 0:  # PLC控制待机 0-待机，1-正常运行
                    change_model1 = True
                    self.bool_check_process_PLC = True  # 开始和PLC通讯连接信号
                    self.bool_ctrl_stop = True  # 05-21 看是否需要暂停
                    time.sleep(0.6)
                    print("---生产者---PLC通知设备停机-暂停")
                    self.bool_check_process_PLC = False  # 开始和PLC通讯连接信号

                    # 需要清空所有队列 self.record_queue.queue.clear()
                    continue
                '''暂停消除后，等待传送带速度起来'''
                if change_model1:  # 暂停后启动触发读取取值模式
                    change_model1 = False
                    for f_i in range(4):
                        time.sleep(1.5)
                        self.bool_get_speed_PLC = True  # 05-19 获取传送带速度
                    self.bool_get_label_PLC = True  # 重新启动后读取异纤选择类别
                    self.bool_get_batch_PLC = True  # 重新启动后读取 大小批次

                if light_alarm_num > 20:  # 光源连续20次检测低于100
                    self.num_camera_err = 33
                    self.bool_camera_err = True
                    light_alarm_num = 0
                    self.ai_point_record.bool_send_PLC1 = True

                self.photo_n += 1  # 拍照计数
                if self.photo_n > 20000:
                    self.photo_n = 1
                    photo_m += 1
                '''现在的拍照逻辑不需要等待'''

                image_path = self.generate_path(str(self.photo_n))  # 返回图片存放路径，组
                # 拍照
                timea2 = time.time()
                ct1 = round(timea2 - timea1, 4)
                logger.info('第{}次------执行一次拍照的时间为：{} @@@'.format(str(self.photo_n), ct1))
                logger.info("-------@@@@@@点信息状态：{}".format(self.num_point))
                timea1 = time.time()
                # 设置条件变量，3颗相机在都超时限制内返回，为正常拍照
                self._count_down_latch = count_down_latch(len(aiCottonConfig.CAMERA_DEVICE_TUPLE))

                speeedas2 = copy.deepcopy(self.speed2)
                start_time = time.time()
                bResult, camid = self.take_photo(image_path)
                # photo_n += 1  # 拍照计数+1
                # 获取图片超时
                if not bResult:
                    num_cam_timeout += 1
                    self.num_camera_back = 0
                    logger.info("相机拍照超时，take photo timeout!")
                    if num_cam_timeout > 2:
                        num_cam_timeout = 0
                        bool_camera_delay = True
                        self.num_camera_err = 11
                        self.bool_camera_err = True
                        self.ai_point_record.bool_send_PLC1 = True
                        logger.info("相机拍照故障或光源异常，系统退出")
                        time.sleep(1)
                        os._exit(0)
                    time.sleep(0.8)
                    continue
                self.num_camera_back = 0
                num_cam_timeout = 0  # 到这一步证明触发OK
                list_5 = [self.batch_cotton, start_time, 1]
                # id5_take_photo = write_mysql5(list_5)  # 拍照表主键ID
                id5_take_photo = self.photo_n  # 拍照表主键ID
                '''相机对应的光源检测'''
                num_test_light = self.photo_n % 50
                if num_test_light == 1 or bool_light:
                    logger.info("------------------------------------------相机对应的光源检测******")
                    for key in self.cameraCtrlListDic:
                        value_grey1 = find_grey_value(self.cameraCtrlListDic[key])
                        logger.info("图片：{}---灰度值为：{}".format(key, value_grey1))
                        if value_grey1 is None:
                            logger.info("{}:读取图片或运算失败".format(key))
                        else:
                            if value_grey1 < 98:
                                logger.info("{}:图片亮度过低,当前值为{},将不再做AI检测".format(key, value_grey1))
                                bool_light = True
                                light_alarm_num += 1
                                break
                            else:
                                logger.info("{}:图片亮度正常".format(key))
                                bool_light = False
                    if not bool_light:
                        light_alarm_num = 0
                    else:
                        time.sleep(1.1)
                        continue

                # 调用ai识别
                ai_result = {}
                ai_image_result = {}
                ai_status = True
                # res = [self.ai_request_pool.submit(self.process_ai_request, i) for i in self.cameraCtrlListDic]
                for key in self.cameraCtrlListDic:
                    position = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[key]  # 相机对应的位置
                    start_n = time.time()
                    res = call_ai_service(self.cameraCtrlListDic[key])  # 调用ai服务，#返回字符串
                    if res is None:
                        ai_status = False
                        break
                    temp = time.time() - start_n
                    logger2.info("第{}次------------- AI service time: {}".format(str(self.photo_n), temp))
                    logger2.info("ai result is {}".format(res))
                    if len(res.get("data").get("0")["labels"]) > 0:  # 有识别才录入
                        ai_result[position] = self.processAiData(res.get("data").get("0"), position)
                    # logger2.info("12")
                    ai_image_result[key] = [self.cameraCtrlListDic[key], res.get("data").get("0")]  # {相机号:[图片路径,点位信息]}
                    # logger2.info("23")
                if not ai_status:
                    self.num_camera_err = 22
                    self.bool_camera_err = True
                    logger.info('AI 返回为None，AI服务出错')
                    self.ai_point_record.bool_send_PLC1 = True
                    continue
                test_time1 = time.time()
                self.ai_image_result_path = copy.deepcopy(ai_image_result)
                th1 = threading.Thread(target=self.use_threading1, args=(), name="save_ai_image")
                th1.start()
                # self.save_ai_image(ai_image_result)  # 应改为调用线程
                logger.info("第{}次存删图片用时:{}".format(self.photo_n, time.time() - test_time1))

                if len(ai_result) > 0:  # 当转换后的点 存在时
                    point_arr = caculate_nearly_point(ai_result)  # 舍去相机重合点 #走到这一步，必有点
                    if point_arr is not None:
                        # print("the checked result is {}".format(point_arr))
                        # print("start_time:{}  speeedas2:{}".format(start_time, speeedas2))
                        self.num_point[3] += len(point_arr)  # 同步去重后的点数量
                        logger7.info("第{}次，异步去重前-结果：{}".format(self.photo_n, point_arr))
                        datapiont1 = self.remove_point2(point_arr, start_time, speeedas2)
                        # print("@@@@@@@@@@@@@@-----({})---time:{}----speed:{}".format(photo_n,start_time,speeedas2))
                        logger7.info("第{}次，异步去重后-筛选后结果：{}".format(self.photo_n, datapiont1))
                        if datapiont1 is not None:
                            self.put_record2queue(datapiont1, start_time, speeedas2, self.photo_n,
                                                  id5_take_photo)  # 将点写入队列（生产者调用）

                if self.ai_point_record.bool_send_PLC1:
                    self.num_camera_err = 88
                    self.bool_camera_err = True
                    self.ai_point_record.bool_send_PLC1 = False
            except Exception as e:
                logger.error(f"err---produce: {e}")
                time.sleep(0.8)

    '''初始化时-设置相机参数'''
    def set_camera_param(self, oCtrl, sn):  # 实例及标号#（初始化调用）
        if sn == aiCottonConfig.CAMERA_DEVICE_TUPLE[0]:
            oParam = aiCottonConfig.A_CAMERA_PARAMETER  # 相机参数
        elif sn == aiCottonConfig.CAMERA_DEVICE_TUPLE[1]:
            oParam = aiCottonConfig.C_CAMERA_PARAMETER  # 相机参数
        else:
            oParam = aiCottonConfig.B_CAMERA_PARAMETER  # 相机参数
        for strName in oParam:
            strValue = oCtrl.get_property(strName)
            # logger.info("(before)strName--{}  strValue--{}".format(strName, strValue))
            if strValue is not None:
                # 这个相机参数存在
                # if (strName == "Exposure" and sn == "35024012"):
                #     oCtrl.set_property(strName, 3800)
                #     continue
                # logger.info(" oParam[strName] ----- {}".format(oParam[strName]))
                oCtrl.set_property(strName, oParam[strName])
                strValue1 = oCtrl.get_property(strName)
        time.sleep(1)
        for strName in oParam:
            strValue1 = oCtrl.get_property(strName)
            logger.info("(now)strName--{}  strValue--{}".format(strName, strValue1))


    def start_run_4_4(self):
        if aiCottonConfig.If_need_PLC:
            self.connect_plc()  # 连接PLC

        self.frist_check_AI()  # 初始化、自检
        # th1_produce = threading.Thread(target=self.run_produce_AI, args=(), name="run_produce_AI")
        # th1_produce.start()
        th1_produce = threading.Thread(target=self.run_produce_old, args=(), name="run_produce_old")
        th1_produce.start()
        if aiCottonConfig.If_need_PLC:
            # th1_consume = threading.Thread(target=self.consume_gas_injection1, args=(), name="consume_gas_injection1")
            # th1_consume.start()
            th1_consume = threading.Thread(target=self.consume_claw_injection1, args=(), name="consume_claw_injection1")
            th1_consume.start()
            # self.test_send()

    def use_threading1(self):
        self.save_ai_image(self.ai_image_result_path)

    # def save_ai_image(self, data_ai):
    #     if self.havebox_path is not None:
    #         for camera_num, point_data in data_ai.items():
    #             image_ori = point_data[0] #图片路径
    #             path_ = image_ori.split("/")[-1]
    #             img = cv2.imread(image_ori) #读出图片
    #             img_upload = copy.deepcopy(img)
    #             point_data_ori = point_data[1] #点数据，原始
    #             point_box = point_data_ori["boxes"] #[[a,b,c,d],[e,f,g,h]]
    #             remove_path = "rm -f " + image_ori
    #             if len(point_box) > 0:
    #                 point_score = point_data_ori["scores"] # [0.7993741035461426, 0.6471705436706543, 0.4785524904727936, 0.4358397126197815]
    #                 point_label = point_data_ori["labels"]  # ['kongqiangmao', 'kongqiangmao', 'shenhuangmao', 'kongqiangmao']
    #                 for j in range(len(point_box)):
    #                     label_, score_, x_min, y_min, x_max, y_max = point_label[j], point_score[j], \
    #                                                                  point_box[j][0], point_box[j][1], \
    #                                                                  point_box[j][2], point_box[j][3]
    #                     self.plot_one_box(img, [x_min, y_min, x_max, y_max], label=str(label_) + "|" + str(score_))
    #                 cv2.imwrite(os.path.join(self.havebox_path, path_), img)
    #                 cv2.imwrite(os.path.join(self.upload_path, path_), img_upload)
    #             else:
    #                 cv2.imwrite(os.path.join(self.nobox_path, path_), img)
    #             logger.info("remove_path:{}".format(remove_path))
    #             os.system(remove_path)

    def save_ai_image(self, data_ai):  # data_ai={相机号:[图片路径,点位信息],相机号:[图片路径,点位信息],相机号:[图片路径,点位信息]}
        try:
            # self.after_pic_path = {}
            will_judge = []
            if self.havebox_path is not None:
                bool_record1 = 0
                if self.photo_n % 30 == 1:
                    bool_record1 = 1 #控制存入上传的变量

                for camera_num, point_data in data_ai.items():  # 分单张图
                    image_ori = point_data[0]  # 图片路径
                    # print("image_ori",image_ori)
                    path_ = image_ori.split("/")[-1]  # 最后的图片名
                    txt_name1 = path_.replace("jpg", "txt") #点信息txt文件

                    remove_path = "rm -f " + image_ori #删除原始图片路径
                    copy_path_have = "mv -f " + image_ori + " " + self.havebox_path + "/"  #每日刷新havebox 路径
                    copy_path_no = "mv -f " + image_ori + " " + self.nobox_path + "/"  #每日刷新nobox 路径
                    point_data_ori = point_data[1]  # 点数据，原始 #[{},{}]
                    # print("单张图片：{}--{}".format(path_, point_data_ori))

                    if len(point_data_ori) > 0:  # 此图有点信息时
                        # print("copy_path_have",copy_path_have)
                        os.system(copy_path_have) #有点信息的图片直接存havebox/xxxx-日期/图片
                        # ###数据库
                        # list_6 = [tp_id, self.upload_path + path_, start_time1, 1]
                        # id6_pic = write_mysql6(list_6)  # 录入图片表
                        # # print("图片表ID：{}".format(id6_pic))
                        # cam_num1 = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[camera_num]  # 相机号对应简单编号
                        # self.after_pic_path[cam_num1] = id6_pic
                        # 写.txt文件
                        tf1 = open(self.havebox_path + "/" + txt_name1, 'a')

                        list_message1 = []  # 单张图片中的点信息列表
                        # bool_pic_label1 = [True] * len(self.label_path) #单张图中的label是否加过
                        for point_message1 in point_data_ori: #单张图中的每一个点信息
                            if point_message1["score"] >= aiCottonConfig.Classification_threshold:
                                level_point = "havebox"
                            else:
                                level_point = "suspected"
                            # if bool_record1 > 0:
                            #     for i in range(len(self.label_path)): #point -label 计数记录 -需要间隔
                            #         if bool_pic_label1[i] and point_message1["label"] == self.label_path[i]:
                            #             self.list_num_label[i] += 1
                            #             bool_pic_label1[i] = False
                            #             bool_record1 += 1
                            point_re_mess1 = {"leftTopX": point_message1["x_min"], "leftTopY": point_message1["y_min"],
                                              "rightBottomX": point_message1["x_max"], "rightBottomY": point_message1["y_max"],
                                              "labelType": point_message1["label"], "labelMap": {
                                    "level": point_message1["level"],  "score": point_message1["score"]
                                }
                                              }
                            # print("图中的每个点：{}".format(point_re_mess1))
                            list_message1.append(point_re_mess1)
                            # 开始存信息
                        # print("写入文件时的点信息：{}".format(json.dumps(list_message1)))
                        tf1.write(json.dumps(list_message1))
                        tf1.close()
                        # if bool_record1 > 0: #把每隔数次的可用 图片+txt cp 到upload路径
                        #     copy_path_upload = "cp -f " + self.havebox_path + "/" + path_ + " " + self.upload_path + "/"
                        #     copy_path_upload_txt = "cp -f " + self.havebox_path + "/" + txt_name1 + " " + self.upload_path + "/"
                        #     # print("copy_path_upload",copy_path_upload)
                        #     os.system(copy_path_upload)
                        #     # print("copy_path_upload_txt", copy_path_upload_txt)
                        #     os.system(copy_path_upload_txt)
                    else:
                        # print("copy_path_no", copy_path_no)
                        # will_judge.append(path_)
                        os.system(copy_path_no)  # 复制到nobox,不做记录
                        # ###数据库
                        # list_6 = [tp_id, self.nobox_path + path_, start_time1, 0]
                        # id6_pic = write_mysql6(list_6)
                        # # print("图片表ID：{}".format(id6_pic))
                        # cam_num1 = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[camera_num]
                        # self.after_pic_path[cam_num1] = id6_pic
                    # logger.info("remove_path:{}".format(remove_path))
                    # os.system(remove_path)
                # if bool_record1 > 1: #当1次拍照中有有用点产生时，写入计数记录
                #     self.write_record_num_label()
                # if self.num_take_pic % 10 == 1 and self.num_take_pic > 0:
                #     # if len(will_judge) == 3:
                #     logger5.info("第{}次--判别图中的羊毛 --无异纤图片数量：{}".format(self.num_take_pic, len(will_judge)))
                #     self.name_judge_pic = copy.deepcopy(will_judge)
                #     self.bool_judge_pic = True
                #     # th1_pic = threading.Thread(target=self.judge_pic, args=(), name="judge_pic")
                #     # th1_pic.start()
                # logger4.info("存完图片表：返回{}--{}".format(len(self.after_pic_path), self.after_pic_path))
            # return after_pic_path
        except Exception as e:
            logger.info(f"err---saveimage: {e}")


# SIGINT信号处理
def sigint_handler(signum, frame):
    GPIO.cleanup()
    sys.exit(0)


if __name__ == '__main__':
    logging.config.fileConfig('log.conf')
    init_flag = "init.txt"
    if os.path.exists(init_flag):
        os.remove(init_flag)
    # 设置信号处理
    run_or_test1 = 1  # 1：正常运行，非1：测试
    signal.signal(signal.SIGINT, sigint_handler)  # 中断进程
    signal.signal(signal.SIGTERM, sigint_handler)  # 软件终止信号
    if run_or_test1 == 1:
        service = AiHjRunService() #实例化
        try:
            f = open(init_flag, "w+")
            f.write("success")
            f.close()
        except:
            logger.error("write init status error =======")
        service.start_run_4_4()

