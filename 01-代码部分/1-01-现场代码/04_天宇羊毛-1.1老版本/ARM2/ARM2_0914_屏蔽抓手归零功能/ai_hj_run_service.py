# coding=utf-8
import sys
import time
import os
import signal
from concurrent.futures import ThreadPoolExecutor
import copy
import queue
import threading
import logging
import logging.config
import cv2
import json
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!This is probably because you need superuser privileges.")
from count_down_latch import count_down_latch
from image2world import image_points_to_world_plane
from utils import transform_conveyer_speed, time2long, long2time, find_grey_value, call_ai_service, caculate_nearly_point
from utils import write_mysql, write_mysql2, write_mysql3, write_mysql4, write_mysql5, write_mysql6
import config_armz as aiCottonConfig
from point_deal_record import point_record
# from save_take_photo import take_photo_context
# from save_take_photo import save_take_photo
# from save_image_record import image_record_context
# from save_image_record import save_image_record

# 添加包路径
START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, "..", "..", "ai-melsec-ctrl", "python"))
sys.path.append(os.path.join(START_PY_PATH, "..", "..", "ai-device-ctrl", "python"))
sys.path.append(os.path.join(START_PY_PATH, "..", ".."))

del START_PY_PATH
# 需要导入的类
if aiCottonConfig.CAMERA_ON:
    from AIDeviceCtrl.tiscamera_ctrl import tiscamera_ctrl
from AIDeviceCtrl.ai_encoder_device import *
from AIDeviceCtrl.ai_encoder_device import ai_encoder_device
from melsec_ctrl.melsec_ctrl import melsec_ctrl
from base import log
from base.timer_thread import simple_task_thread


logger = logging.getLogger('main')
logger2 = logging.getLogger('remover')
logger4 = logging.getLogger('recorder')
logger5 = logging.getLogger('rtemp')
log.init_log("save_db")
log.info("===================================")


'''
123--high
20200927,对宇新羊毛进行预写（同无锡远纺，1组相机带2套抓手）
20201031，现场测试完成，相机触发和回调，与PLC通讯正常，读取写入都正常
2020_1203,数据库录入（简单版）成功，访问成功，4G ip同网段下 192.168.2.150：8089
'''


class AiHjRunService:

    def __init__(self):
        self.__oPoolForRaster = ThreadPoolExecutor(4, "PoolForRasters")
        self.lock = threading.RLock()#队列线程锁，读写互斥，仅能进行一项
        self.bool_lock_time = False  # 读取PLC时间优先级判断
        self.lock_bmq = threading.Lock()#编码器线程锁
        self.ai_point_record = point_record() #计数对象，引用
        self.fiber_queue = queue.Queue(maxsize=5) #异纤优先队列
        self.hard_yellow_queue = queue.Queue(maxsize=5)  # 深黄毛队列
        self.light_yellow_queue = queue.Queue(maxsize=10)  # 中黄毛队列
        self.fiber_seemingly_queue = queue.Queue(maxsize=5)  # 异纤疑似队列
        # self.record_queue = queue.Queue(maxsize=10) #中黄毛分类队列
        # self.record_queue2 = queue.Queue(maxsize=6)  #中黄毛分类队列 - 次队列
        self.fiber_queue_assit = queue.Queue(maxsize=5) #异纤优先队列 - 次队列
        self.hard_yellow_queue_assit = queue.Queue(maxsize=5)  # 深黄毛队列 - 次队列
        self.light_yellow_queue_assit = queue.Queue(maxsize=6)  # 中黄毛队列 - 次队列
        self.fiber_seemingly_queue_assit = queue.Queue(maxsize=5)  # 异纤疑似队列 - 次队列
        self.currentHomingCount = 0  # 手1抓取次数计数
        self.currentHomingCount2 = 0  # 手2抓取次数计数
        self._melsec_ctrl = melsec_ctrl()
        self._melsec_ctrl_frist = melsec_ctrl()
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
        self.cameraCtrlList = {}  # 摄像机控制器列表
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
        self.speed1max = 0
        self.speed2_K = 147.615 #编码值/mm
        self.speed2 = 0.09295 #单位M/s(覆盖的参数是mm/s)
        self.robot1 = True#抓手1可进行
        self.sleepdown1 = True  #PLC控制，生产者暂停信号
        self.dataZ1 =[]#去重数据组
        self.date_path1 = time.strftime("%Y_%m_%d",time.localtime())
        self.time_trigger = time.time()
        self.num_camera_back = 0
        self.choose_model1 = 0 #默认异纤种类（#0,异纤  1，异纤+脏棉）
        self.list_zh1 = aiCottonConfig.Choose_type
        self.num_yixian1 = 0
        self.num_changeda = 0
        self.bool_xfz = False
        self.Camera_MAP = aiCottonConfig.CAMERA_SAVE_IMAGE
        self.point_start1 = 0  # 总生成点数
        self.point_start2 = 0  # 实际录入点数
        self.point_end1 = 0  # OK点数
        self.point_end2 = 0  # NG点数
        self.keep_time1 = None  # 间断计时
        self.keep_time2 = None  # 间断计时
        self.lt_keep_time = 0  # 间断计时
        self.num_err_record = 0 #异常记录通讯更新标记 12_16
        self.times_queue2 = 0
        self.times_queue2_all = 0
        self.times_queue2_NG = 0
        # 若要处理一些定时任务，比如自动删除旧的数据，需要开启下面定时任务线程
        self.oTaskThread = simple_task_thread("simple_task")
        self.oTaskThread.start()
        # 构造存储t_point_record操作，这个对象可以反复使用，非线程安全
        # self.oSavePointRec = save_point_record()
        # self.oSaveErrRec = save_err()  # 2020_12_16
        self.oCtrl1 = [None, None, None]
        self.ai_request_pool = ThreadPoolExecutor(3, "AIRequestPool")
        self.havebox_path = None
        self.nobox_path = None
        self.upload_path = None
        self.label_path = aiCottonConfig.Choose_type[-1]  # [1,2,3]
        self.batch_cotton = []
        self.ai_image_result_path = ""
        self.real_all_piont_put_2 = 0
        self.cam_num = []
        self.cam_num2 = [aiCottonConfig.CAMERA_DEVICE_TUPLE[0], aiCottonConfig.CAMERA_DEVICE_TUPLE[1], aiCottonConfig.CAMERA_DEVICE_TUPLE[2]]
        self.list_num_label = [0]*len(self.label_path)
        self.num_take_pic = 0
        self.after_pic_path = {}  #2021-06-03 数据库返回图片表主键值
        self.queue_w_sql_tp = queue.Queue(maxsize=10)  #2021-06-03 信号，为True时，执行写入 -拍照表 (要换成队列，有就存写)
        self.queue_w_sql_image = queue.Queue(maxsize=10) #2021-06-03 信号，为True时，执行写入 -图片表
        self.queue_w_sql_point = queue.Queue(maxsize=20) #2021-06-03 信号，为True时，执行写入 -点位表
        self.bool_judge_pic = False   # 2021-06-15 执行有无羊毛的判断
        self.name_judge_pic = []  # 2021-06-15 判断的图片名

    '''开机程序自检--PLC的读取，发送，相机触发拍照，返回，AI的返回'''

    def frist_check(self):
        bool_light = True
        bool_del_aimodel = True
        try:
            logger.info("----------开始自检----------")
            self.mkdir_pic_path1()

            # date_path1 = time.strftime("%Y_%m%d", time.localtime())
            # date_path2 = aiCottonConfig.Path_upload + date_path1
            # if not os.path.exists("/mnt/data/data/image/"):
            #     os.makedirs("/mnt/data/data/image/")
            # if not os.path.exists("/mnt/data/data/image/havebox/"):
            #     os.makedirs("/mnt/data/data/image/havebox/")
            # if not os.path.exists("/mnt/data/data/image/nobox/"):
            #     os.makedirs("/mnt/data/data/image/nobox/")
            # if not os.path.exists("/mnt/data/data/upload_image/"):
            #     os.makedirs("/mnt/data/data/upload_image/")
            # self.havebox_path = "/mnt/data/data/image/havebox/" + date_path1
            # self.nobox_path = "/mnt/data/data/image/nobox/" + date_path1
            # self.upload_path = "/mnt/data/data/upload_image/" + date_path2
            # if not os.path.exists(self.nobox_path):
            #     os.makedirs(self.nobox_path)
            # if not os.path.exists(self.havebox_path):
            #     os.makedirs(self.havebox_path)
            # if not os.path.exists(self.upload_path):
            #     os.makedirs(self.upload_path)
            #
            # for ai1 in range(len(self.list_zh1)):
            #     logger.info("类型{} ：{}".format(ai1, self.list_zh1[ai1]))

            '''PLC的读写'''
            logger.info("-----PLC部分自检")
            # todo 加重试次数，重试全失败，退出程序
            name1 = aiCottonConfig.MELSEC_CODE.ZI_TEST1
            data = [123, 456, 789, 1024]
            name2 = aiCottonConfig.MELSEC_CODE.ZJ_XINHAO
            data2 = [88]
            result1 = self._melsec_ctrl.write_dword_data(name1, data)  # 写入
            if result1 is not None:
                logger.info("数据写入PLC 成功")
                time.sleep(0.3)
                result2 = self._melsec_ctrl.read_dword_data(name1, 4)  # 读取
                if result2 is not None:
                    logger.info("读取PLC 成功")
                    logger.info("PLC起始地址：{}，数据为{}".format(name1, result2))
                    time.sleep(0.3)
                    data = [222, 222, 222, 222]
                    self._melsec_ctrl.write_dword_data(name1, data)  # 写入重置
                    self._melsec_ctrl.write_dword_data(name2, data2)  # 写入重置自检信号位
                else:
                    logger.info("无法读取PLC")
            else:
                logger.info("数据未能写入PLC，请检查原因（IP，端口，集线器模式）")

            '''相机模块自检'''
            logger.info("-----等待相机模块加载完成")
            name3 = aiCottonConfig.MELSEC_CODE.ARM_XINHAO
            time.sleep(2)
            logger.info("-----Camera部分自检")
            num_light = 0
            while bool_light:
                for num in range(1, 4):
                    num_light = num
                    data2 = [self.num_changed1()]
                    self._melsec_ctrl.write_dword_data(name3, data2)
                    image_path = self.generate_path(str(num))  # 返回图片存放路径，组
                    self._count_down_latch = count_down_latch(len(aiCottonConfig.CAMERA_DEVICE_TUPLE))
                    bResult,camid = self.take_photo(image_path)
                    if not bResult:
                        logger.info("相机拍照超时，take photo timeout!")
                        logger.info("请检查相机ID  触发参数")
                        data2 = [11]
                        self.write_signal(data2)
                    else:
                        '''相机对应的光源检测'''
                        logger.info("-----相机对应的光源检测")
                        for key in self.cameraCtrlListDic:
                            value_grey1 = find_grey_value(self.cameraCtrlListDic[key])
                            logger.info("图片：{}---灰度值为：{}".format(key, value_grey1))
                            if value_grey1 is None:
                                logger.info("{}:读取图片或运算失败".format(key))
                            else:
                                if value_grey1 < 101:
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
                            data2 = [33]
                            self.write_signal(data2)
                            time.sleep(3)
                if num_light == 3 and bool_light:
                    logger.info("相机拍照故障或光源异常，系统退出")
                    os._exit(0)


                '''AI模块自检————调用ai识别'''
                logger.info("-----AI服务部分自检")
                ai_result = {}
                ai_status = True
                reties = 3
                for key in self.cameraCtrlListDic:
                    position = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[key]  # 相机对应的位置
                    res = call_ai_service(self.cameraCtrlListDic[key], 90)  # 调用ai服务，#返回字符串
                    while res is None and reties > 0:
                        time.sleep(10)
                        res = call_ai_service(self.cameraCtrlListDic[key], 90) #若初始3次内失败，则重新调取
                        reties -= 1
                    if res is None:
                        ai_status = False
                        break
                    ai_result[position] = self.processAiData(res.get("data").get("0"), position)
                    # 返回像素点坐标，相机位置，世界坐标的字典 的列表
                if not ai_status:
                    logger.info('AI 返回为None，AI服务出错')
                    data2 = [22]
                    self.write_signal(data2)
                else:
                    logger.info("ai_result ---- {}".format(ai_result))
                    data2 = [88]
                    self.write_signal(data2)
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
            time.sleep(0.3)
            os._exit(0)


    def mkdir_pic_path1(self):
        date_path1 = time.strftime("%Y_%m%d", time.localtime()) #当天日期
        date_path2 = aiCottonConfig.Path_upload + date_path1 # 设备编号+ 当天日期
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
        # for x_path in self.label_path:
        #     if not os.path.exists(self.havebox_path + "/" + x_path):
        #         os.makedirs(self.havebox_path + "/" + x_path)
        #     if not os.path.exists(self.upload_path + "/" + x_path):
        #         os.makedirs(self.upload_path + "/" + x_path)
        for ai1 in range(len(self.list_zh1)):
            logger.info("类型{} ：{}".format(ai1, self.list_zh1[ai1])) #现有配置的识别类型
        photo1 = self.generate_path(str(232))
        print(str(photo1))
        #创建或录入--点分类记录
        txt_name1 = self.upload_path + "/point_record_message.txt"
        bool_name_file = os.path.isfile(txt_name1)
        if not bool_name_file: #不存在时，创建txt,并写入000
            logger.info("创建新-点信息记录次数-txt文件")
            tf_1 = open(txt_name1, 'a')
            point_message3 = ""
            for i_label in range(len(self.label_path)):
                point_message3 += self.label_path[i_label] + "," + str(self.list_num_label[i_label]) + ","
            tf_1.write(point_message3)
            tf_1.write("\n")
            tf_1.close()
        else: #文件已存在，说明已经有计数累加记录
            # logger.info("文件已存在：{}".format(2345))
            tf_2 = open(txt_name1, 'r+')
            context1 = tf_2.readlines()
            logger.info("列表长度：{}".format(len(context1)))
            if len(context1) == 0:
                logger.info("文件已存在,但上次写入异常，无字符")
                for i_label in range(len(self.label_path)):
                    self.list_num_label[i_label] = 0  # 取到文件中的次数数据，赋值到列表
                    logger.info("已有-点信息记录次数：{}--{}".format(self.label_path[i_label], self.list_num_label[i_label]))
            else:
                context2 = context1[-1]
                txt1 = context2.replace(" ", "").replace("\n", "")
                txt2 = txt1.split(",")  # 点信息
                for i_label in range(len(self.label_path)):
                    self.list_num_label[i_label] = int(txt2[i_label*2 + 1]) #取到文件中的次数数据，赋值到列表
                    logger.info("已有-点信息记录次数：{}--{}".format(self.label_path[i_label], self.list_num_label[i_label]))

    # ####---------------主函数部分-------------
    '''生产者--记录数据'''
    def run_produce_point_data(self):  # 生产者（产生点数据）
        logger.info("进入生产者")
        bool_light = False
        change_model1 = False
        name3 = aiCottonConfig.MELSEC_CODE.ARM_XINHAO
        timea1 = time.time()
        photo_n = 10
        num_cam_timeout = 0
        light_alarm_num = 0
        logger.info('准备--开机完成信号')
        self.write_sleep_data(2)  # 开机完成信号
        logger.info('准备--获得批次号')
        self.get_batch(False)
        logger.info('准备--读取速度来判定')
        self.judge_speed()  # 读取速度来判定
        logger.info('准备--开机读取异纤选择类别')
        self.read_choose_model()  # 开机读取异纤选择类别

        bool_del_aimodel = True
        # 循环开始
        while True:
            try:
                if not self.sleepdown1:  # PLC控制，待机（消费者传来的参数）
                    change_model1 = True
                    data2 = [self.num_changed1()]
                    self._melsec_ctrl.write_dword_data(name3, data2)  # 写入自检信号位-断连状态
                    time.sleep(2.5)
                    continue
                if change_model1:  # 暂停后启动触发读取取值模式
                    change_model1 = False
                    self.read_choose_model()  # 重新启动后读取异纤选择类别
                    self.get_batch(False) #重新启动后读取 大小批次
                if light_alarm_num > 20:  # 光源连续20次检测低于100
                    data2 = [33]
                    self.write_signal(data2)
                    light_alarm_num = 0
                    self.ai_point_record.bool_send_PLC1 = True
                # if self.record_queue.full():
                #     logger.info('主队列已满')
                '''现在的拍照逻辑不需要等待'''

                image_path = self.generate_path(str(photo_n + 1))  # 返回图片存放路径，组
                # 拍照
                timea2 = time.time()
                ct1 = timea2 - timea1
                logger.info('第{}次------执行一次拍照的时间为：{} @@@'.format(str(photo_n + 1), ct1))
                timea1 = time.time()
                # 设置条件变量，3颗相机在都超时限制内返回，为正常拍照
                self._count_down_latch = count_down_latch(len(aiCottonConfig.CAMERA_DEVICE_TUPLE))

                '''读取PLC的系统时间戳，并转换'''
                # data = self.read_data(0)
                # if data:
                #     start_time = time2long(data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC),
                #                            data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC))
                #     self.speed2 = transform_conveyer_speed(data.get(aiCottonConfig.MELSEC_CODE.CSD_SPEED1))
                # else:
                #     logger.info("read plc system time error")
                #     # self.reconnect_plc()
                #     # logger.info("reconnect plc finished")
                #     time.sleep(2.5)
                #     continue
                if self.speed2 < 50:
                    logger.info("传送带过慢")
                    time.sleep(3)
                    continue
                self.speed1max = max(self.speed1max,self.speed2)
                speeedas2 = copy.deepcopy(self.speed2)
                start_time = time.time()
                bResult,camid = self.take_photo(image_path)
                list_5 = [self.batch_cotton[0] + "-" + self.batch_cotton[1], start_time, 1]
                id5_take_photo = write_mysql5(list_5)  #拍照表主键ID
                print("拍照表主键ID：{}".format(id5_take_photo))
                photo_n += 1  # 拍照计数+1
                self.num_take_pic = photo_n
                # 获取图片超时
                if not bResult:
                    num_cam_timeout += 1
                    self.num_camera_back = 0
                    logger.info("相机拍照超时，take photo timeout!")
                    if num_cam_timeout > 2:
                        num_cam_timeout = 0
                        bool_camera_delay = True
                        data2 = [11]
                        self.write_signal(data2)
                        self.ai_point_record.bool_send_PLC1 = True
                        logger.info("相机拍照故障或光源异常，系统退出")
                        time.sleep(1)
                        os._exit(0)
                    time.sleep(0.8)
                    continue
                self.num_camera_back = 0
                num_cam_timeout = 0  # 到这一步证明触发OK
                '''相机对应的光源检测'''
                num_test_light = photo_n % 50
                if num_test_light == 1 or bool_light:
                    logger.info("------------------------------------------相机对应的光源检测******")
                    for key in self.cameraCtrlListDic:
                        value_grey1 = find_grey_value(self.cameraCtrlListDic[key])
                        logger.info("图片：{}---灰度值为：{}".format(key, value_grey1))
                        if value_grey1 is None:
                            logger.info("{}:读取图片或运算失败".format(key))
                        else:
                            if value_grey1 < 100:
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
                    # logger2.info("第{}次------------- AI service time: {}".format(str(photo_n), temp))
                    # logger4.info("第{}次--ai result is {}".format(str(photo_n), res))
                    #'data': {'0': {'boxes': [[1181.16796875, 1929.2083740234375, 1633.39453125, 2054.791748046875]],
                    # 'scores': [0.7380592226982117], 'labels': ['yixian'], 'class_scores': [], 'img_exist': 1}}
                    ai_result[position] = self.processAiData(res.get("data").get("0"), position)
                    # logger2.info("12")
                    ai_image_result[key] = [self.cameraCtrlListDic[key], ai_result[position]]  # {相机号:[图片路径,点位信息]}
                    # logger2.info("23")
                if not ai_status:
                    data2 = [22]
                    self.write_signal(data2)
                    logger.info('AI 返回为None，AI服务出错')
                    self.ai_point_record.bool_send_PLC1 = True
                    continue
                test_time1 = time.time()
                # logger4.info("AI-result:{}".format(ai_result))
                # self.ai_image_result_path = copy.deepcopy(ai_image_result)
                th1 = threading.Thread(target=self.use_threading1, args=(ai_image_result, ai_result, start_time, photo_n, id5_take_photo), name="save_ai_image")
                th1.start()
                # self.save_ai_image(ai_image_result)  # 应改为调用线程
                # logger.info("第{}次存删图片用时:{}".format(photo_n, time.time() - test_time1))

                self.point_deal1(ai_result, start_time, self.speed2, photo_n, id5_take_photo)
                # if ai_result is not None:
                #     logger2.debug("AI result not checked is {}".format(ai_result))
                #     point_arr = caculate_nearly_point(ai_result)  # 舍去相机重合点
                #     if point_arr is not None:
                #         logger2.debug("the checked result is {}".format(point_arr))
                #         datapiont1 = self.remove_point2(point_arr, start_time, speeedas2)
                #         # print("@@@@@@@@@@@@@@-----({})---time:{}----speed:{}".format(photo_n,start_time,speeedas2))
                #         if datapiont1 is not None:
                #             logger2.debug("the datapiont1 result is {}".format(datapiont1))
                #             self.put_record2queue(datapiont1, start_time, speeedas2, photo_n, id5_take_photo,)  # 将点写入队列（生产者调用）
                if self.ai_point_record.bool_send_PLC1:
                    data2 = [88]
                    self.write_signal(data2)
                    self.ai_point_record.bool_send_PLC1 = False
                if aiCottonConfig.BOOL_SLEEP:
                    time.sleep(aiCottonConfig.SLEEP_TIME)
            except Exception as e:
                logger.error(f"err---produce: {e}")
                time.sleep(0.8)

    '''消费者-消费数据'''
    def run_consume_point_record(self):  # 消费者（使用点数据）---抓手1+2
        zhua_a = 1  # 用于锁定抓手
        zhua_b = 0  # 用于判断读取抓手状态
        time.sleep(0.4)  # 生产者调试对应
        t5 = -1.0
        onemoretime = True
        twomoretime = True
        arm_ctrl = aiCottonConfig.ARM_NUM
        while True:
            try:
                # logger.info("====循环标记：{}".format(self.bool_xfz))
                if self.bool_xfz:
                    # logger.info("进入抓手循环")
                    '''判断是否需要暂停，或超出单次检测时间'''
                    plc_status = self.read_sleep_status()
                    if plc_status:
                        sleep_status1 = plc_status.get(aiCottonConfig.MELSEC_CODE.STOP_ALL1)
                        if self.num_take_pic % 20 == 3:
                            logger.info('sleep_status1: {}'.format(sleep_status1))
                    else:
                        logger.info("sleep_status1 is none")
                        self.reconnect_plc()
                        logger.info("reconnect plc finished")
                        continue
                    if sleep_status1 == 0:#PLC需要保持为0
                        logger.info("------------此时待机")
                        self.sleepdown1 = False#此时待机
                        self.record_err()
                        self.fiber_queue.queue.clear()  # 因为要暂停，之前存在队列上的数据点就没用了
                        self.hard_yellow_queue.queue.clear()
                        self.light_yellow_queue.queue.clear()
                        self.fiber_seemingly_queue.queue.clear()
                        self.fiber_queue_assit.queue.clear()
                        self.hard_yellow_queue_assit.queue.clear()
                        self.light_yellow_queue_assit.queue.clear()
                        self.fiber_seemingly_queue_assit.queue.clear()
                        time.sleep(5)
                        continue
                    else:
                        self.sleepdown1 = True  # 此时正常
                        run_time1 = self.keep_time()
                        if self.num_take_pic % 20 == 3:
                            logger.info("----------累计时间------{}\n-------现在速度-------{}".format(int(run_time1), self.speed2))
                        if run_time1 > 1800 and onemoretime:  # 防止1200s后重复进入
                            onemoretime = False
                            logger.info("此次已检测30分钟，通知PLC转向")
                            # self.write_sleep_data(1)  # 已运行20分钟，让PLC转向
                        if run_time1 > 3600 and twomoretime:  # 防止2400s后重复进入
                            twomoretime = False
                            logger.info("此次已检测60分钟，通知PLC换包")
                            # self.write_sleep_data(3)  # 已运行40分钟，让PLC换包
                            self.lt_keep_time = 0  # 累计时间初始化0
                            self.keep_time1 = None  # 防止传送带未停，造成此次累计时间刷入
                            onemoretime, twomoretime = True, True
                            # time.sleep(20)  # 等待至传送带停止或重新启动



                    '''读取判断抓手1的状态'''
                    tong_status = self.read_tongs_status(1)  # X轴抓取中#X轴归位中
                    if tong_status:
                        if self.num_take_pic % 20 == 3:
                            logger.info('tong_status: {}'.format(tong_status))
                        bool_zs1_1 = tong_status.get(aiCottonConfig.MELSEC_CODE.TONGS_STATUS1)  # 抓取中
                        bool_zs1_2 = tong_status.get(aiCottonConfig.MELSEC_CODE.HOMING_STATUS1)  # 归位中
                        bool_zs2_1 = tong_status.get(aiCottonConfig.MELSEC_CODE.TONGS_STATUS2)  # 抓取中
                        bool_zs2_2 = tong_status.get(aiCottonConfig.MELSEC_CODE.HOMING_STATUS2)  # 归位中
                        # bool_zs1_1 = 1
                        # bool_zs1_2 = 1
                        # bool_zs2_1 = 1
                        # bool_zs2_2 = 1

                    else:
                        logger.info("tong_status is none")
                        self.reconnect_plc()
                        logger.info("reconnect plc finished")
                        continue

                    '''判断已经抓取次数'''
                    if self.currentHomingCount >= 1000 and bool_zs2_2 == 0:  # 当抓手1运动计数超过次数，让抓手回原点
                        logger.info("高处模组---抓手1---发送归位")
                        # self.record_queue2.put(point_record)
                        # bResult = self.write_homing_data(1)  # 写入缓冲，返回socket响应的数据
                        bResult = True
                        # self.record_queue.queue.clear()  # 因为要暂停，之前存在队列上的数据点就没用了
                        self.currentHomingCount = 0
                        if bResult:  # 回原点确定
                            self.currentHomingCount = 0  # 计数值清零
                        time.sleep(0.1)
                        continue
                    if self.currentHomingCount2 >= 1000 and bool_zs1_2 == 0:  # 当抓手1运动计数超过次数，让抓手回原点
                        logger.info("高处模组---抓手2---发送归位")
                        # self.record_queue2.put(point_record)
                        # bResult = self.write_homing_data(2)  # 写入缓冲，返回socket响应的数据
                        bResult = True
                        # self.record_queue.queue.clear()  # 因为要暂停，之前存在队列上的数据点就没用了
                        self.currentHomingCount2 = 0
                        if bResult:  # 回原点确定
                            self.currentHomingCount2 = 0  # 计数值清零
                        time.sleep(0.1)
                        continue

                    '''读取判断抓手1的状态'''
                    if zhua_b != 2:  # 若是没被抓手2没锁定
                        # 抓手1忙碌时或主队列为空
                        if self.judge_empty_main_queue() or bool_zs1_1 == 1 or bool_zs1_2 == 1:
                            zhua_a, zhua_b = 0, 0  # 不取队列，无比较动作(无脑解锁，清零)
                            # time.sleep(0.1)
                        else:
                            zhua_a, zhua_b = 1, 1  # 进入抓手1比较部分，并锁定
                    '''读取判断抓手2的状态'''
                    if zhua_b != 1:  # 若是没被抓手1没锁定
                        # 抓手2忙碌时
                        if bool_zs2_1 == 1 or bool_zs2_2 == 1:
                            zhua_a, zhua_b = 0, 0  # 不取队列，无比较动作(无脑解锁，清零)
                            if not self.judge_empty_main_queue():
                                time.sleep(0.3)  # 抓手1/2都在忙碌，等待一会儿
                        else:
                            zhua_a, zhua_b = 2, 2  # 进入抓手2比较部分，并锁定

                    '''准备取队列上的数据'''
                    if zhua_a != 0:  # 锁定成抓手1/2（起码有一个抓手空闲）
                        zhua_b = 0  # 解锁
                        if self.judge_empty_queue():
                            '''判断是否长时间无异纤，并通知PLC暂停'''
                            t4 = time.time()
                            if t5 > 0:
                                time_l1 = t4 - t5
                                if time_l1 > 60000:
                                    self.sleepdown1 = False  # 此时待机
                                    logger.info("已有60s无异纤，休眠程序及抓手！")
                                    # self.write_sleep_data(0)  # 60s无异纤，让PLC提醒
                            time.sleep(0.4)#无数据，可以停久一点
                            continue
                        t5 = time.time()
                        bool_queue1 = True
                        num_queue1 = 0
                        while bool_queue1:
                            num_queue1 += 1
                            point_record = self.choose_point1(zhua_a)
                            if point_record is None:
                                if num_queue1 % 10 == 1:
                                    logger.info("all record queue are empty, we can sleep")
                                time.sleep(0.1)
                            else:
                                bool_queue1 = False
                                continue
                        start_time = point_record.get("start_time")  # 拍照时刻的点的时间戳(arm:s)
                        speed_bmq1 = point_record.get("speed")  # -----传送带速度#----mm/s
                        x = point_record.get("worldX") - aiCottonConfig.DIFF_X  # X值加减参数
                        y = point_record.get("worldY") - aiCottonConfig.LEFT_DIFF_Y
                        print("point_record",point_record)
                        # ------------------------------------------------------------------------------------
                        if zhua_a == 1:
                            zhua_b = 0  # 一但进入判断，就解锁（不论抓不着还是去抓取）
                            x = x + aiCottonConfig.X1_LEN1
                            y = y - 0.25*speed_bmq1 + aiCottonConfig.Y1_LEN1  # 抓手1现场补偿值加大0mm,-5mm(加了连接板5mm)

                            current_speed_x = 520  # mm/s
                            will_time1 = abs(2200 - x) / current_speed_x + 0.3  # 抓手从空闲位到抓到异纤的预测时间,s
                            will_length = speed_bmq1 * will_time1  # 预计抓手移动需要的时间 mm

                            spend_time = time.time() - start_time
                            spend_length = speed_bmq1 * spend_time  # 传送带速度*时间=# 传送带走的距离
                            if float(spend_length + will_length) < y:  # 此时，传送带未走到位，才有抓到的条件
                                data, arm_time_now = self.read_data(1)  # 最后读取PLC系统时间，保证时间的准确性
                                current_time = time2long(data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC),
                                                         data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC))

                                # 下抓时间/最终的时间点：t_PLC + y/speed +偏差值- (t2_arm - t1_arm)
                                # down_time = round(speed_bmq1*aiCottonConfig.T1_LEN1/1000 + aiCottonConfig.T1_LEN2, 3)
                                end_time = current_time + (y/speed_bmq1 + aiCottonConfig.T1_LEN1 - (arm_time_now - start_time))*1000
                                sec, mill_sec = long2time(end_time)  # 毫秒转时间

                                logger.info("------1---@@@@--------秒：{} 毫秒：{}".format(int(sec), int(mill_sec)))

                                self.write_data(int(sec), int(mill_sec), int(x), 0, 0, 1)
                                self.ai_point_record.use_1claw_OK += 1  # 抓手1 抓取OK
                                if point_record["level"] == 1:
                                    self.ai_point_record.use_1claw_OK_1 += 1  # 抓手1 抓取OK 异纤 优先
                                elif point_record["level"] == 2:
                                    self.ai_point_record.use_1claw_OK_2 += 1  # 抓手1 抓取OK  -其他异常点
                                else:
                                    self.ai_point_record.use_1claw_OK_3 += 1  # 抓手1 抓取OK  -异纤 疑似
                                self.currentHomingCount += 1
                                self.point_end1 += 1
                                logger4.info("===总：{} 使用：{} 舍去：{}----进入次队列总:{} OK:{} NG:{}---\n该点传给PLC：{}".format(
                                    int(self.point_end1 + self.point_end2), self.point_end1, self.point_end2,
                                    self.times_queue2_all,
                                    self.times_queue2, self.times_queue2_all - self.times_queue2, point_record))
                                logger4.info(
                                    "----\n运算此点时，点走过的路程：{}mm, \n抓手计划的时间对应的路程: {}mm".format(spend_length, will_length))
                                list_point = [point_record.get("id_tp"), point_record.get("id_pic"),
                                              point_record.get("speed"), point_record.get("x_max"),
                                              point_record.get("y_max"), point_record.get("x_min"),
                                              point_record.get("y_min"), point_record.get("worldX"),
                                              point_record.get("worldY"), 4,point_record.get("label"),
                                              point_record.get("score"), point_record.get("level")]
                                write_mysql(list_point)
                                continue

                            point_record["times_judge"] += 1
                            self.ai_point_record.use_1claw_check_NG += 1  # 抓手1 舍去 存入次队列-总
                            if point_record["level"] == 1:
                                num_OK, num_NG = self.real_put_point_record(self.fiber_queue_assit, point_record,
                                                                               "异纤-优先-次")
                                self.ai_point_record.use_1claw_check_NG_1 += num_OK  # 抓手1 舍去 存入次队列-异纤 优先
                                self.ai_point_record.use_1claw_check_NG_1_throw += num_NG  # 抓手1 舍去 存入次队列-异纤 优先 因队列满删掉
                            elif point_record["level"] == 2:
                                num_OK, num_NG = self.real_put_point_record(self.hard_yellow_queue_assit, point_record,
                                                                               "深黄毛-次")
                                self.ai_point_record.use_1claw_check_NG_2 += num_OK  # 抓手1 舍去 存入次队列-其他异常点
                                self.ai_point_record.use_1claw_check_NG_2_throw += num_NG  # 抓手1 舍去 存入次队列-其他异常点 因队列满删掉
                            elif point_record["level"] == 2:
                                num_OK, num_NG = self.real_put_point_record(self.light_yellow_queue_assit, point_record,
                                                                               "中黄毛-次")
                            else:
                                num_OK, num_NG = self.real_put_point_record(self.fiber_seemingly_queue_assit,
                                                                            point_record,
                                                                               "异纤-疑似-次")
                                self.ai_point_record.use_1claw_check_NG_3 += num_OK  # 抓手1 舍去 存入次队列-异纤 疑似
                                self.ai_point_record.use_1claw_check_NG_3_throw += num_NG  # 抓手1 舍去 存入次队列-异纤 疑似 因队列满删掉


                        # --------------------------------------------------------------------------------
                        elif zhua_a == 2:
                            zhua_b = 0  # 一但进入判断，就解锁（不论抓不着还是去抓取）
                            x = x + aiCottonConfig.X2_LEN1
                            y = y + 607 - 0.25*speed_bmq1 + aiCottonConfig.Y2_LEN1 #抓手2与抓手1相距607mm+5mm(加了连接板5mm)

                            current_speed_x = 520  # mm/s
                            will_time1 = abs(2200 - x) / current_speed_x + 0.1  # 抓手从空闲位到抓到异纤的预测时间,s
                            will_length = speed_bmq1 * will_time1  # 预计抓手移动需要的时间 mm

                            spend_time = time.time() - start_time
                            spend_length = speed_bmq1 * spend_time  # 传送带速度*时间=# 传送带走的距离
                            if float(spend_length + will_length) < y:  # 此时，传送带未走到位，才有抓到的条件
                                data, arm_time_now = self.read_data(2)  # 最后读取PLC系统时间，保证时间的准确性
                                current_time = time2long(data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC),
                                                         data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC))
                                # 下抓时间/最终的时间点：t_PLC + y/speed +偏差值 - (t2_arm - t1_arm)
                                end_time = current_time + (y / speed_bmq1 + aiCottonConfig.T2_LEN1 - (arm_time_now - start_time)) * 1000
                                sec, mill_sec = long2time(end_time)  # 毫秒转时间

                                self.write_data(int(sec), int(mill_sec), int(x), 0, 0, 2)
                                logger.info("------2---@@@-----------秒：{} 毫秒：{}".format(int(sec), int(mill_sec)))
                                # logger4.info('zhua shou 2 first hit point_record {}'.format(point_record))
                                self.ai_point_record.use_2claw_OK += 1  # 抓手2 抓取OK
                                if point_record["level"] == 1:
                                    self.ai_point_record.use_2claw_OK_1 += 1  # 抓手2 抓取OK 异纤 优先
                                elif point_record["level"] == 2:
                                    self.ai_point_record.use_2claw_OK_2 += 1  # 抓手2 抓取OK  -其他异常点
                                else:
                                    self.ai_point_record.use_2claw_OK_3 += 1  # 抓手2 抓取OK  -异纤 疑似
                                self.currentHomingCount2 += 1
                                self.point_end1 += 1
                                logger4.info("===总：{} 使用：{} 舍去：{}----进入次队列总:{} OK:{} NG:{}---\n该点传给PLC：{}".format(
                                    int(self.point_end1 + self.point_end2), self.point_end1, self.point_end2, self.times_queue2_all,
                                    self.times_queue2, self.times_queue2_all - self.times_queue2, point_record))
                                logger4.info(
                                    "----\n运算此点时，点走过的路程：{}mm, \n抓手计划的时间对应的路程: {}mm".format(spend_length, will_length))
                                list_point = [point_record.get("id_tp"), point_record.get("id_pic"),
                                              point_record.get("speed"), point_record.get("x_max"),
                                              point_record.get("y_max"), point_record.get("x_min"),
                                              point_record.get("y_min"), point_record.get("worldX"),
                                              point_record.get("worldY"), 4, point_record.get("label"),
                                              point_record.get("score"), point_record.get("level")]
                                write_mysql(list_point)
                                if point_record.get("times_judge") > 0:
                                    self.ai_point_record.use_2claw_OK_assit_all += 1  # 抓手2 抓取OK 从次队列拿到的点
                                    if point_record["level"] == 1:
                                        self.ai_point_record.use_2claw_OK_assit_1 += 1  #抓手2 抓取OK 从次队列拿到的点 异纤 优先
                                    elif point_record["level"] == 2:
                                        self.ai_point_record.use_2claw_OK_assit_2 += 1  # 抓手2 抓取OK 从次队列拿到的点 其他异常点
                                    else:
                                        self.ai_point_record.use_2claw_OK_assit_3 += 1  # 抓手2 抓取OK 从次队列拿到的点 -异纤 疑似

                                    self.times_queue2 += 1
                                    logger4.info("抓手2使用次队列点数据成功，{}次".format(self.times_queue2))
                                # time.sleep(0.1)
                            else:
                                # 该点对于抓手2还是不合格，重新大循环，不管抓手1的状态了
                                logger4.info("2-----由于超出极限，抓手把该点抛掉")
                                self.point_end2 += 1
                                self.ai_point_record.use_2claw_check_NG += 1  # 抓手2 舍去 -总
                                if point_record["level"] == 1:
                                    self.ai_point_record.use_2claw_check_NG_1 += 1  # 抓手2 舍去  -异纤 优先
                                elif point_record["level"] == 2:
                                    self.ai_point_record.use_2claw_check_NG_2 += 1  # 抓手2 舍去  -其他异常点
                                else:
                                    self.ai_point_record.use_2claw_check_NG_3 += 1  # 抓手2 舍去  -异纤 疑似
                                if point_record.get("times_judge") > 0:
                                    self.ai_point_record.use_2claw_check_NG_from_q2 += 1  # 抓手2 舍去 -总 -从次队列
                                    if point_record["level"] == 1:
                                        self.ai_point_record.use_2claw_check_NG_1_from_q2 += 1  # 抓手2 舍去 -异纤 优先 -从次队列
                                    elif point_record["level"] == 2:
                                        self.ai_point_record.use_2claw_check_NG_2_from_q2 += 1  # 抓手2 舍去 -其他异常点 -从次队列
                                    else:
                                        self.ai_point_record.use_2claw_check_NG_3_from_q2 += 1  # 抓手2 舍去 -异纤 疑似 -从次队列
                                logger4.info(
                                    "+++总：{} 使用：{} 舍去：{}--------该点舍去：{}".format(
                                        int(self.point_end1 + self.point_end2),
                                        self.point_end1, self.point_end2,
                                        point_record))
                                list_point = [point_record.get("id_tp"), point_record.get("id_pic"),
                                              point_record.get("speed"), point_record.get("x_max"),
                                              point_record.get("y_max"), point_record.get("x_min"),
                                              point_record.get("y_min"), point_record.get("worldX"),
                                              point_record.get("worldY"), 5, point_record.get("label"),
                                              point_record.get("score"), point_record.get("level")]
                                write_mysql(list_point)
                                # logger4.info("抓手2超出极限舍去记录点：{}".format(point_record))
                else:
                    logger.info("正在自检，或等待传送带开启")
                    time.sleep(3)
            except Exception as e:
                logger.error(f"err---+++++++: {e}")
                time.sleep(1)
                # quit()

    '''循环自增数，1~100，给PLC发送变化数据，自证连接正常'''
    def num_changed1(self):
        self.num_changeda += 1
        if self.num_changeda > 500:
            self.num_changeda = 1
        return self.num_changeda

    '''判断传送带的速度是否稳定'''
    def judge_speed(self):
        bool_jud_sp1 = True
        old_speed = None
        name2 = aiCottonConfig.MELSEC_CODE.ARM_XINHAO

        while bool_jud_sp1:

            cds_speed = self.read_speed().get(aiCottonConfig.MELSEC_CODE.CSD_SPEED1)  # 取PLC上的传送带速度
            # cds_speed = 2000
            if cds_speed < 500:
                logger.info("读取的传送带的速度值太低")
                data2 = [self.num_changed1()]
                logger.info("自增数：{}".format(str(data2[0])))
                self._melsec_ctrl.write_dword_data(name2, data2)  # 写入自检信号位-断连状态
                time.sleep(1.5)
                continue
            logger.info('cds_speed: {}'.format(cds_speed))
            if old_speed is not None:  # 开始时old_speed为空，避免第1次
                if cds_speed - old_speed < 50:  # 前后2次速度，趋于稳定#1102数值改写
                    # self.speed2 = cds_speed  # 写入速度
                    self.speed2 = transform_conveyer_speed(cds_speed)  # 写入速度
                    logger.info("检测到现在传送带速度为：{} mm/s".format(self.speed2))
                    if self.speed2 > 400:
                        logger.info("检测到传送带速度过快")
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
        if k > 0 and speeda1 > 20:  # =0时，说明传过来的是空值，不进行操作
            dataZ2 = copy.deepcopy(self.dataZ1)
            pointZ2 = copy.deepcopy(pointZ1)
            # logger2.info("now_point_or---:{},,s:{},t:{}".format(pointZ1, speeda1, time01))

            if not len(dataZ2) == 0:  # 当存储器有值时，进行对比

                for pointZC in dataZ2:  # dataZ2=[[],[],[]]------pointZC=[time,[{},{},{}]]
                    key1 = pointZC[0]
                    # 对比存储器中的个时间点组（超限-舍去，不超-对比）
                    if time01 - key1 > (570 / int(abs(speeda1)+1) + 2.2):
                        if pointZC in self.dataZ1:
                            self.dataZ1.remove(pointZC)  # 去掉超出限制的点
                    else:
                        for pointb2 in pointZ2:  # 最新的点组pointZ2=[{},{},{}] , pointb2={}=value1
                            for value1 in pointZC[1]:  # pointZC=[time,[{},{},{}]], #value1字典{X， Y，position,WX,WY}
                                if abs(value1["worldX"] - pointb2["worldX"]) < 40:  # 先对比X，若不同，应该不是同一个点
                                    l1 = round(speeda1 * (time01 - key1), 2)  # 2组数据实际的距离
                                    l2_rm1 = max(55, abs(round(time01 - key1, 2)) * 28) #随时间跨度而增加的Y方向重合限制，起始值35
                                    if abs(float(value1["worldY"] - pointb2[
                                        "worldY"]) - l1) < l2_rm1:  # 新点pointb2 +l1 == 旧点value1
                                        if pointb2 in pointZ1:
                                            pointZ1.remove(pointb2)
            if len(pointZ1) > 0:
                self.dataZ1.append([time01, pointZ1])
                # logger2.info("Save_pool---:{}".format(pointZ1))
                return pointZ1
            else:
                return None
        else:
            return None

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

    '''存入队列'''

    def put_record2queue(self, point_arr, start_time, speed1, num_tp, id5_take_photo):  # 将点写入队列（生产者调用）

        try:
            if point_arr is not None:
                num_tp_i = 0
                while len(self.after_pic_path) != 3:
                    pass
                # logger4.info(" point_arr {}".format(point_arr))
                for item in point_arr:
                    # logger4.info("进入该点信息")
                    self.ai_point_record.real_all_piont_put += 1  # 实际存入队列 点 总数
                    item["speed"] = speed1
                    item["start_time"] = start_time  # 在每组坐标的字典上添加开始时间的对应组
                    num_tp_i += 1
                    # item["ID_tp"] = num_tp
                    item["ID_point"] = str(num_tp) + "_" + str(num_tp_i)
                    item["times_judge"] = 0
                    item["id_tp"] = id5_take_photo
                    # logger4.info("该点信息-biaoji1")
                    # logger4.info("self.after_pic_path:{}".format(self.after_pic_path))
                    # logger4.info("item-position:{}".format(item["position"]))
                    item["id_pic"] = self.after_pic_path[str(item["position"])]
                    # logger4.info("该点信息-已赋值:{}".format(self.after_pic_path[str(item["position"])]))
                    # item["time_arm"] = time.time()
                    if item["level"] == 1:
                        num_OK, num_NG = self.real_put_point_record(self.fiber_queue, item, "异纤-优先-主")
                        self.ai_point_record.real_fiber_priority_put += num_OK  # 实际存入队列 异纤 优先
                        self.ai_point_record.real_fiber_priority_throw += num_NG  # 异纤 优先 存入时因队列满删掉的点数
                    elif item["level"] == 2:
                        num_OK, num_NG = self.real_put_point_record(self.hard_yellow_queue, item, "深黄毛-主")
                        # self.ai_point_record.real_other_label_put += num_OK  # 实际存入队列 其他异常点
                        # self.ai_point_record.real_other_label_throw += num_NG  # 其他异常点 存入时因队列满删掉的点数
                    elif item["level"] == 3:
                        num_OK, num_NG = self.real_put_point_record(self.light_yellow_queue, item, "中黄毛-主")
                    else:
                        num_OK, num_NG = self.real_put_point_record(self.fiber_seemingly_queue, item, "异纤-疑似-主")
                        # self.ai_point_record.real_fiber_seemingly_put += num_OK  # 实际存入队列 异纤 疑似


                if num_tp_i > 0:
                    logger4.info("第{}次,本轮生成{}个点--耗时：{}---累计生成{}个点，因队列满删掉共{}个点".format(num_tp, num_tp_i, time.time()- start_time,self.point_start1,
                                                                                 self.point_start2))
        except Exception as e:
            logger.error(f"err--put.queue---+++++++: {e}")


    '''判断所有的队列是否为空'''

    def judge_empty_queue(self):
        return self.fiber_queue.empty() and self.fiber_queue_assit.empty() and \
               self.hard_yellow_queue.empty() and self.hard_yellow_queue_assit.empty() and \
               self.light_yellow_queue.empty() and self.light_yellow_queue_assit.empty() and \
               self.fiber_seemingly_queue.empty() and self.fiber_seemingly_queue_assit.empty()

    def judge_empty_main_queue(self):
        return self.fiber_queue.empty() and self.hard_yellow_queue.empty() and self.light_yellow_queue.empty() and self.fiber_seemingly_queue.empty()

    '''读取队列'''
    def choose_point1(self, numAB):
        # 抓手1只读主队列，抓手2读次队列
        if numAB == 1:  # 抓手1
            if self.fiber_queue.empty():
                if self.hard_yellow_queue.empty():
                    if self.light_yellow_queue.empty():
                        if self.fiber_seemingly_queue.empty():
                            rePP1 = None
                        else:
                            rePP1 = self.fiber_seemingly_queue.get()
                            logger4.info('抓手1取到 异纤疑似-主队列数据 {}'.format(rePP1))
                    else:
                        rePP1 = self.light_yellow_queue.get()
                        logger4.info('抓手1取到 中黄毛-主队列数据 {}'.format(rePP1))
                else:
                    rePP1 = self.hard_yellow_queue.get()
                    logger4.info('抓手1取到 深黄毛-主队列数据 {}'.format(rePP1))
            else:
                rePP1 = self.fiber_queue.get()
                logger4.info('抓手1取到 异纤-优先-主队列数据 {}'.format(rePP1))
        else:
            if self.fiber_queue_assit.empty(): #异纤优先-次
                if self.fiber_queue.empty():#异纤优先
                    if self.hard_yellow_queue_assit.empty():#深黄毛-次
                        if self.hard_yellow_queue.empty():#深黄毛
                            if self.light_yellow_queue_assit.empty():#中黄毛-次
                                if self.light_yellow_queue.empty():#中黄毛
                                    if self.fiber_seemingly_queue_assit.empty():#异纤疑似-次
                                        if self.fiber_seemingly_queue.empty():#异纤疑似
                                            rePP1 = None
                                        else:
                                            rePP1 = self.fiber_seemingly_queue.get()
                                            logger4.info('抓手2取到 异纤-疑似-主队列数据 {}'.format(rePP1))
                                    else:
                                        rePP1 = self.fiber_seemingly_queue_assit.get()
                                        logger4.info('抓手2取到 异纤-疑似-次队列数据 {}'.format(rePP1))
                                else:
                                    rePP1 = self.light_yellow_queue.get()
                                    logger4.info('抓手2取到 中黄毛-主队列数据 {}'.format(rePP1))
                            else:
                                rePP1 = self.light_yellow_queue_assit.get()
                                logger4.info('抓手2取到 中黄毛-次队列数据 {}'.format(rePP1))
                        else:
                            rePP1 = self.hard_yellow_queue.get()
                            logger4.info('抓手2取到 深黄毛-主队列数据 {}'.format(rePP1))
                    else:
                        rePP1 = self.hard_yellow_queue_assit.get()
                        logger4.info('抓手2取到 深黄毛-次队列数据 {}'.format(rePP1))
                else:
                    rePP1 = self.fiber_queue.get()
                    logger4.info('抓手2取到 异纤-优先-主队列数据 {}'.format(rePP1))
            else:
                rePP1 = self.fiber_queue_assit.get()
                logger4.info('抓手2取到 异纤-优先-次队列数据 {}'.format(rePP1))

        return rePP1

    '''---------------读写PLC-------------'''

    def connect_plc(self):
        bool_plc1 = True
        num_plc1 = 0
        while bool_plc1:
            bResult = self._melsec_ctrl.open((aiCottonConfig.MELSEC_SERVER_IP, aiCottonConfig.MELSEC_SERVER_PORT))
            if "ssc" in aiCottonConfig.Path_upload:
                bResult1 = self._melsec_ctrl_frist.open((aiCottonConfig.MELSEC_SERVER_IP_F, aiCottonConfig.MELSEC_SERVER_PORT))
            if not bResult:
                logger.info("打开PLC设备连接失败")
                num_plc1 += 1
                time.sleep(2)
                if num_plc1 > 300:
                    logger.info("长时间连接不上PLC，退出程序")
                    time.sleep(2)
                    os._exit(0)
                    return
            else:
                bool_plc1 = False
            if "ssc" in aiCottonConfig.Path_upload:
                if not bResult1:
                    logger.info("打开PLC-确认PLC-设备连接失败")
        logger.info("connect PLC is ok")
        self.bool_PLC_NG = False
        # self.bool_xfz = True

    def reconnect_plc(self):
        self._melsec_ctrl.close()
        time.sleep(2)
        self.connect_plc()

    def get_batch(self,sign2): #获得批次号
        result_big, result_small = self.read_batch(sign2)
        self.batch_cotton = [result_big, result_small]
        if len(result_big) + len(result_small) > 0:
            write_mysql4(self.batch_cotton)  # 写入批次表--0525
        logger.info("+++++++++++此时批次号为：{}".format(self.batch_cotton))

    def ascii_to_char(self,list_int):
        char_batch1 = ""

        for j in range(len(list_int)):
            if list_int[j] == 0:
                continue
            if list_int[j] < 256:#2的8次方，8位
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

    '''读取PLC的系统时间'''
    def read_data(self, zs_numb2):  # （生产者，消费者各调用2次，读取PLC的返回数据）
        read_PLC_time = time.time()
        if zs_numb2 == 0:
            # print("主程序调用PLC通讯")
            self.bool_lock_time = True
        self.lock.acquire()  # 线程加锁
        try:
            if zs_numb2 == 0 or zs_numb2 == 8:

                name01 = aiCottonConfig.MELSEC_CODE.CSD_SPEED1
                bReadData = self._melsec_ctrl.read_dword_data(name01, 1)
                result = self._melsec_ctrl.read_dword_data(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC, 2)  # 返回数组
                name2 = aiCottonConfig.MELSEC_CODE.ARM_XINHAO
                data2 = [self.num_changed1()]
                # print('写入自检信号位-断连状态', data2)
                result_PLC_connect = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入自检信号位-断连状态
                if not result_PLC_connect:
                    logger.info("写入自增连接信号失败:{}".format(result_PLC_connect))
                logger.info("生产者读取PLC花费时间:{}".format(time.time() - read_PLC_time))
                if result is not None:  # 有值
                    data = {
                            aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC: result[0],
                            aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC: result[1],
                            name01: bReadData[0]
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
                time_now = time.time()
                result1 = self._melsec_ctrl.read_dword_data(name3[0], 5)  # 返回数组
                logger.info("消费者读取PLC花费时间:{}".format(time.time() - read_PLC_time))
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
                    return data, time_now   # 将读取的值传给新建的data字典中，键为config中

        except Exception as ex:
            logger.error("read plc system time error {}".format(ex))
            return None
        finally:
            self.bool_lock_time = False
            self.lock.release()

    '''写入信号位'''

    def write_signal(self, data3):
        while self.bool_lock_time:
            time.sleep(0.1)
            logger.info('写入信号位,wait')
        else:
            self.lock.acquire()
            try:
                name2 = aiCottonConfig.MELSEC_CODE.ZJ_XINHAO
                result3 = self._melsec_ctrl.write_dword_data(name2, data3)  # 写入自检信号位
                # time.sleep(0.2)
                return result3
            finally:
                self.lock.release()

    '''读取抓手状态（忙碌/空闲）'''

    def read_tongs_status(self, zs_numb):  # 在消费者中被调用
        while self.bool_lock_time:
            time.sleep(0.1)
            logger.info('读取抓手状态,wait')
        else:
            self.lock.acquire()  # 线程锁
            try:
                name1 = aiCottonConfig.MELSEC_CODE.TONGS_STATUS1
                name2 = aiCottonConfig.MELSEC_CODE.HOMING_STATUS1
                name3 = aiCottonConfig.MELSEC_CODE.TONGS_STATUS2
                name4 = aiCottonConfig.MELSEC_CODE.HOMING_STATUS2
                bReadData1 = self._melsec_ctrl.read_bit_data(name1, 3)  # 返回2组值
                bReadData2 = self._melsec_ctrl.read_bit_data(name3, 3)  # 返回2组值
                if bReadData1 is not None and bReadData2 is not None:
                    data = {
                        name1: bReadData1[0],
                        name2: bReadData1[2],
                        name3: bReadData2[0],
                        name4: bReadData2[2]
                    }
                    return data  ##X轴抓取中#X轴归位中
            except Exception as ex:
                logger.error("read plc tong status error {}".format(ex))
                return None
            finally:
                self.lock.release()

    '''读取抓手状态（是否需要待机）'''
    def read_sleep_status(self):  # 在消费者中被调用
        while self.bool_lock_time:
            time.sleep(0.1)
            logger.info('读取抓手状态,是否需要待机,wait')
        else:
            self.lock.acquire()  # 线程锁
            try:
                #和PLC连接的自增信号
                data2 = [self.num_changed1()]
                result_PLC_connect = self._melsec_ctrl.write_dword_data(aiCottonConfig.MELSEC_CODE.ARM_XINHAO, data2)  # 写入自检信号位-断连状态
                if not result_PLC_connect:
                    logger.info("写入自增连接信号失败:{}".format(result_PLC_connect))
                if data2[0] % 10 == 2:
                    #刷新传送带速度值 ，传给全局变量
                    speed_ReadData = self._melsec_ctrl.read_dword_data(aiCottonConfig.MELSEC_CODE.CSD_SPEED1, 1)
                    logger.info("读取PLC上的传送带速度值：{}".format(speed_ReadData[0]))
                    # speed_ReadData[0] = 2000
                    self.speed2 = transform_conveyer_speed(speed_ReadData[0])
                name01 = aiCottonConfig.MELSEC_CODE.STOP_ALL1
                bReadData = self._melsec_ctrl.read_bit_data(name01, 1)  # 返回
                if bReadData is not None:
                    data = {
                        name01: bReadData[0]
                    }
                    return data
            except Exception as ex:
                logger.error("read plc sleep status error {}".format(ex))
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
            bReadData = self._melsec_ctrl.read_dword_data(name01, 1)  #
            if bReadData is not None:
                data = {
                    name01: bReadData[0]
                }
                self.choose_model1 = bReadData[0]
                logger.info('data: {}'.format(data))
                return data

            return None
        finally:
            self.lock.release()

    '''读取批次号--PLC通讯'''
    def read_batch(self, sign1):#初始化时 sign1=Fasle ，
        self.lock.acquire()  # 线程锁
        try:
            logger.info('读取批次号--PLC通讯--1')
            result1_char1, result2_char1 = "",  ""
            sign2 = True #默认去读写
            if sign1:
                result_sign = self._melsec_ctrl.read_bit_data(aiCottonConfig.MELSEC_CODE.SIGN_BATCH, 1)
                if result_sign[0] == 0:#当信号位为0，表示无变化时，不去读取大小批次
                    sign2 = False
            logger.info('读取批次号--PLC通讯--2')
            if sign2:
                result1_ascii = self._melsec_ctrl.read_word_data(aiCottonConfig.MELSEC_CODE.BIG_BATCH, 5)
                result1_char1 = self.ascii_to_char(result1_ascii)
                result2_ascii = self._melsec_ctrl.read_word_data(aiCottonConfig.MELSEC_CODE.SMALL_BATCH, 8)
                result2_char1 = self.ascii_to_char(result2_ascii)
            logger.info('result1_char1：{}， result2_char1：{}'.format(result1_char1,result2_char1))
            return result1_char1, result2_char1
        finally:
            self.lock.release()
    '''写入抓取时间和坐标等数据'''

    def write_data(self, sec, millsec, x, feedback_x, feedback_speed, zs_numb3):  # 最后2个，反馈x,反馈速度（消费者调用）
        while self.bool_lock_time:
            time.sleep(0.1)
            logger.info('写入抓取时间和坐标等数据,wait')
        else:
            self.lock.acquire()
            try:
                if zs_numb3 == 1:
                    name4 = aiCottonConfig.MELSEC_CODE.GRAB_TIME_SEC1
                else:
                    name4 = aiCottonConfig.MELSEC_CODE.GRAB_TIME_SEC2
                data = [sec, millsec, x, feedback_x, feedback_speed]
                result1 = self._melsec_ctrl.write_dword_data(name4, data)  # 抓取时间戳
                # result2 = self._melsec_ctrl.write_dword_data(aiCottonConfig.MELSEC_CODE.GRAB_TIME_MILLSEC, [millsec])
                if result1 is not None:
                    return True
                return False
            finally:
                self.lock.release()

    '''抓手回原点'''

    def write_homing_data(self, zs_numb1):  # （消费者调用）
        while self.bool_lock_time:
            time.sleep(0.1)
            logger.info('抓手回原点,wait')
        else:
            self.lock.acquire()
            try:
                if zs_numb1 == 1:
                    name2 = aiCottonConfig.MELSEC_CODE.TONGS_HOMING1
                else:
                    name2 = aiCottonConfig.MELSEC_CODE.TONGS_HOMING2
                return self._melsec_ctrl.write_bit_data(name2, [1])
            finally:
                self.lock.release()

    '''向PLC写入休眠信号'''

    def write_sleep_data(self, num_onemt):  # （消费者调用）(向PLC写入休眠信号)
        while self.bool_lock_time:
            time.sleep(0.1)
            logger.info('向PLC写入休眠信号,wait')
        else:
            self.lock.acquire()
            try:
                if num_onemt == 0:
                    name3 = aiCottonConfig.MELSEC_CODE.SLEEP_PLC
                    self._melsec_ctrl_frist.write_bit_data(name3, [1])
                    return True
                elif num_onemt == 2:
                    logger.info("写入M50，1")
                    name3 = aiCottonConfig.MELSEC_CODE.START_OK
                    self._melsec_ctrl.write_bit_data(name3, [1])
                    if "ssc" in aiCottonConfig.Path_upload:
                        self._melsec_ctrl_frist.write_bit_data(name3, [1])
                    return True
                elif num_onemt == 3:
                    name3 = aiCottonConfig.MELSEC_CODE.CHANGE_OK
                    self._melsec_ctrl.write_bit_data(name3, [1])
                    return True
                elif num_onemt == 4:
                    name3 = aiCottonConfig.MELSEC_CODE.CHANGE_OK
                    self._melsec_ctrl.write_bit_data(name3, [0])
                    return True
                else:
                    name3 = aiCottonConfig.MELSEC_CODE.DO_ONE_TIME_PLC
                    self._melsec_ctrl.write_bit_data(name3, [1])
                    return True

            finally:
                self.lock.release()


# ####---------------相机拍照/相机回调/图片存放-------------

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
        return bResult,cam_now1

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

    '''图片存放路径'''

    def generate_path(self, num_tp):  # 返回图片存放路径，组#（生产者调用）
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
            # camera_path = {"13024367":"/mnt/data/data/image_original/img_" + self.date_path1 + "/" + "%s_%s_%s.jpg",
            # "12024382":"/mnt/data/data/image_original/img_" + self.date_path1 + "/" + "%s_%s_%s.jpg",
            # "13024376":"/mnt/data/data/image_original/img_" + self.date_path1 + "/" + "%s_%s_%s.jpg"}
        return camera_path

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

    def process_ai_request(self, camera_key):
        position = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[camera_key]  # 相机对应的位置
        start_n = time.time()
        res = call_ai_service(self.cameraCtrlListDic[camera_key])  # 调用ai服务，#返回字符串
        logger2.info("the camera {}------------- AI service time: {}".format(camera_key, time.time() - start_n))
        if res is None:
            logger.error("AI service request failed")
            return None
        else:
            logger2.debug("ai result is {}".format(res))
            return self.processAiData(res.get("data").get("0"), position)

    def processAiData(self, res_data, position):  # 返回像素点坐标，相机位置，世界坐标的字典 的列表#（生产者调用）
        arr = []
        data_label = res_data["labels"]
        if len(data_label) > 0: # 为空列表时，可以直接返回 arr = []
            data_score = res_data["scores"]
            data_point = res_data["boxes"]
            for i_point in range(len(data_label)):
                self.ai_point_record.ai_all_point += 1  # 计数 AI 识别总数
                # logger4.info("data_score[i_point]:{}".format(data_score[i_point]))
                if data_score[i_point] < aiCottonConfig.Suspected_threshold:#当分数小于怀疑值的时候，点不要
                    continue

                if data_label[i_point] in self.list_zh1[int(self.choose_model1)]: # 当 label 是在PLC传来的分类列表中
                    self.ai_point_record.ai_all_label += 1  # 计数 AI中 所有符合分类的点
                    #先判断 点的位置
                    if data_point[i_point][1] < 50 or data_point[i_point][3] > 2000:  # Y方向，靠近边缘，极有可能是识别不全，舍去
                        continue
                    if data_point[i_point][0] < 100 or data_point[i_point][2] > 2348:  # X方向，靠近边缘，极有可能是识别不全，舍去(相邻相机重合370pix)
                        continue
                    self.ai_point_record.ai_pix_main += 1  # 计数 AI 符合分类、不在边缘处 的点
                    # logger4.info("data_label[i_point]:{}".format(data_label[i_point]))
                    x = (data_point[i_point][0] + data_point[i_point][2]) / 2  # 图片中的像素坐标
                    y = (data_point[i_point][1] + data_point[i_point][3]) / 2
                    worldx, worldy, worldz = image_points_to_world_plane(x, y, int(position))  # 换算过后的世界坐标
                    if int(position) == 1: #对A相机的画面的截断（与B相机的点重合）
                        if worldx > 779 + 0:
                            continue
                    if int(position) == 2: #对C相机的画面的截断（与B相机的点重合）
                        if worldx < 1463 - 0:
                            continue
                    # 再判断 点的分类的等级
                    # 1:异纤-优先，2深黄毛，3中黄毛，4异纤-疑似
                    if data_label[i_point] == "yixian":
                        if float(data_score[i_point]) >= aiCottonConfig.Classification_threshold:
                            point_level = 1 #1:异纤-优先
                            self.ai_point_record.fiber_priority += 1  # 计数 初步筛选 AI-异纤 优先
                        else:
                            point_level = 4
                            self.ai_point_record.fiber_seemingly += 1  # 计数 初步筛选 AI-异纤 疑似
                    elif data_label[i_point] == "shenhuangmao":
                        point_level = 2
                        self.ai_point_record.other_label += 1  # 计数 初步筛选 AI-深黄毛
                    else:
                        point_level = 3  # 中黄毛
                    map = {"position": position, "label": data_label[i_point], "level": point_level, "x": x, "y": y,
                           "worldX": abs(worldx), "worldY": abs(worldy),"score": round(data_score[i_point], 5),
                           "x_min": data_point[i_point][0],
                           "x_max": data_point[i_point][2], "y_min": data_point[i_point][1],
                           "y_max": data_point[i_point][3]}
                    self.ai_point_record.ai_first_filtrate += 1  # 计数 AI 初步筛选的点
                    arr.append(map) #arr = [{},{}]
        return arr

    '''将点信息 存入队列，若满即删并记录'''
    def real_put_point_record(self, queue_put, point_message, name_queue):
        ai_point_all31 = 0
        if queue_put.full():
            throw1 = queue_put.get()
            logger4.info("got the record from full queue")
            # list_point = [throw1.get("ID_tp"), throw1.get("position"),
            #               throw1.get("speed"), throw1.get("x_max"),
            #               throw1.get("y_max"), throw1.get("x_min"),
            #               throw1.get("y_min"), throw1.get("worldX"),
            #               throw1.get("worldY"), 5]
            # ai_point_all31 += 1  # 统计AI识别到的点--存入队列 但因满队列而删掉的点
            # write_mysql(list_point)
            # logger4.info("舍去：{}队列舍去最早入队的点：{}".format(name_queue, throw1))
        queue_put.put(point_message)  # 放到队列里
        ai_point_all32 = 1  # 统计AI识别到的点--最后存入队列的
        logger4.info("存入：{}队列存入点：{}".format(name_queue, point_message))
        return ai_point_all32, ai_point_all31

    # def log_message_produce(self):
    #     print_list = [self.ai_point_record.ai_all_point, self.ai_point_record.ai_all_label,
    #                   self.ai_point_record.ai_pix_main, self.ai_point_record.ai_first_filtrate,
    #                   self.ai_point_record.fiber_priority, self.ai_point_record.fiber_seemingly,
    #                   self.ai_point_record.other_label, self.ai_point_record.real_all_piont_put,
    #                   self.ai_point_record.real_fiber_priority_put, self.ai_point_record.real_fiber_seemingly_put,
    #                   self.ai_point_record.real_other_label_put, self.ai_point_record.real_fiber_priority_throw,
    #                   self.ai_point_record.real_fiber_seemingly_throw, self.ai_point_record.real_other_label_throw
    #                   ]
    #     logger4.info(
    #         "AI总数:{}, AI分类总:{}, AI非边缘:{}, AI初筛:{} (初:异纤-优:{}, 其他:{}, 异纤-疑:{})".format(print_list[0], print_list[1],
    #                                                                                   print_list[2], print_list[3],
    #                                                                                   print_list[4], print_list[6],
    #                                                                                   print_list[5]))
    #     logger4.info(
    #         "存入总:{}(存:异纤-优:{}, 其他:{}, 异纤-疑:{})  --因满删:{}(删:异纤-优:{}, 其他:{}, 异纤-疑:{})".format(print_list[7],
    #                                                                                         print_list[8],
    #                                                                                         print_list[10],
    #                                                                                         print_list[9],
    #                                                                                         print_list[11] + print_list[
    #                                                                                             12] + print_list[13],
    #                                                                                         print_list[11],
    #                                                                                         print_list[13],
    #                                                                                         print_list[12]))

    # def log_message_consume(self):
    #     print_list2 = [self.ai_point_record.use_1claw_OK,self.ai_point_record.use_1claw_OK_1,self.ai_point_record.use_1claw_OK_2,self.ai_point_record.use_1claw_OK_3,
    #                    self.ai_point_record.use_2claw_OK,self.ai_point_record.use_2claw_OK_1,self.ai_point_record.use_2claw_OK_2,self.ai_point_record.use_2claw_OK_3,
    #                    self.ai_point_record.use_2claw_OK_assit_all,self.ai_point_record.use_2claw_OK_assit_1,self.ai_point_record.use_2claw_OK_assit_2,self.ai_point_record.use_2claw_OK_assit_3,
    #                    self.ai_point_record.use_1claw_PLC_throw,self.ai_point_record.use_2claw_PLC_throw,
    #                    self.ai_point_record.use_1claw_first_NG,self.ai_point_record.use_1claw_first_NG_1,self.ai_point_record.use_1claw_first_NG_2,self.ai_point_record.use_1claw_first_NG_3,
    #                    self.ai_point_record.use_1claw_check_NG,self.ai_point_record.use_1claw_check_NG_1,self.ai_point_record.use_1claw_check_NG_2,self.ai_point_record.use_1claw_check_NG_3,
    #                    self.ai_point_record.use_1claw_first_NG_1_throw,self.ai_point_record.use_1claw_first_NG_2_throw,self.ai_point_record.use_1claw_first_NG_3_throw,
    #                    self.ai_point_record.use_2claw_first_NG,self.ai_point_record.use_2claw_first_NG_1,self.ai_point_record.use_2claw_first_NG_2,self.ai_point_record.use_2claw_first_NG_3,
    #                    self.ai_point_record.use_2claw_first_NG_from_q2,self.ai_point_record.use_2claw_first_NG_1_from_q2,self.ai_point_record.use_2claw_first_NG_2_from_q2,self.ai_point_record.use_2claw_first_NG_3_from_q2,
    #                    self.ai_point_record.use_2claw_check_NG,self.ai_point_record.use_2claw_check_NG_1,self.ai_point_record.use_2claw_check_NG_2,self.ai_point_record.use_2claw_check_NG_3,
    #                    self.ai_point_record.use_2claw_check_NG_from_q2,self.ai_point_record.use_2claw_check_NG_1_from_q2,self.ai_point_record.use_2claw_check_NG_2_from_q2,self.ai_point_record.use_2claw_check_NG_3_from_q2
    #     ]
    #     logger4.info("总抓取数:{} 丢弃总数:{}".format())
    #     #丢弃总数 =
    #     logger4.info("总抓取数:{} (抓手1:{} ，抓手2:{})".format())
    #     logger4.info("抓手1:{} (异纤-优:{}, 其他:{}, 异纤-疑:{})".format())
    #     logger4.info("抓手2:{} (异纤-优:{}, 其他:{}, 异纤-疑:{}) --次队列中(异纤-优:{}, 其他:{}, 异纤-疑:{})".format())
    #
    #     logger4.info("丢弃总数:{} PLC异常丢弃:{} (抓手2初步舍弃:{} (异纤-优:{}, 其他:{}, 异纤-疑:{})) (抓手2舍弃:{} (异纤-优:{}, 其他:{}, 异纤-疑:{}))".format())
    #     logger4.info(
    #         "丢弃总数:{} 从次队列取出:{} (抓手2初步舍弃:{} (异纤-优:{}, 其他:{}, 异纤-疑:{})) (抓手2舍弃:{} (异纤-优:{}, 其他:{}, 异纤-疑:{}))".format())
    #     logger4.info(
    #         "抓手1舍去总数:{} 抓手1初步舍弃:{} (异纤-优:{}, 其他:{}, 异纤-疑:{})  (抓手1舍弃:{} (异纤-优:{}, 其他:{}, 异纤-疑:{})".format())
    #     logger4.info("因队列满删掉:{} (异纤-优:{}, 其他:{}, 异纤-疑:{}) ".format())


    '''间断时间计时'''

    def keep_time(self):
        if self.speed2 > 10 and self.sleepdown1:
            if self.keep_time1 is None:
                self.keep_time1 = time.time()
            lt_now = time.time() - self.keep_time1 + self.lt_keep_time
        else:
            if self.keep_time1 is not None:
                self.lt_keep_time += time.time() - self.keep_time1
                self.keep_time1 = None
            lt_now = self.lt_keep_time
        return lt_now

# ####---------------暂不使用-------------

    '''未使用'''

    def read_tongs_speed(self):  # （未使用）
        self.lock.acquire()
        try:
            speed = self._melsec_ctrl.read_dword_data(aiCottonConfig.MELSEC_CODE.TONGS_X_SPEED1, 1)
            if speed is not None:
                return speed[0]
            return 0
        finally:
            self.lock.release()

    '''关闭相机'''

    def closeCamera(self):
        """ 
        关闭相机  
        """
        if aiCottonConfig.CAMERA_ON:
            for key, value in self.cameraCtrlList.items():
                logger.info("the {} camera is {}".format(key, value.get("status", "---")))
                if value.get("status", "---") != "active":
                    oCtrl = value.get("instance", None)
                    if oCtrl:
                        oCtrl.close_device()
                    self.cameraCtrlList.pop(key)

    '''读取编码器，换算传送带速度'''

    def read_speed23(self):
        oDevice = ai_encoder_device()  #
        oSerialList = oDevice.list_serial_port()  # 遍历列表
        logger.info("found serial port：")
        for oInfo in oSerialList:
            logger.info("name: %s, device: %s, description: %s" % (oInfo.name, oInfo.device, oInfo.description))
        bResult = oDevice.open("/dev/ttyUSB0")
        logger.info("oDevice.open: ", bResult)
        if not bResult:
            return
        try:
            # 先读取参数
            strAddress, strParams = oDevice.read_params()
            if strAddress is None:
                logger.info("oDevice.read_params()失败")
                return
            # end if
            logger.info("oDevice.read_params: addr = %s" % strAddress)
            # 打印参数描述
            logger.info("oDevice.read_params: params = %s" % ai_encoder_device.param_desc(strParams))

            # 设置为被动模式
            if oDevice.set_passive_mode(strAddress):
                logger.info("oDevice.set_passive_mode OK")
            else:
                logger.info("oDevice.set_passive_mode FAILED")
            # end if

            # 设置地址
            if oDevice.set_address(strAddress, 78):
                logger.info("oDevice.set_address to 78 OK")
                # 测试读取数据
                iData = oDevice.read_data(78)
                logger.info("oDevice.read_data(from 78) = %s" % iData)

                if oDevice.set_address(78, strAddress):
                    logger.info("oDevice.set_address 78 to default OK")
                else:
                    logger.info("oDevice.set_address FAILED")
                # end if
            else:
                logger.info("oDevice.set_address FAILED")
            # end if

            # 测试读取数据
            # for i in range(100):
            speed_ori1 = 0
            while True:

                iData1 = oDevice.read_data(strAddress)
                timeb1 = time.time()
                time.sleep(2)  # 逻辑不严谨（与生产者，消费者）
                iData2 = oDevice.read_data(strAddress)
                timeb2 = time.time()
                ts1 = timeb2 - timeb1
                L_pt1 = iData2 - iData1  # 编码器绝对值之差
                if L_pt1 < 0:  # 跳0时的处理
                    L_pt1 += 1000000
                L_pt2 = L_pt1 / 1000  # 计算圈数
                # speeda1 = L_pt2/ts1*250#每圈代表的长度
                # speeda1 = L_pt1/ts1 * 250  # 每个分辨率代表的长度
                speeda1 = L_pt1 / ts1 / self.speed2_K  # 每个分辨率代表的长度（mm/s）
                if speeda1 > 5 and speeda1 < 300:
                    if abs(speeda1 - speed_ori1) < 5:  # 速度相差小于3mm/s，等效于传送带正常
                        self.speed2 = speeda1  # 92.95
                        # print('现在的传送带速度为：{}'.format(self.speed2))
                    else:
                        self.speed2 = speeda1  # 92.95
                        logger.info('传送带处于加速期，速度差为：{}mm/s'.format(abs(speeda1 - speed_ori1)))
                else:
                    self.speed2 = speeda1  # 92.95
                    logger.info("编码器读取有误，该值为：{}".format(speeda1))
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
        self.judge_pic_thread()
        # self.__oPoolForRaster.submit(self.read_speed23)

    '''初始化时-设置相机参数'''

    def set_camera_param(self, oCtrl, sn):  # 实例及标号#（初始化调用）
        if sn == aiCottonConfig.CAMERA_DEVICE_TUPLE[0]:
            oParam = aiCottonConfig.A_CAMERA_PARAMETER  # 相机参数
        elif sn == aiCottonConfig.CAMERA_DEVICE_TUPLE[1]:
            oParam = aiCottonConfig.C_CAMERA_PARAMETER  # 相机参数
        else:
            oParam = aiCottonConfig.B_CAMERA_PARAMETER  # 相机参数

        # oParam = aiCottonConfig.CAMERA_PARAMETER#相机参数

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

    '''连接PLC的IP及端口，初始化相机'''

    def init_service(self):
        self.connect_plc()
        self.initCamera()


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

    def write_record_num_label(self):  # 录入点计数信息
        txt_name1 = self.upload_path + "/point_record_message.txt"
        bool_name_file = os.path.isfile(txt_name1)
        if bool_name_file:
            logger.info("创建新-点信息记录次数-txt文件")
            tf_2 = open(txt_name1, 'r+')
            point_message3 = ""
            for i_label in range(len(self.label_path)):
                point_message3 += self.label_path[i_label] + "," + str(self.list_num_label[i_label]) + ","
            tf_2.write(point_message3)
            tf_2.write("\n")
            tf_2.close()

    def use_threading1(self, ai_image_result_path, ai_result, start_time1, photo_n, tp_id):
        self.save_ai_image(ai_image_result_path, start_time1, tp_id)
        # if len(after_pic_path) == 3:
        #     self.point_deal1(ai_result, start_time1, self.speed2, photo_n, tp_id, after_pic_path)
        # else:
        #     print("图片表数量：{}".format(len(after_pic_path)))

    def save_ai_image(self, data_ai, start_time1, tp_id):  # data_ai={相机号:[图片路径,点位信息],相机号:[图片路径,点位信息],相机号:[图片路径,点位信息]}
        try:
            self.after_pic_path = {}
            will_judge = []
            if self.havebox_path is not None:
                bool_record1 = 0
                if self.num_take_pic % 10 == 1:
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
                        ###数据库
                        list_6 = [tp_id, self.upload_path + path_, start_time1, 1]
                        id6_pic = write_mysql6(list_6)  # 录入图片表
                        # print("图片表ID：{}".format(id6_pic))
                        cam_num1 = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[camera_num]  # 相机号对应简单编号
                        self.after_pic_path[cam_num1] = id6_pic
                        #写.txt文件
                        tf1 = open(self.havebox_path + "/" + txt_name1, 'a')

                        list_message1 = []  # 单张图片中的点信息列表
                        bool_pic_label1 = [True] * len(self.label_path) #单张图中的label是否加过
                        for point_message1 in point_data_ori: #单张图中的每一个点信息
                            if point_message1["score"] >= aiCottonConfig.Classification_threshold:
                                level_point = "havebox"
                            else:
                                level_point = "suspected"
                            if bool_record1 > 0:
                                for i in range(len(self.label_path)): #point -label 计数记录 -需要间隔
                                    if bool_pic_label1[i] and point_message1["label"] == self.label_path[i]:
                                        self.list_num_label[i] += 1
                                        bool_pic_label1[i] = False
                                        bool_record1 += 1
                            point_re_mess1 = {"leftTopX": point_message1["x_min"], "leftTopY": point_message1["y_min"],
                                              "rightBottomX": point_message1["x_max"], "rightBottomY": point_message1["y_max"],
                                              "labelType": point_message1["label"], "labelMap": {
                                    "level": level_point,  "score": point_message1["score"]
                                }
                                              }
                            # print("图中的每个点：{}".format(point_re_mess1))
                            list_message1.append(point_re_mess1)
                            # 开始存信息
                        # print("写入文件时的点信息：{}".format(json.dumps(list_message1)))
                        tf1.write(json.dumps(list_message1))
                        tf1.close()
                        if bool_record1 > 0: #把每隔数次的可用 图片+txt cp 到upload路径
                            copy_path_upload = "cp -f " + self.havebox_path + "/" + path_ + " " + self.upload_path + "/"
                            copy_path_upload_txt = "cp -f " + self.havebox_path + "/" + txt_name1 + " " + self.upload_path + "/"
                            # print("copy_path_upload",copy_path_upload)
                            os.system(copy_path_upload)
                            # print("copy_path_upload_txt", copy_path_upload_txt)
                            os.system(copy_path_upload_txt)
                    else:
                        # print("copy_path_no", copy_path_no)
                        will_judge.append(path_)
                        os.system(copy_path_no)  # 复制到nobox,不做记录
                        ###数据库
                        list_6 = [tp_id, self.nobox_path + path_, start_time1, 0]
                        id6_pic = write_mysql6(list_6)
                        # print("图片表ID：{}".format(id6_pic))
                        cam_num1 = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[camera_num]
                        self.after_pic_path[cam_num1] = id6_pic
                    # logger.info("remove_path:{}".format(remove_path))
                    # os.system(remove_path)
                if bool_record1 > 1: #当1次拍照中有有用点产生时，写入计数记录
                    self.write_record_num_label()
                if self.num_take_pic % 10 == 1 and self.num_take_pic > 0:
                    # if len(will_judge) == 3:
                    logger5.info("第{}次--判别图中的羊毛 --无异纤图片数量：{}".format(self.num_take_pic, len(will_judge)))
                    self.name_judge_pic = copy.deepcopy(will_judge)
                    self.bool_judge_pic = True
                    # th1_pic = threading.Thread(target=self.judge_pic, args=(), name="judge_pic")
                    # th1_pic.start()
                logger4.info("存完图片表：返回{}--{}".format(len(self.after_pic_path), self.after_pic_path))
            # return after_pic_path
        except Exception as e:
            logger.info(f"err---saveimage: {e}")


    def point_deal1(self, ai_result, start_time, speeedas2, photo_n, id5_take_photo):
        if ai_result is not None:
            logger2.debug("AI result not checked is {}".format(ai_result))
            point_arr = caculate_nearly_point(ai_result)  # 舍去相机重合点
            if point_arr is not None:
                logger2.debug("the checked result is {}".format(point_arr))
                datapiont1 = self.remove_point2(point_arr, start_time, speeedas2)
                # print("@@@@@@@@@@@@@@-----({})---time:{}----speed:{}".format(photo_n,start_time,speeedas2))
                if datapiont1 is not None:
                    # logger4.info("the datapiont1 result is {}".format(datapiont1))
                    self.put_record2queue(datapiont1, start_time, speeedas2, photo_n, id5_take_photo)  # 将点写入队列（生产者调用）


    '''2021-06-03试写-写入数据库-独立线程'''
    def write_to_sql_thread(self):

        while True:
            try:
                num_empty_queue = 0
                if not self.queue_w_sql_tp.empty():
                    write_mysql5(self.queue_w_sql_tp.get())  #存拍照表
                if not self.queue_w_sql_image.empty():
                    write_mysql6(self.queue_w_sql_image.get())  #存图片表
                if not self.queue_w_sql_point.empty():
                    write_mysql(self.queue_w_sql_point.get())  #存点位表

            except Exception as e:
                logger.error(f"write_to_sql_thread  err: {e}")
                time.sleep(0.1)


    def search_empty(self, img, thre=150, zoom=0.2, num_thre=1500):
        try:
            if len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            H, W = img.shape[:2]
            W5 = int(W / 5)
            img = img[:, W5:W - W5]
            img = cv2.resize(img, (int(zoom * (W - 2 * W5)), int(zoom * H)), cv2.INTER_NEAREST)
            his = cv2.calcHist([img], [0], None, [255], [0, 256])
            if sum(his[thre:]) >= num_thre:
                return 1 #  有羊毛
            else:
                return 0
        except Exception as e:
            print('search_empty error: ', str(e))
            return 0

    def judge_pic_thread(self):
        th1_pic = threading.Thread(target=self.judge_pic, args=(), name="judge_pic")
        th1_pic.start()
    def judge_pic(self):

        bool_num_statu = [0, 0, 0]
        num_pic_none = 0
        num_pic_have = 0
        path_pic = None
        while True:
            try:
                if self.bool_judge_pic:
                    self.bool_judge_pic = False
                    logger5.info("第{}次--进入--判别图中的羊毛".format(self.num_take_pic))
                    num_once = 0
                    path_pic = copy.deepcopy(self.name_judge_pic)
                    if path_pic is not None:
                        for path1 in path_pic:
                            if os.path.exists(self.nobox_path + "/" + path1):
                                img_will = cv2.imread(self.nobox_path + "/" + path1)
                            else:
                                img_will = cv2.imread(self.havebox_path + "/" + path1)
                            result1 = self.search_empty(img_will)
                            num_once += result1
                        if num_once == 0:  # 3图 都是0，没有羊毛
                            num_pic_none += 1
                        else:
                            num_pic_have += 1

                    if num_pic_have > 4:
                        print("通过图像判断--有羊毛")
                        bool_num_statu[0] += 1
                        num_pic_none = 0
                        num_pic_have = 0


                    if num_pic_none > 2 and bool_num_statu[0] > 0:
                        print("通过图像判断--无羊毛")
                        bool_num_statu[1] += 1
                        num_pic_none = 0
                        num_pic_have = 0


                    if bool_num_statu[0] > 0 and bool_num_statu[1] > 0:
                        bool_num_statu[0] = 0
                        bool_num_statu[1] = 0
                        bool_num_statu[2] += 1
                        if bool_num_statu[2] % 2 == 1:  # 单次时，等于第一遍，需要转向，M1454= 1
                            self.write_sleep_data(3)
                            logger5.info("第{}次--向PLC发送‘1’-反转--计数列表:{}".format(self.num_take_pic, bool_num_statu))
                        else:
                            self.write_sleep_data(4)
                            logger5.info("第{}次--向PLC发送‘0’-正转--计数列表:{}".format(self.num_take_pic, bool_num_statu))
                    logger5.info("第{}次--无羊毛计数{}，有羊毛计数{}---计数列表:{}".format(self.num_take_pic,
                                                              num_pic_none, num_pic_have, bool_num_statu))
                else:
                    time.sleep(0.3)
            except Exception as e:
                print('judge_pic error: ', str(e))





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
        service = AiHjRunService()
        service.connect_plc()
        # service.init_service()  # 调用函数（初始化modbus,及相机）
        retry = 5
        start = time.time()
        t = threading.Thread(target=service.initCamera, args=(), name="camera_init_thread")
        t.start()
        time.sleep(5)
        logger.info("the camera init thread is {}".format(t.is_alive()))
        while retry > 0:
            logger.info("start to check camera init status")
            all_status = False
            ctrl_list = service.cameraCtrlList
            for k, v in ctrl_list.items():
                logger.info("the {} camera is {}".format(k, v.get("status", "---")))
                if v.get("status", "---") == "active":
                    all_status = True
                else:
                    all_status = False
            if all_status:
                break
            if time.time() - start > 30:
                logger.info("the camera list status: {}".format(ctrl_list))
                retry -= 1
                service.closeCamera()
                t = threading.Thread(target=service.initCamera, args=(), name="camera_init_thread_{}".format(retry))
                t.start()
                start = time.time()
            else:
                time.sleep(3)
        try:
            f = open(init_flag, "w+")
            f.write("success")
            f.close()
        except:
            logger.error("write init status error =======")
        service.start()
