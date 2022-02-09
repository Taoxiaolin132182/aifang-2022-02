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
from random import randint
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!This is probably because you need superuser privileges.")

# import share_func.utils
from share_func.utils import transform_conveyer_speed, time2long, long2time, find_grey_value, caculate_nearly_point
from share_func.utils import write_mysql, write_mysql2, write_mysql3, write_mysql4, write_mysql5, write_mysql6

from share_func.choose_arm import back_to_arm_num
arm_num = back_to_arm_num()
if arm_num == 1:
    from cfg1_need.image2world import image_points_to_world_plane
    import cfg1_need.config_armz as aicfg
elif arm_num == 2:
    from cfg2_need.image2world import image_points_to_world_plane
    import cfg2_need.config_armz as aicfg

# 添加包路径
START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, "..", "..", "ai-melsec-ctrl", "python"))
# sys.path.append(os.path.join(START_PY_PATH, "..", "..", "ai-device-ctrl", "python"))
sys.path.append(os.path.join(START_PY_PATH, "..", ".."))
sys.path.append(os.path.join(START_PY_PATH, "..", "call_code"))
if aicfg.If_decode_model:
    sys.path.append("/mnt/data/data/aimodel")
    import cfg_decode as mdcfg

del START_PY_PATH
# 需要导入的类
from aimodel.config import *
from aimodel.cameraModel import *
from aimodel.aiModel import *
from aimodel.tritonserver import *

from melsec_ctrl.melsec_ctrl import melsec_ctrl
from base import log
from base.timer_thread import simple_task_thread


logger = logging.getLogger('main')
logger2 = logging.getLogger('remover')
logger4 = logging.getLogger('recorder')
logger5 = logging.getLogger('rtemp')
logger6 = logging.getLogger('sql')
logger7 = logging.getLogger('needrecoed')
logger8 = logging.getLogger('yixrecord')
log.init_log("save_db")
log.info("===================================")


'''
2021-06-04---调用AI服务拍照+4抓手改造
2021-0702---调用AI、拍照类
2021-0811---合并arm1，arm2,以所在机器的mac地址做判别
2021-0818---增加颜色，详细类别
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
        self.bool_read_plc_time = [False, 0]  # 11-05 更换信号方式，便于for循环
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
        # [触摸屏IP(需要通讯时),第1抓取模组,第2抓取模组  2021-06-05 + 出棉机控制:10-15
        self.PLC_ctrl = [melsec_ctrl(), melsec_ctrl(), melsec_ctrl(), melsec_ctrl()]
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
        self.num_point_temp = 0  # 2021-08-02
        self.bool_record_count_qp_PLC = [False, False]  # 喷气的计数触发变量 2021-08-02
        self.bool_err_record = [False, False]  # PLC错误记录 2021-08-02
        self.num_err_record = 0  # 异常记录通讯更新标记 12_16-- 2021-08-02
        self.cameraModel = None  # 2021-06-18  全局变量--相机类
        self.detectionModel = [None, None]  # 2021-09-29  全局变量--AI类

        # 路径相关 2021-11-16
        '''[0]have-W, [1]no-W, [2]up-have-W, [3]up-no-W, 
           [4]have-UV, [5]no-UV, [6]up-have-UV, [7]up-no-UV'''
        self.pic_p_use = [None] * 8  # 照片存放路径
        self.save_pic_aipath = "/mnt/data/data/image_original/img_" + time.strftime("%Y_%m%d", time.localtime())

        self.__oPoolForRaster1 = ThreadPoolExecutor(9, "PoolForRasters")  # 线程池 2021-07-06
        self.__oPoolForRaster2 = processPool(8)  # 进程池 2021-07-06

        self.lock = threading.RLock()#队列线程锁，读写互斥，仅能进行一项
        self.bool_lock_time = False  # 读取PLC时间优先级判断

        # 2021-07-02--新建5*3个队列 | 08-13 建6*3个队列 | 11-04 建6*4个队列
        self.q_1st = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
        self.q_2nd = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
        self.q_3rd = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
        self.q_4th = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
        self.q_5th = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
        self.q_6th = [queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5), queue.Queue(maxsize=5)]
        self.queue_all = [self.q_1st, self.q_2nd, self.q_3rd, self.q_4th, self.q_5th, self.q_6th]
        self.list_zh1 = {}  # 2021-07-02 重制限制类别列表
        self.queue_gas = queue.Queue(maxsize=60)
        self.sql_point_queue = queue.Queue(maxsize=30)  # 点数据的存放队列
        self.sql_err_queue = queue.Queue(maxsize=30)  # PLC错误记录的存放队列

        self.new_add_global_variables = [False, False, False, False, False, False]
        '''
        [0] = 光源图片检测的信号  -- 2021.08.09
        [1] = 发送程序异常(相机，AI，光源)  -- 2021.08.09
        [2] = 按规则上传的信号  -- 2021.08.09
        [3] = 按规则上传nobox的信号  -- 2021.11.10
        '''
        self.new_add_global_data = [[], 0, [], [], []]
        '''
        [0] = 光源检测的图片名 (列表) -- 2021.08.09
        [1] = 异常代码 (计数) -- 2021.08.09
        [2] = 按规则上传-数据 (列表)-- 2021.08.09
        [3] = 按规则上传nobox-数据 (列表)-- 2021.11.10
        '''
        self.label_path = ["level-1", "level-2", "level-3", "level-4", "level-5"]  # 上传规则-等级-2021.08.09
        self.list_num_label = [[0, 0, 0, 0, 0], [500, 500, 500, 500, 500]]  # 上传规则-数量-2021.08.09
        self.grab_gohome_count = [0, 0, 0, 0]  # 抓手抓取次数计数，来判断是否需要回原点 -2021.08.11
        #相机引脚号
        self.White_light = 13  # 白光 引脚
        self.UV_light = 12  # 紫外 引脚
        #GPIO初始化
        GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.White_light, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.UV_light, GPIO.OUT, initial=GPIO.LOW)
        # #输入高低电平
        self.bool_ctrl_light1 = [False, False]  # 灯光控制[白光，紫光]
        self.light_num1 = 1  # 对应处理函数的结果控制变量[白光[0]，紫光[1]]

        self.speed2 = aicfg.Speed_of_csd #单位M/s(覆盖的参数是mm/s)
        self.dataZ1 =[]#去重数据组
        self.choose_model1 = aicfg.Choose_label #默认异纤种类（#0,异纤  1，异纤+脏棉）
        self.num_changeda = 0
        self.bool_xfz = False
        self.num_err_record = 0 #异常记录通讯更新标记 12_16
        self.times_queue2 = 0
        # 若要处理一些定时任务，比如自动删除旧的数据，需要开启下面定时任务线程
        self.oTaskThread = simple_task_thread("simple_task")
        self.oTaskThread.start()
        self.batch_cotton = ""
        self.save_pic_name1 = []  # 存图的路径+名称
        self.after_pic_path = {}  # 存入图片表后返回的ID
        self.result_takepic_sort = []
        self.bool_up_to_standard = False  # 异纤数量-达标信号 2021_09_22
        # self.change_camera_param = None  # 改变相机参数  2021_09_26
        self.list_cam_param = [[], []]  # 相机参数列表 [[白光参数],[紫光参数]]  2021_09_26
        self.c_p = None  # 获取配置文件  2021_09_26

    # ---------------初始化部分-------------
    '''--------2021-06-05 由配置选择要连接的PLC----------'''
    def connect_plc(self):  # 2021-06-05 由配置选择要连接的PLC

        plc_port = aicfg.PLC_port
        plc_ctrl_list = aicfg.PLC_ctrl_choose
        plc_ip_list = [aicfg.PLC_ip_main, aicfg.PLC_ip_frist, aicfg.PLC_ip_second, aicfg.PLC_ip_third]

        for plc_i in range(len(plc_ctrl_list)):
            if plc_ctrl_list[plc_i] == 1:
                bool_plc1 = True
                num_plc1 = 0
                while bool_plc1:
                    time.sleep(0.1)
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
        plc_ctrl_list = aicfg.PLC_ctrl_choose
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
        name1 = aicfg.MELSEC_CODE.ZI_TEST1
        data = [123, 456, 789, 1024]
        name2 = aicfg.MELSEC_CODE.ZJ_XINHAO
        data2 = [88]
        result1 = self.PLC_ctrl[aicfg.Run_choose[1]].write_dword_data(name1, data)  # 写入
        if result1 is not None:
            logger7.info("数据写入PLC 成功")
            time.sleep(0.3)
            result2 = self.PLC_ctrl[aicfg.Run_choose[1]].read_dword_data(name1, 4)  # 读取
            if result2 is not None:
                logger7.info("读取PLC 成功")
                logger7.info("PLC起始地址：{}，数据为{}".format(name1, result2))
                time.sleep(0.3)
                data = [222, 222, 222, 222]
                self.PLC_ctrl[aicfg.Run_choose[1]].write_dword_data(name1, data)  # 写入重置
                self.PLC_ctrl[aicfg.Run_choose[1]].write_dword_data(name2, data2)  # 写入重置自检信号位
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
        plc_ctrl_list = aicfg.PLC_ctrl_choose

        name1 = aicfg.MELSEC_CODE.ARM_XINHAO
        name2 = aicfg.MELSEC_CODE.START_OK
        name3 = aicfg.MELSEC_CODE.PENQI
        name4 = aicfg.MELSEC_CODE.CSD_SPEED1
        name5 = aicfg.MELSEC_CODE.CHOOSE_MODEL
        name6 = aicfg.MELSEC_CODE.STOP_ALL1

        name7 = aicfg.MELSEC_CODE.TONGS_STATUS1
        name8 = aicfg.MELSEC_CODE.TONGS_STATUS2
        name9 = aicfg.MELSEC_CODE.MELSEC_TIME_SEC

        name10 = aicfg.MELSEC_CODE.GRAB_TIME_SEC1
        name11 = aicfg.MELSEC_CODE.GRAB_TIME_SEC2

        name12 = aicfg.MELSEC_CODE.TONGS_HOMING1
        name13 = aicfg.MELSEC_CODE.TONGS_HOMING2

        name14 = aicfg.MELSEC_CODE.ZJ_XINHAO
        arm_err = [0, 0, 0]  # 异常的计数
        time_err = [time.time(), time.time()]
        need_close = False

        name20 = aicfg.PLC_address.Point_record  # 发送PLC现在的识别个数 信号
        name21 = aicfg.PLC_address.Clear_num_record  # 点的清零
        backup_num = -1  # 备份计数，防止同数写入

        name22 = aicfg.PLC_address.Err_record  # PLC 异常记录初始位
        name23 = aicfg.PLC_address.Err_status  # 异常记录更新位（有变化才写入）

        name24 = aicfg.PLC_address.Up_to_standard  # 异纤检测数量--达标信号

        bool_ctrl_print = False  # 方便计算一次循环中到指定部分运行完，所花费的时间
        while True:
            try:
                t1 = time.time()

                '''程序异常通知信号'''
                if self.new_add_global_variables[1]:
                    self.new_add_global_variables[1] = False

                    if self.new_add_global_data[1] == 11:  # 相机异常
                        if time.time() - time_err[0] > 30:  # 间隔30秒以上
                            self.new_add_global_data[1] = 88; arm_err[0] = 0  # 计数清零
                            logger7.info("=====相机异常_与上一次超过30秒，计数清零")
                        else:
                            arm_err[0] += 1; logger7.info("=====相机异常_与上一次少于30秒，计数+1")
                            if arm_err[0] > 3:
                                arm_err[0] = 0; need_close = True
                                self.PLC_ctrl[aicfg.Run_choose[1]].write_dword_data(name14,
                                                                                    [self.new_add_global_data[1]])
                                logger7.info("============检测到 相机连续异常多次 关闭程序，等待重启==========")
                        time_err[0] = time.time()  # 刷新最新的--相机异常时间
                    elif self.new_add_global_data[1] == 22:  # AI异常
                        if time.time() - time_err[1] > 30:  # 间隔30秒以上
                            self.new_add_global_data[1] = 88; arm_err[1] = 0  # 计数清零
                        else:
                            arm_err[1] += 1
                            if arm_err[1] > 3:
                                arm_err[1] = 0; need_close = True
                                self.PLC_ctrl[aicfg.Run_choose[1]].write_dword_data(name14,
                                                                                    [self.new_add_global_data[1]])
                                logger7.info("============检测到 AI连续异常多次 关闭程序，等待重启==========")
                        time_err[1] = time.time()  # 刷新最新的--AI异常时间
                    else:
                        # 写入自检信号位
                        self.PLC_ctrl[aicfg.Run_choose[1]].write_dword_data(name14, [self.new_add_global_data[1]])
                        if need_close:
                            time.sleep(10); os._exit(0)
                    if self.new_add_global_data[1] != 88:  # 根据规则，写完还需要写一次88 来覆盖
                        self.new_add_global_data[1] = 88
                        self.new_add_global_variables[1] = True

                '''读取是否需要清零-识别数量'''
                if self.bool_record_count_qp_PLC[1]:
                    self.bool_record_count_qp_PLC[1] = False
                    res_21 = self.PLC_ctrl[aicfg.Run_choose[1]].read_bit_data(name21, 1)
                    if (res_21[0] == "1") or (res_21[0] == 1):
                        self.num_point_temp = 0
                        self.bool_record_count_qp_PLC[0] = True
                '''写入点的识别数量'''
                if self.bool_record_count_qp_PLC[0]:
                    self.bool_record_count_qp_PLC[0] = False
                    if self.num_point_temp != backup_num:
                        backup_num = copy.deepcopy(self.num_point_temp)
                        self.PLC_ctrl[aicfg.Run_choose[1]].write_word_data(name20, [self.num_point_temp])


                '''命令PLC控制喷气'''
                if self.bool_circulation_qp_PLC:  # 循环时的通知PLC喷气
                    self.bool_circulation_qp_PLC = False
                    if not self.pqlist_queue.empty():
                        # if True:
                        send_data = self.pqlist_queue.get()
                        self.PLC_ctrl[aicfg.Run_choose[1]].write_word_data(name3, send_data[1])
                        print("消费者--penqi--to-PLC:time{}--{}".format(time.time(), send_data))

                '''循环触发读取-异常记录更新位（有变化才写入）'''
                if self.bool_err_record[0]:
                    self.bool_err_record[0] = False
                    result23 = self.PLC_ctrl[aicfg.Run_choose[1]].read_word_data(name23, 1)
                    status_send = int(result23[0])
                    # logger7.info("异常记录更新位:{}".format(status_send))
                    if status_send != self.num_err_record:  # 对比前一次变化
                        self.num_err_record = copy.deepcopy(status_send)
                        self.bool_err_record[1] = True  # 有变化时，读入记录
                '''读取-异常记录异常记录初始位+ 33位'''
                if self.bool_err_record[1]:
                    self.bool_err_record[1] = False
                    result22 = self.PLC_ctrl[aicfg.Run_choose[1]].read_bit_data(name22, 33)
                    logger7.info("异常记录表:{}".format(result22))
                    if not self.sql_err_queue.full():
                        self.sql_err_queue.put(result22)
                '''读取抓手状态'''
                if self.bool_read_claw_state:
                    self.bool_read_claw_state = False
                    if self.num_claw_state == 2:
                        res1 = self.PLC_ctrl[aicfg.Run_choose[1]].read_bit_data(name7, 3)
                        res2 = self.PLC_ctrl[aicfg.Run_choose[1]].read_bit_data(name8, 3)
                        # print("res1:{}   res2:{}".format(res1, res2))
                        self.list_claw_state = [res1[0], res1[2], res2[0], res2[2],
                                                1, 1, 1, 1]
                    elif self.num_claw_state == 4:
                        # print("----@@@@@@@@消费者---读取抓手状态  时间戳   ：{}".format(time.time()))
                        res1 = self.PLC_ctrl[aicfg.Run_choose[1]].read_bit_data(name7, 3)
                        res2 = self.PLC_ctrl[aicfg.Run_choose[1]].read_bit_data(name8, 3)
                        res3 = self.PLC_ctrl[aicfg.Run_choose[2]].read_bit_data(name7, 3)
                        res4 = self.PLC_ctrl[aicfg.Run_choose[2]].read_bit_data(name8, 3)
                        self.list_claw_state = [res1[0], res1[2], res2[0], res2[2],
                                                res3[0], res3[2], res4[0], res4[2]]
                '''读取PLC时间戳'''
                if self.bool_read_plc_time[0]:
                    i_p = 1 if self.bool_read_plc_time[1] < 3 else 2
                    # print("----@@@@@@@@消费者---获取PLC时间戳(前)   ：{}".format(time.time()))
                    result = self.PLC_ctrl[aicfg.Run_choose[i_p]].read_dword_data(name9, 2)
                    # print("----@@@@@@@@消费者---获取PLC时间戳(中)   ：{}".format(time.time()))
                    self.time_arm = time.time()
                    self.time_plc = time2long(result[0], result[1])
                    self.bool_read_plc_time = [False, 0]  # 同样也是调用处标记
                    # print("plc_time:{}".format(result))
                    # print("plc_time:{}--{}".format(result[0], result[1]))
                    # print("----@@@@@@@@消费者---获取PLC时间戳(后)   ：{}".format(time.time()))

                '''写入PLC-抓取时刻'''
                if self.bool_send_toPLC_claw:

                    if self.send_toPLC_list[0] == 1:
                        # print("----@@@@@@@@消费者---抓手1---写入PLC时间戳：{}---#################".format(time.time()))
                        self.PLC_ctrl[aicfg.Run_choose[1]].write_dword_data(name10, self.send_toPLC_list[1:])
                    elif self.send_toPLC_list[0] == 2:
                        self.PLC_ctrl[aicfg.Run_choose[1]].write_dword_data(name11, self.send_toPLC_list[1:])
                    elif self.send_toPLC_list[0] == 3:
                        # print("----@@@@@@@@消费者---抓手3---写入PLC时间戳：{}---#################".format(time.time()))
                        self.PLC_ctrl[aicfg.Run_choose[2]].write_dword_data(name10, self.send_toPLC_list[1:])
                    elif self.send_toPLC_list[0] == 4:
                        self.PLC_ctrl[aicfg.Run_choose[2]].write_dword_data(name11, self.send_toPLC_list[1:])
                    logger7.info("发送给PLC的数据为：{}".format(self.send_toPLC_list))
                    self.bool_send_toPLC_claw = False

                    bool_ctrl_print = True
                '''抓手归零-重建OP信号'''
                if self.bool_claw_goback:
                    self.bool_claw_goback = False
                    if self.num_plc_goback == 1:
                        self.PLC_ctrl[aicfg.Run_choose[1]].write_bit_data(name12, [1])
                    elif self.num_plc_goback == 2:
                        self.PLC_ctrl[aicfg.Run_choose[1]].write_bit_data(name13, [1])
                    elif self.num_plc_goback == 3:
                        self.PLC_ctrl[aicfg.Run_choose[2]].write_bit_data(name12, [1])
                    elif self.num_plc_goback == 4:
                        self.PLC_ctrl[aicfg.Run_choose[2]].write_bit_data(name13, [1])

                '''循环时的PLC--心跳'''
                if self.bool_circulation_process_PLC:  # 循环时的PLC断连信号
                    data2 = [self.num_changed1()]
                    self.PLC_ctrl[aicfg.Run_choose[1]].write_word_data(name1, data2)  # 写入自检信号位-断连状态
                    self.bool_circulation_process_PLC = False
                '''向PLC写入开始信号'''
                if self.bool_start_signal_PLC:  # 05-19 向PLC写入开始信号(传送带转起来)
                    for plc_i in range(len(plc_ctrl_list)):
                        if plc_ctrl_list[plc_i] == 1:
                            self.PLC_ctrl[plc_i].write_bit_data(name2, [1])
                    self.bool_start_signal_PLC = False
                    logger7.info("向PLC   M50写入 1 ---表示程序一开始")
                '''接受PLC 发送的暂停指令'''
                if self.bool_ctrl_stop:
                    # print("----@@@@@@@@消费者--暂停指令---时间戳：{}".format(time.time()))
                    self.if_need_stop = self.PLC_ctrl[aicfg.Run_choose[1]].read_bit_data(name6, 1)[0]  # PLC 发送的暂停指令
                    self.bool_ctrl_stop = False
                '''获取传送带速度'''
                if self.bool_get_speed_PLC:  # 05-19 获取传送带速度
                    cds_speed = self.PLC_ctrl[aicfg.Need_time_PLC].read_dword_data(name4, 1)[0]  # 根据设备情况，指定PLC

                    self.speed2 = transform_conveyer_speed(cds_speed)  # 写入速度
                    # self.speed2 = 170.66  # 写入速度--对应传送带频率2300*0.0742
                    logger7.info("----@@@@第{}次拍照时，传送带速度{}--频率：{}".format(self.photo_n, self.speed2, cds_speed))
                    # self.speed2 = 1179.57
                    # self.speed2 = 500
                    # print("检测到现在传送带速度为：{} mm/s".format(self.speed2))
                    self.bool_get_speed_PLC = False

                '''异纤数量-达标信号'''
                if self.bool_up_to_standard:  # 异纤数量-达标信号
                    self.bool_up_to_standard = False
                    self.PLC_ctrl[aicfg.Run_choose[3]].write_bit_data(name24, [1])

                if not self.bool_xfz:
                    '''获取批次号'''
                    if self.bool_get_batch_PLC:  # 05-19 获取批次号 用的self.PLC_ctrl[1]
                        self.get_batch(False)
                        self.bool_get_batch_PLC = False

                    '''取识别种类'''
                    if self.bool_get_label_PLC:  # 05-19 获取识别种类
                        bReadData = self.PLC_ctrl[aicfg.Run_choose[1]].read_word_data(name5, 1)
                        self.choose_model1 = bReadData[0]
                        logger7.info("读取异纤识别种类:{}".format(self.choose_model1))
                        self.bool_get_label_PLC = False
                    '''自检--心跳'''
                    if self.bool_check_process_PLC:  # 05-19 自检过程中，和PLC保持通讯
                        data2 = [self.num_changed1()]
                        # logger.info("自增数：{}".format(str(data2[0])))
                        print("name:{},data:{}".format(name1, data2))
                        self.PLC_ctrl[aicfg.Run_choose[1]].write_word_data(name1, data2)  # 写入自检信号位-断连状态
                        time.sleep(0.5)
                if bool_ctrl_print:
                    bool_ctrl_print = False
                    print("第{}次拍照期间，线程循环时间：{}".format(self.photo_n, time.time() - t1))
                time.sleep(0.001)
            except Exception as e:
                logger.error(f"err -- keep_connection_to_PLC: {e}")
                logger.info("由于与 PLC通讯问题，退出程序")
                time.sleep(0.1)
                os._exit(0)  # PLC 写入不成功，则关闭程序

    # ---------------自检部分-------------
    '''自检总览'''
    def frist_check_AI(self):
        print("进入自检")
        logger7.info("进入自检")

        if aicfg.If_need_PLC:
            self.check_PLC()  # 自检PLC连接
            self.bool_check_process_PLC = True  # 开始和PLC通讯连接信号  --不会停止
            self.connect_PLC_thread()  # 开线程-发送PLC连接通断信号
        print("开线程-写入点位表")
        self.use_thread_sql1()  # 开线程-写入点位表
        # 控制灯光交替线程--搜索间隔10ms
        if aicfg.Ctrl_light:  # 控制灯光交替线程--是否需要开启线程
            th4_signal = threading.Thread(target=self.ctrl_light_alternate, args=(), name="ctrl_light_alternate")
            th4_signal.start()
        else:
            GPIO.output(self.White_light, GPIO.HIGH)  # 触发高电平-(放大板灯灭)-白光亮
            logger7.info("白光常亮")
        self.ai_server_start_v2()  # AI部分服务启动(模型和相机)

        self.create_file_path1()  # 创建文件路径，每日刷新，检查本地与网络时间
        test_name1 = 2
        if test_name1 > 10:
            self.test_takepic_AI_v2()  # 测试函数 -- 指定特定的光源和相机参数 测试拍照
        self.check_takepic_AI_v2()  # 自检拍照和AI识别
        self.remove_model_file()  # 删除模型文件
        if aicfg.If_need_PLC:
            self.bool_start_signal_PLC = True  # 05-19 向PLC写入开始信号(传送带转起来)
            self.bool_get_batch_PLC = True  # 05-19 获取批次号
            self.bool_get_label_PLC = True  # 05-19 获取识别种类
            self.bool_ctrl_stop = True  # 05-21 看是否需要暂停-测试
            time.sleep(3.5)
            pre_sp1 = 0
            for f_i in range(30):
                time.sleep(0.8)
                self.bool_get_speed_PLC = True  # 05-19 获取传送带速度
                while self.bool_get_speed_PLC:
                    time.sleep(0.05)
                if self.speed2 > aicfg.Speed_of_csd * 0.8:  # 增加传送带速度近似值判断
                    if pre_sp1 == self.speed2:
                        break
                    else:
                        pre_sp1 = copy.deepcopy(self.speed2)
        self.read_limit_label()  # 录入 应筛选的类别
        self.create_or_read_upload_record()  # 记录或读取 上传记录
        # 一般信号触发函数(光源判断，上传图片及记录)
        th3_signal = threading.Thread(target=self.thread_recevived_signal, args=(), name="thread_recevived_signal")
        th3_signal.start()
        # th5_record = threading.Thread(target=self.record_point_count, args=(), name="record_point_count")
        # th5_record.start()

        print("自检完成")
        logger7.info("自检完成")

    '''AI部分服务启动(模型和相机)'''
    def ai_server_start_v2(self):
        num_camera_init = 0

        # 模型初始化
        logger7.info("start init Triton_server")
        model_path1 = aicfg.AI_model_cfg_path  # 加载配置文件路径
        name_aifile = model_path1.split("/")[-2]
        print("加载的模型文件为：{}".format(name_aifile))
        logger7.info("加载的模型文件为：{}".format(name_aifile))
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
            logger7.info("start init ai_model")
            if aicfg.AI_model_choose == 1:
                self.detectionModel[0] = model_detection_core(model_config)
            elif aicfg.AI_model_choose == 2:
                self.detectionModel[0] = model_atss_detection(model_config)
            elif aicfg.AI_model_choose == 3:
                self.detectionModel[0] = model_detection_wool_double(model_config)
            elif aicfg.AI_model_choose == 4:
                self.detectionModel[0] = model_detection_wool_single(model_config)
            else:
                print("请对应配置文件, 缺失：AI/AI_model_choose")
                logger7.info("请对应配置文件, 缺失：AI/AI_model_choose")
                sys.exit(0)
            logger7.info("检测模型初始化:{}".format(aicfg.AI_model_choose))
            if aicfg.Ctrl_light:  # 控制灯光交替线程--是否需要开启线程
                self.detectionModel[1] = fluorescence_model()
                print("检测UV模型初始化")
                logger7.info("检测UV模型初始化")
            # 相机初始化
            logger7.info("start init camera")
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

            '''只有初始化相机后，才能调用设置相机参数的函数'''
            if aicfg.Ctrl_light:  # 控制灯光交替线程--是否需要开启线程
                c_p = aicfg.Camera_param_change  # 读出配置文件中的参数
                for ic in range(len(c_p) - 1):  # (按相机个数分) 加了一组key-name，所以要 -1
                    cp_in1, cp_in2 = {}, {}  # "param" 的 值，不相同时录入，相同时不录入(但要人工确保和cfg.py 上的相关参数一致)
                    for icn in range(len(c_p[ic])):  # 某个相机对应的参数个数
                        if c_p[ic][icn][0] != c_p[ic][icn][1]:  # 参数值不相等时
                            cp_in1.update({c_p[-1][icn]: c_p[ic][icn][0]})  # "param" 的 值
                            cp_in2.update({c_p[-1][icn]: c_p[ic][icn][1]})  # "param" 的 值
                    if len(cp_in1) > 0:  # 当参数有不同时，录入
                        cpnow1 = {'sn': aicfg.Camera_id[ic][0], 'param': cp_in1}  # CP 的 格式
                        cpnow2 = {'sn': aicfg.Camera_id[ic][0], 'param': cp_in2}  # CP 的 格式
                        self.list_cam_param[0].append(cpnow1)
                        self.list_cam_param[1].append(cpnow2)
                print("整理后，相机需要刷入的参数列表：{}".format(self.list_cam_param))
                logger7.info("整理后，相机需要刷入的参数列表：{}".format(self.list_cam_param))
            time.sleep(1)
        except Exception as e:
            logger7.error(f"init -error: {e}")
            logger7.info("初始化失败 --退出程序")
            time.sleep(0.25)
            os._exit(0)

    '''自检拍照和AI识别'''
    def check_takepic_AI_v2(self):

        t2 = time.time()
        bool_take_pic = False  # 拍照结果--信号，False:可以进行存图、aiInfer
        self.bool_ai_infer += 11
        for i in range(4):
            try:
                # 等待一段时间(拍摄周期)
                t1 = time.time()  # 上一次循环结束的时间戳
                l_t1 = round((1 - (t1 - t2)), 3)
                if l_t1 > 0:
                    time.sleep(l_t1)
                logger.info("自检-第{}次循环开始".format(str(i + 1)))

                t2 = time.time()
                # 调用拍照
                if aicfg.Ctrl_light:
                    self.light_num1 = 1 - self.light_num1  # 信号 0-1 交换
                    self.bool_ctrl_light1[self.light_num1] = True  # 光源触发
                    if len(self.list_cam_param[0]) > 0:  # 当有相机参数不同时[0][1] 的 len 一致
                        for cam_p1 in self.list_cam_param[self.light_num1]:  # 某光的具体参数
                            self.cameraModel.dfsGetPhoto.setCameraParamManu(cam_p1)  # 设入参数
                else:
                    self.light_num1 = 0  # 信号，强制为白光
                time.sleep(aicfg.Wait_light_time)  # 为确保灯光亮度达到合适的--等待时间
                self.result_takepic_sort = []  # 清空拍照后的图片名
                list_tp = [{"id": i, "time_tp": t2}]  # 传入拍照进程 所需参数
                self.__oPoolForRaster1.submit(self.tp_try, list_tp)  # 拍照进程
                bool_take_pic = False  # 默认拍照OK
                while len(self.result_takepic_sort) < len(aicfg.Camera_id):  # 等待拍照后图片名回传
                    time.sleep(0.005)
                    if time.time() - t2 > aicfg.Frame_time + 0.6:  # 相机 拍照 超时
                        bool_take_pic = True  # 拍照 NG 信号
                        break
                # 调用AI
                t3 = time.time()
                if not bool_take_pic:  # 拍照成功
                    print("开启存图线程")
                    logger7.info("开启存图线程")
                    list_save_pic1 = {"tp_num": i, "tp_end_time": t3, "pic_name": self.result_takepic_sort}
                    self.__oPoolForRaster1.submit(self.call_ai_savepic_service_v2, list_save_pic1)
                    print("开启AIinfer线程")
                    logger7.info("开启AIinfer线程")
                    # self.call_ai_trigger_data1_v2(i, t1, 0, 1, result_takepic) #现在强制为True
                    self.__oPoolForRaster1.submit(self.call_ai_trigger_data1_v2, i, t3, 0, 1, self.result_takepic_sort)
                    if i == 0:
                        time.sleep(8)
                    time.sleep(2)
            except Exception as e:
                logger7.error(f"check_takepic_AI_v2 -error: {e}")
                logger7.info("自检失败 --准备退出程序")
                time.sleep(0.25)


    '''紫光交替参数拍摄'''
    def test_takepic_AI_v2(self):
        self.White_light = 13
        self.UV_light = 13  # 紫外 引脚
        self.list_cam_param = [
            [{'sn': aicfg.Camera_id[0][0], 'param': {'Gain': 10.0, 'Exposure': 20000}},
                {'sn': aicfg.Camera_id[1][0], 'param': {'Gain': 10.0, 'Exposure': 20000}},
                {'sn': aicfg.Camera_id[2][0], 'param': {'Gain': 10.0, 'Exposure': 20000}},],
            [{'sn': aicfg.Camera_id[0][0], 'param': {'Gain': 10.0, 'Exposure': 10000}},
                {'sn': aicfg.Camera_id[1][0], 'param': {'Gain': 10.0, 'Exposure': 10000}},
                {'sn': aicfg.Camera_id[2][0], 'param': {'Gain': 10.0, 'Exposure': 10000}},]]

        GPIO.output(self.White_light, GPIO.HIGH)  # 触发高电平-(放大板灯灭)-白光亮
        time.sleep(1)
        for cam_p1 in self.list_cam_param[0]:
            self.cameraModel.dfsGetPhoto.setCameraParamManu(cam_p1)
        time.sleep(1)
        t2 = time.time()
        bool_take_pic = True  # 拍照结果--信号，False:可以进行存图、aiInfer
        self.bool_ai_infer += 11
        for i in range(8000):
            # 等待一段时间(拍摄周期)
            t1 = time.time()  # 上一次循环结束的时间戳
            l_t1 = round((1 - (t1 - t2)), 3)
            if l_t1 > 0:
                time.sleep(l_t1)
            logger.info("自检-第{}次循环开始".format(str(i + 1)))

            t2 = time.time()
            # 调用拍照
            tt_Ctrl_light = False  # False | True
            if tt_Ctrl_light:
                self.light_num1 = 1 - self.light_num1  # 信号 0-1 交换
                self.bool_ctrl_light1[self.light_num1] = True  # 光源触发
                if len(self.list_cam_param[0]) > 0:  # 当有相机参数不同时[0][1] 的 len 一致
                    for cam_p1 in self.list_cam_param[self.light_num1]:  # 某光的具体参数
                        self.cameraModel.dfsGetPhoto.setCameraParamManu(cam_p1)  # 设入参数
            else:
                self.light_num1 = 0  # 信号，强制为白光
            time.sleep(aicfg.Wait_light_time)  # 为确保灯光亮度达到合适的--等待时间
            self.result_takepic_sort = []  # 清空拍照后的图片名
            list_tp = [{"id": i, "time_tp": t2}]  # 传入拍照进程 所需参数
            self.__oPoolForRaster1.submit(self.tp_try, list_tp)  # 拍照进程
            bool_take_pic = False  # 默认拍照OK
            while len(self.result_takepic_sort) < len(aicfg.Camera_id):  # 等待拍照后图片名回传
                time.sleep(0.005)
                if time.time() - t2 > aicfg.Frame_time + 0.6:  # 相机 拍照 超时
                    bool_take_pic = True  # 拍照 NG 信号
                    break
            # 调用AI
            t3 = time.time()
            if not bool_take_pic:  # 拍照成功
                print("开启存图线程")
                logger7.info("开启存图线程")
                list_save_pic1 = {"tp_num": i, "tp_end_time": t3, "pic_name": self.result_takepic_sort}
                self.__oPoolForRaster1.submit(self.call_ai_savepic_service_v2, list_save_pic1)

                print("第{}次，已拍完，可以开门操作".format(i + 1))
                time.sleep(30)
                print("第{}次，还要10秒，请关门".format(i + 1))
                time.sleep(10)

    def remove_model_file(self):
        if aicfg.If_decode_model:  # 是否需要删除模型
            logger7.info("准备删除对应模型的原始文件")
            model_file_path1 = mdcfg.path_job + mdcfg.path_model + mdcfg.model_last_name[1]
            code1 = "rm -f " + model_file_path1 + " &"
            if os.path.exists(model_file_path1):
                os.system(code1)
                logger7.info("{}:该原始模型文件1已删除".format(model_file_path1))
            if mdcfg.model_count > 1:
                model_file_path2 = mdcfg.path_job + mdcfg.path_model_add + mdcfg.model_last_name_add[1]
                code2 = "rm -f " + model_file_path2 + " &"
                if os.path.exists(model_file_path2):
                    os.system(code2)
                    logger7.info("{} 该原始模型文件2已删除".format(model_file_path2))
            time.sleep(0.5)



    '''创建文件路径，每日刷新'''
    def create_file_path1(self):
        date_today = self.check_date_time()  # 检查本地时间和网络时间
        if date_today is not None:
            self.save_pic_aipath = "/mnt/data/data/image_original/img_" + date_today
            date_path1 = date_today + "_inter"
        else:
            date_path1 = time.strftime("%Y_%m%d", time.localtime()) + "_lost"
        date_path2 = aicfg.Path_upload + date_path1

        pre_path_list1 = ["/mnt/data/data/image_original/", "/mnt/data/data/upload_image/", "/mnt/data/data/image/",
                          "/mnt/data/data/image/havebox/", "/mnt/data/data/image/nobox/"]
        '''[0]have-W, [1]no-W, [2]up-have-W, [3]up-no-W, 
           [4]have-UV, [5]no-UV, [6]up-have-UV, [7]up-no-UV'''
        self.pic_p_use[0] = os.path.join(pre_path_list1[3], date_path2 + "_W")
        self.pic_p_use[1] = os.path.join(pre_path_list1[4], date_path2 + "_W")
        self.pic_p_use[2] = os.path.join(pre_path_list1[1], date_path2 + "_have_W")
        self.pic_p_use[3] = os.path.join(pre_path_list1[1], date_path2 + "_no_W")
        if aicfg.Ctrl_light:
            self.pic_p_use[4] = os.path.join(pre_path_list1[3], date_path2 + "_UV")
            self.pic_p_use[5] = os.path.join(pre_path_list1[4], date_path2 + "_UV")
            self.pic_p_use[6] = os.path.join(pre_path_list1[1], date_path2 + "_have_UV")
            self.pic_p_use[7] = os.path.join(pre_path_list1[1], date_path2 + "_no_UV")

        for ip in range(len(pre_path_list1) + len(self.pic_p_use) + 1):
            if ip < len(pre_path_list1):
                path_p1 = pre_path_list1[ip]
            else:
                if ip == len(pre_path_list1):
                    path_p1 = self.save_pic_aipath
                else:
                    path_p1 = self.pic_p_use[ip - len(pre_path_list1) - 1]
                logger7.info("pic_path({})：{}".format(ip + 1 - len(pre_path_list1), path_p1))
            if path_p1 is None:
                break
            else:
                if not os.path.exists(path_p1):
                    os.makedirs(path_p1)
        for iph in range(len(pre_path_list1) - 2):
            chmod_code1 = "chmod -R 777 " + pre_path_list1[iph] + " &"
            os.system(chmod_code1)

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
            if list_num1[0] >= 1:
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
                    now_date = time.strftime("%Y_%m%d", time.localtime(beijinTime))
                    list_num1[1] = False  # 跳出 internet 循环
            except Exception as e:
                logger7.info(f"err---internet: {e}")
                time.sleep(1)

        while list_num1[3]:  # check_time 循环信号
            time.sleep(0.001)
            if list_num1[2] >= 30:  # 失败计数
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
                        now_date = time.strftime("%Y_%m%d", time.localtime())
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
        count_stop_time = 0
        self.bool_ai_infer += 11
        if aicfg.Mechine_function == "claw":
            self.choose_mechine_model = 1  # 2021-0607 抓手模式
        else:
            self.choose_mechine_model = 2  # 2021-0607 喷气模式
        # 循环开始
        while True:
            try:
                time.sleep(0.001)
                if aicfg.Bool_sleep_produce:
                    time.sleep(aicfg.Sleep_time_produce)
                '''被PLC暂停后的操作：保持通讯心跳，监测暂停信号的恢复'''
                # print("暂停信号：{}".format(self.if_need_stop))
                # print("传送带速度：{}".format(self.speed2))
                # self.if_need_stop = 1  # 强制为 运行 信号
                # self.speed2 = 500
                if self.if_need_stop == 0:  # PLC控制待机 0-待机，1-正常运行
                    if not change_model1:
                        logging.info("---生产者---PLC通知设备停机-暂停")
                    change_model1 = True
                    count_stop_time += 1
                    if count_stop_time % 10 == 1:
                        self.bool_err_record[0] = True  # 触发读取PLC异常信息
                        self.bool_circulation_process_PLC = True  # 开始和PLC通讯连接信号
                    self.bool_ctrl_stop = True  # 读取是否需要暂停 --暂停时生产者控制，运行时消费者控制
                    time.sleep(0.6)
                    if count_stop_time % 20 == 1:
                        print("---生产者---PLC通知设备停机-暂停")
                    # 需要清空所有队列 self.record_queue.queue.clear()
                    continue
                '''暂停消除后，等待传送带速度起来'''
                if change_model1:  # 暂停后启动触发读取取值模式
                    logging.info("---生产者---PLC通知设备开启")
                    change_model1 = False
                    count_stop_time = 0
                    self.create_file_path1()  # 创建文件路径，每日刷新，检查本地与网络时间
                    pre_sp1 = 0
                    for f_i in range(30):
                        time.sleep(0.8)
                        self.bool_get_speed_PLC = True  # 05-19 获取传送带速度
                        while self.bool_get_speed_PLC:
                            time.sleep(0.05)
                        if self.speed2 > aicfg.Speed_of_csd * 0.8:  # 增加传送带速度近似值判断
                            if pre_sp1 == self.speed2:
                                break
                            else:
                                pre_sp1 = copy.deepcopy(self.speed2)
                    self.bool_get_label_PLC = True  # 重新启动后读取异纤选择类别
                    self.bool_get_batch_PLC = True  # 重新启动后读取 大小批次

                    self.read_limit_label()  # 录入 应筛选的类别

                self.photo_n += 1  # 拍照计数
                if self.photo_n > 20000:
                    self.photo_n = 1
                    photo_m += 1

                bool_take_pic = True
                if self.photo_n % 2 == 1:
                    logger.info("-------@@@@@@点信息状态：{}".format(self.num_point))
                t1 = time.time()  # 上一次循环结束的时间戳
                l_t1 = round((aicfg.Frame_time - aicfg.Wait_light_time - (t1 - t2)), 3)
                if l_t1 > 0:
                    time.sleep(l_t1)
                else:
                    if abs(l_t1) > 0.8:  # 当拍照时间间隔大于正常值时，推测为相机异常(根据之前现象)
                        logger7.info("============检测到 拍照时间间隔偏大：{}==========".format(abs(l_t1) + aicfg.Frame_time))
                logger.info("生产者-第{}次--循环时间为：-----------{}-----------".format(self.photo_n - 1,
                                                                              round(time.time() - t2, 3)))

                # 上一帧的 存图，aiinfer 不影响下一帧
                t2 = time.time()  # 开始拍摄的时间戳
                if aicfg.Ctrl_light:
                    self.light_num1 = 1 - self.light_num1  # 信号 0-1 交换
                    self.bool_ctrl_light1[self.light_num1] = True  # 光源触发
                    if len(self.list_cam_param[0]) > 0:  # 当有相机参数不同时[0][1] 的 len 一致
                        for cam_p1 in self.list_cam_param[self.light_num1]:  # 某光的具体参数
                            self.cameraModel.dfsGetPhoto.setCameraParamManu(cam_p1)  # 设入参数
                else:
                    self.light_num1 = 0  # 信号，强制为白光
                time.sleep(aicfg.Wait_light_time)  # 为确保灯光亮度达到合适的--等待时间
                self.result_takepic_sort = []  # 清空拍照后的图片名
                list_tp = [{"id": self.photo_n, "time_tp": t2}]  # 传入拍照进程 所需参数
                self.__oPoolForRaster1.submit(self.tp_try, list_tp)  # 拍照进程
                bool_take_pic = False  # 默认拍照OK
                while len(self.result_takepic_sort) < len(aicfg.Camera_id):  # 等待拍照后图片名回传
                    time.sleep(0.005)
                    if time.time() - t2 > aicfg.Frame_time + 0.6:  # 相机 拍照 超时
                        bool_take_pic = True  # 拍照 NG 信号
                        break
                if not bool_take_pic:  # 拍照成功-存图，
                    id5_take_photo = copy.deepcopy(self.photo_n)
                    # logger.info("拍照表主键ID：{}".format(id5_take_photo))
                    t3 = time.time()
                    # print("第{}次-存拍照表-用时：{}s".format(str(self.photo_n), round(time.time() - t2, 4)))
                    if aicfg.AI_save_pic_bool:  # 临时改动
                        list_save_pic1 = {"tp_num": id5_take_photo, "tp_end_time": t3, "pic_name": self.result_takepic_sort}
                        self.bool_save_pic = False  # 准备及保存图片过程中，信号为False
                        self.__oPoolForRaster1.submit(self.call_ai_savepic_service_v2, list_save_pic1)  # 存图

                    # if self.bool_ai_infer > len(aicfg.Camera_id) - 1:  # 当前帧判断：要是前一帧还在识别，则跳过当前帧
                    self.__oPoolForRaster1.submit(self.call_ai_trigger_data1_v2, self.photo_n, t3, photo_m,
                                                  id5_take_photo, self.result_takepic_sort)
                    # else:
                    #     self.bool_ai_infer = 3  # # 这一帧跳过时，强制给再下一帧AIinfer
            except Exception as e:
                logger7.error(f"err---produce: {e}")
                if ("image" in str(e)) and ("received" in str(e)):
                    logger7.error("相机丢帧---超时错误")
                    self.new_add_global_data[1] = 11  # 相机拍照异常--代号
                    self.new_add_global_variables[1] = True
                time.sleep(0.25)


    def tp_try(self,list_id):
        self.__oPoolForRaster2.map(self.take_photo_new, list_id)

    def take_photo_new(self, list_id):
        try:
            tp_id = list_id["id"]; t2 = list_id["time_tp"]
            light_n = copy.deepcopy(self.light_num1)
            result_takepic = self.cameraModel.takePic()
            if len(result_takepic) == len(aicfg.Camera_id):
                # bool_take_pic = False
                for list_cam in aicfg.Camera_id:
                    for name_pic in result_takepic:
                        if list_cam[0] in name_pic:
                            # [[name,0],[name,1],[]]  ---按配置文件中的相机号排序
                            self.result_takepic_sort.append([name_pic, light_n])  #
                            continue
                # logger.info("第{}次到拍照结束用时：{}s".format(str(tp_id), round(time.time() - t2, 3)))
                # logger.info("第{}次到拍照结束用时：{}s".format(str(self.photo_n), round(time.time() - t2, 3)))
            else:
                # print("拍照服务返回信息:{}".format(result_takepic))
                # print("相机拍照--失败 --退出程序")
                logger.info("拍照服务返回信息:{}".format(result_takepic))
                logger.info("相机拍照--失败 --退出程序")
        except Exception as e:
            logger7.error(f"err---take_photo_new: {e}")
            if ("image" in str(e)) and ("received" in str(e)):
                logger7.error("相机丢帧---超时错误")
                self.new_add_global_data[1] = 11  # 相机拍照异常--代号
                self.new_add_global_variables[1] = True
            time.sleep(0.25)

    '''调用存图函数'''
    def call_ai_savepic_service_v2(self, list_save_pic2):
        self.save_pic_name1 = []  # 清空
        self.after_pic_path = {}
        num_sp = list_save_pic2["tp_num"]
        t4 = list_save_pic2["tp_end_time"]
        pic_name_list = list_save_pic2["pic_name"]
        # print("存图线程开始启动时间：{}".format(round(time.time() - t4, 3)))
        if aicfg.AI_save_pic_bool:
            # t5 = time.time()
            res = self.cameraModel.savePic(self.save_pic_aipath)  # res = {}
            # print("res:{}".format(res))
            # print("第{}次，存图线程完成时间-真实：{}".format(num_sp, round(time.time() - t5, 3)))
            if len(res) == len(aicfg.Camera_id):
                self.bool_save_pic = True
                self.save_pic_name1.append(res)

                # 写入数据库 - 并返回
                for name_i in range(len(pic_name_list)):
                    list_6 = [int(num_sp), pic_name_list[name_i][0], t4, 1]
                    id6_pic = write_mysql6(list_6)  # 录入图片表
                    # print("图片表ID：{}".format(id6_pic))
                    self.after_pic_path[str(name_i + 1)] = id6_pic
            else:
                print("存图-调用服务--失败")
                # logger.info("存图-调用服务--失败")
        # print("第{}次，存图线程完成时间：{}".format(num_sp, round(time.time() - t4, 3)))

    '''move图片'''
    def move_pic1(self, list_move_pic3):
        try:
            list_pic_name1 = list_move_pic3["list_pic_name"]
            # print("存图名称：{}".format(list_pic_name1))
            for name_p in list_pic_name1:
                pic_path_abs2 = os.path.join(self.save_pic_aipath, name_p[0])
                num_p = 1 if name_p[1] == 0 else 5
                copy_path_no1 = "mv -f " + pic_path_abs2 + " " + self.pic_p_use[num_p] + "/"  # # 每日刷新nobox 路径
                os.system(copy_path_no1)  # 复制到nobox,不做记录
        except Exception as e:
            logger.error(f"err---move_nobox_pic: {e}")

    '''
    # @list_pic_name=[0pic-name,1pic-name,2pic-name] 
    [['camera39024076_2021_07_16_15_56_34_538084.jpg', 0],
     ['camera48024027_2021_07_16_15_56_34_538084.jpg', 0],
     ['camera48024034_2021_07_16_15_56_34_538084.jpg', 0]]
    # @point_world={"1":[{},{}],}
    self.__oPoolForRaster.submit(self.save_pic_message, list_pic_name, point_world)
    '''
    '''生成.txt文件，move 图片'''
    def save_pic_message(self, list_move_pic1):
        try:
            bool_need_move = False  # True：把图移到havebox | False：把图移到nobox
            list_pic_name1 = list_move_pic1["list_pic_name"]  # 已整理(图片名和所在列表位置对应)
            point_world1 = list_move_pic1["point_world"]
            # print("存图名称：{}".format(list_pic_name1))
            for i in range(len(list_pic_name1)):  # 对 每张图片(有图片)
                path_ = list_pic_name1[i]  # 最后的图片名 列表[name, 0]
                pic_path_abs = os.path.join(self.save_pic_aipath, path_[0])  # 合成完整 原始图片路径
                if point_world1 is not None:  # 当点数据 为 None(有图片-有数据)
                    if str(i+1) in point_world1.keys():  # 图片代号 存在于 点字典中(有图片-有数据-该图有数据)
                        point_data_ori = point_world1[str(i+1)]  # 点数据，原始 #[{},{}]
                        if len(point_data_ori) > 0:  # 此图有点信息时(有图片-有数据-该图有数据-图中数据有值)
                            bool_need_move = True  # 把图移到havebox 信号
                            '''单张图片中 点信息提取写入，并记录到全局变量中，等待上传线程中写入'''
                            self.upload_msg_with_save(point_data_ori, path_)
                '''对 每张图片 判断是否需要进行nobox的移动-(点数据为None 或 无此图数据)'''
                if bool_need_move:
                    bool_need_move = False  # 立马重置信号
                    num_p = 0 if path_[1] == 0 else 4
                else:
                    if self.new_add_global_variables[3]:  # 上传 nobox 判断
                        pic_name_now = copy.deepcopy(path_)
                        self.new_add_global_data[3].append(pic_name_now)  # 传入 图片名[name,0]
                    num_p = 1 if path_[1] == 0 else 5
                cmd_mv1 = "mv -f " + pic_path_abs + " " + self.pic_p_use[num_p] + "/"  #
                os.system(cmd_mv1)  # 执行移动命令
            '''上传判断 (当 有上传信号 且 有图片名称时)'''
            if self.new_add_global_variables[2] and (len(self.new_add_global_data[2]) > 0):  # 上传判断
                self.new_add_global_variables[2] = False  # 有符合规则的图和记录生成
            if self.new_add_global_variables[3] and (len(self.new_add_global_data[3]) > 0):  # 上传判断
                self.new_add_global_variables[3] = False  # 有符合规则的图和记录生成

        except Exception as e:
            logger.error(f"err---move_deal_pic: {e}")

    ''' 单张图片中 点信息提取写入，并记录到全局变量中，等待上传线程中写入 '''
    def upload_msg_with_save(self, dict_p1, pic_name1):  # pic_name1是相对的文件名
        """
        (功能1) 为 常用功能，每张图片都要经过 上级调用前已确认有图有点
        (功能2) 为 触发功能，当其他线程传来信号，根据全局计数执行 计数，限制，传参(图片名)
        """
        try:
            list_message1 = []  # 单张图片中的点信息列表
            bool_pic_label1 = [True] * len(self.label_path)  # 单张图中的label是否加过
            bool_upload = False  # 上传请求的 图片名 信号 (有请求，且不超限，才上传)

            for point_message1 in dict_p1:  # 单张图中的每一个点信息
                '''(功能1)格式化点信息，并添加但单图列表中，等待写入单图txt'''
                dict_need1 = self.get_dict_from_message1(point_message1)  # 提取点信息成字典格式
                list_message1.append(dict_need1)  # 单个字典 添加到 准备写入的 列表中
                '''(功能2)上传信号 + 锁定图片个数(单张图仅在每种label数量 + 1)'''
                if self.new_add_global_variables[2]:  # 上传判断 -另外线程传来的
                    i_lv = int(point_message1["level"]) - 1  # 此点对应的下标锁号
                    if bool_pic_label1[i_lv]:  # 对应level没加锁(到这句，就表示此label起码有了1个)
                        bool_pic_label1[i_lv] = False  # 单张中的这个level锁定，整个函数过程中只能进来一次
                        # 对应level 小于限制数量
                        if self.list_num_label[0][i_lv] <= self.list_num_label[1][i_lv]:  # 防止上传数量超限
                            self.list_num_label[0][i_lv] += 1  # 对应的level + 1
                            bool_upload = True

            '''(功能2)应答 上传请求的 图片名 部分'''
            if bool_upload:  # 有请求，且不超限，才上传
                pic_name_now = copy.deepcopy(pic_name1)  # 防止错乱 [name,0]
                self.new_add_global_data[2].append(pic_name_now)  # 传入图片名
            '''(功能1)创建并写入单图txt'''
            txt_name1 = pic_name1[0].replace("jpg", "txt")  # 点信息txt文件
            num_p = 0 if pic_name1[1] == 0 else 4
            with open(self.pic_p_use[num_p] + "/" + txt_name1, 'w') as tf1:
                tf1.write(json.dumps(list_message1))  # 开始存信息，写入txt文件

        except Exception as e:
            logger.error(f"err---upload_msg_with_save: {e}")

    '''提取点信息成字典格式'''
    def get_dict_from_message1(self, msg1):
        """
        :param msg1: 传入的点信息，字典
        :return: None 或者 所需格式的字典
        """
        res1 = None
        try:
            # logger.info("send to save image dict: {}".format(msg1))
            if (len(msg1) > 8) and isinstance(msg1, dict):
                res1 = {"leftTopX": msg1["x_min"], "leftTopY": msg1["y_min"], "rightBottomX": msg1["x_max"],
                        "rightBottomY": msg1["y_max"], "labelType": msg1["label"],
                        "labelMap": {"level": msg1["level"], "score": msg1["score"],
                                     "ff_color": msg1["ff_color"], "ff_type": msg1["ff_type"]}}
            else:
                logger.info("send to save image dict error")
        except Exception as e:
            logger.error(f"err---get_need_dict: {e}")
        return res1

    '''调用AI识别-内部使用进程'''
    def call_ai_trigger_data1_v2(self, num_tp, start_time, num_mtp, tp_id, list_pic_name1):  # 计数，拍照时间戳，大循环计数
        # print("进入AIinfer--thread")
        while self.bool_ai_infer < len(aicfg.Camera_id):
            time.sleep(0.005)
        self.bool_ai_infer = 0  # AI开始时：0, 完成后置为3
        self.ai_point_data = []
        # list_arg1 = [{"num_cam": i, "num_tp": num_tp, "start_time": start_time} for i in
        #              range(len(aicfg.Camera_id))]
        list_arg1 = [{"num_tp": num_tp, "start_time": start_time}]
        if self.light_num1 == 0:
            self.__oPoolForRaster2.map(self.call_ai_1_v2, list_arg1)
        else:
            self.__oPoolForRaster2.map(self.ai_deal_UV_light, list_arg1)
        # for j in range(len(aicfg.Camera_id)):
        #     self.call_ai_1_v2(list_arg1[j])  # 串行调用

        list_tp_num1 = {"num_tp": num_tp, "start_time": start_time, "num_mtp": num_mtp,
                        "tp_id": tp_id, "list_pic_name1": list_pic_name1}
        self.wait_deal_data1(list_tp_num1)
        # self.__oPoolForRaster2.map(self.wait_deal_data1, [list_tp_num1])
    '''{'boxes': [], 'scores': [], 'labels': [], 'img_name': 'camera13914456_2021_08_11_17_26_43_004148.jpg'}'''
    '''调用AI识别-函数'''
    def call_ai_1_v2(self, list_arg2):
        try:
            # print("进入AIinfer")
            # num_cam, num_tp, start_time = list_arg2["num_cam"], list_arg2["num_tp"], list_arg2["start_time"]
            num_tp, start_time = list_arg2["num_tp"], list_arg2["start_time"]
            for num_cam in range(len(aicfg.Camera_id)):

                sn = aicfg.Camera_id[num_cam][0]  # 指定的相机号
                img = self.cameraModel.cameraData[sn][2]  # 处理后的图片
                oriImg = self.cameraModel.cameraData[sn][0]  # oriImg 原始图片数据
                img_name = self.cameraModel.cameraData[sn][1]  # 当前预测的图片
                # print("sn:{}--拿到对应图像".format(sn))
                # print("sn:{}--img_name:{}".format(sn, img_name))
                # print("sn:{}--img:{}".format(sn, img))
                # print("sn:{}--oriImg:{}".format(sn, oriImg))
                res = self.detectionModel[0].aiInfer(oriImg, img, img_name)  # AI识别  res ={}
                # print("第{}次到AI识别结束用时-真实：{}s".format(str(num_tp), round(time.time() - start_time, 3)))
                # if self.photo_n in range(20, 60) and (num_cam > 0):
                #     res = {'boxes': [[627.5390625, 401.0, 1032.510986328125, 886.2000122070312]],
                #            'scores': [0.76], 'labels': ["yixian"]}  # 虚拟一个点
                # print("AI识别--返回：{}".format(res))
                if len(res["labels"]) > 0:  # 有识别才录入
                    list_data_name = [num_cam + 1, res]
                    self.ai_point_data.append(list_data_name)  # [[1,{box...}],[2,,{box...}]]
                self.bool_ai_infer += 1  # AI识别完成信号
                # print("第{}次到AI识别结束用时：{}s".format(str(num_tp), round(time.time() - start_time, 3)))
                time.sleep(0.001)
        except Exception as e:
            logger.error(f"aiinfer -error: {e}")


    def ai_deal_UV_light(self, list_arg3):
        try:
            # print("进入AIinfer")
            num_tp, start_time = list_arg3["num_tp"], list_arg3["start_time"]
            for num_cam in range(len(aicfg.Camera_id)):
                if aicfg.Ctrl_light:  # 控制灯光交替线程--是否需要开启线程
                    sn = aicfg.Camera_id[num_cam][0]  # 指定的相机号
                    # img = self.cameraModel.cameraData[sn][2]  # 处理后的图片
                    oriImg = self.cameraModel.cameraData[sn][0]  # oriImg 原始图片数据
                    img_name = self.cameraModel.cameraData[sn][1]  # 当前预测的图片
                    # print("sn:{}--拿到对应图像".format(sn))
                    # print("sn:{}--img_name:{}".format(sn, img_name))
                    # print("sn:{}--img:{}".format(sn, img))
                    # print("sn:{}--oriImg:{}".format(sn, oriImg))
                    res = self.detectionModel[1].detect(oriImg, img_name, aicfg.UV_threshold)  # AI识别  res ={}
                    # print("第{}次到AI识别结束用时-真实：{}s".format(str(num_tp), round(time.time() - start_time, 3)))
                    # if self.photo_n in range(20, 60) and (num_cam > 0):
                    #     res = {'boxes': [[727.5390625, 401.0, 1032.510986328125, 986.2000122070312]],
                    #            'scores': [0.66], 'labels': ["yixian"]}  # 虚拟一个点
                    # print("AI识别--返回：{}".format(res))
                    if len(res["labels"]) > 0:  # 有识别才录入
                        list_data_name = [num_cam + 1, res]
                        self.ai_point_data.append(list_data_name)  # [[1,{box...}],[2,,{box...}]]
                self.bool_ai_infer += 1  # AI识别完成信号
                # print("第{}次到AI识别结束用时：{}s".format(str(num_tp), round(time.time() - start_time, 3)))
                time.sleep(0.001)
        except Exception as e:
            logger.error(f"ai_deal_UV_light -error: {e}")


    '''等待AI返回，及后续处理'''
    def wait_deal_data1(self, tp_num2):
        num_tp = tp_num2["num_tp"]
        start_time = tp_num2["start_time"]
        num_mtp = tp_num2["num_mtp"]
        tp_id = tp_num2["tp_id"]
        list_pic_name1 = tp_num2["list_pic_name1"]
        bool_check_ai = True
        t_wait_ai = time.time()
        while self.bool_ai_infer < len(aicfg.Camera_id):  # < 3
            if time.time() - t_wait_ai > aicfg.Frame_time + 0.4:
                bool_check_ai = False
                # 此时 应该是AI有异常
                self.new_add_global_data[1] = 22  # AI异常--代号
                self.new_add_global_variables[1] = True
                break
            time.sleep(0.001)
        # 保证了这一帧中，会将 bool_ai_infer = 3/2 ,从而保证下一帧 的等待一定有结果
        if bool_check_ai:
            ai_data_list = copy.deepcopy(self.ai_point_data)
            if aicfg.AI_draw_pic_bool:  # 根据AI返回，直接画图
                list_draw_ai = [{"ai_data_list": ai_data_list}]
                self.__oPoolForRaster2.map(self.draw_pic_for_ai, list_draw_ai)
            # if aicfg.Mechine_function == "gas":  # 处理喷气类的点信息
            #     self.point_deal_gas(ai_data_list, start_time, num_mtp, num_tp)
            if aicfg.Mechine_function == "claw":  # 处理抓手类的点信息
                while not self.produce_point_is_OK:  # 在上一帧的点数据处理过程中，等待 当False时正在执行上一轮，等待
                    time.sleep(0.001)
                self.point_deal_claw(ai_data_list, start_time, self.speed2, num_mtp, num_tp,
                                     tp_id, list_pic_name1)  # ai_data_list =[[1,{box...}],[2,,{box...}]]
        else:
            self.bool_ai_infer = len(aicfg.Camera_id)  # 强制给下次的aiinfer 可以执行
            logger.info("第{}次点处理跳过，AI未全部返回：当前AI返回数量：{}".format(num_tp, self.bool_ai_infer))
    '''2021-06-07---点的数据处理'''
    def point_deal_claw(self, ai_result, start_time, speeedas2, photo_m, photo_n, id5_take_photo, list_pic_name):
        self.produce_point_is_OK = False
        t5 = time.time()
        # print("第{}次---进入点位处理--抓手".format(photo_n))
        # logger7.info("AI返回的原始数据，ai_result:{}".format(ai_result))
        if len(ai_result) > 0:  # [[1,{box...}],[2,{box...}]]
            point_world = {}
            for point_data1 in ai_result:  # 分图片
                w_point1 = self.processAiData(point_data1[1], point_data1[0])  # 生成改图的点信息 列表
                # [] or [{},{}]  会有空值
                if len(w_point1) > 0:  # 当列表为空，不把该图信息录入字典(即：字典有该图信息时，必有点信息内容)
                    point_world[str(point_data1[0])] = w_point1  # point_world = {"1":[{},{}],}
            # logger7.info("第{}次，世界坐标数据，point_world:{}".format(photo_n, point_world))
            # @list_pic_name=[0pic-name,1pic-name,2pic-name]
            # @point_world={"1":[{},{}],}
            if aicfg.AI_save_pic_bool:
            # if aicfg.AI_draw_pic_bool:
                list_move_pic = [{"list_pic_name": list_pic_name, "point_world": point_world}]
                self.__oPoolForRaster2.map(self.save_pic_message, list_move_pic)
            if len(point_world) > 0:  # 当转换后的点 存在时
                # caculate_nearly_point(point_world, 2)中  2 是相机个数
                point_arr = caculate_nearly_point(point_world, len(aicfg.Camera_id))  # 舍去相机重合点 #走到这一步，必有点
                if point_arr is not None:
                    # print("the checked result is {}".format(point_arr))
                    # print("start_time:{}  speeedas2:{}".format(start_time, speeedas2))
                    self.num_point[3] += len(point_arr)  # 同步去重后的点数量
                    datapiont1 = self.remove_point2(point_arr, start_time, speeedas2)
                    # print("@@@@@@@@@@@@@@-----({})---time:{}----speed:{}".format(photo_n,start_time,speeedas2))
                    # logger7.info("第{}次，异步去重后-筛选后结果：{}".format(photo_n, datapiont1))
                    if datapiont1 is not None:
                        self.put_record2queue(datapiont1, start_time, speeedas2, photo_n,
                                              id5_take_photo)  # 将点写入队列（生产者调用）
        else:
            if aicfg.AI_save_pic_bool:
            # if aicfg.AI_draw_pic_bool:
                list_move_pic2 = [{"list_pic_name": list_pic_name}]
                self.__oPoolForRaster2.map(self.move_pic1, list_move_pic2)
                if self.new_add_global_variables[3]:  # 上传 nobox 判断
                    pic_name_now = copy.deepcopy(list_pic_name)
                    self.new_add_global_data[3] = pic_name_now  # 传入 图片名[name,0]
                    self.new_add_global_variables[3] = False  # 上传 nobox 应答信号
        # 触发 --检测光源亮度
        if self.new_add_global_variables[0]:
            if list_pic_name[0][1] == 0:  # 判断图片不是UV下拍的
                self.new_add_global_variables[0] = False
                self.new_add_global_data[0] = list_pic_name
        # print("第{}次仅点数据处理用时：{}s".format(photo_n, round(time.time() - t5, 3)))
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
        """
        :param point_arr: 点信息 字典
        :param start_time: 开始时间戳
        :param speed1: 传送带速度
        :param num_tp: 拍照次数
        :param id5_take_photo: 拍照表ID
        """
        try:
            if point_arr is not None:
                num_tp_i = 0  # 点的ID(给自己分析用的)
                while len(self.after_pic_path) == 0:  # 等待存图线程有图片表的返回ID
                    time.sleep(0.005)
                # logger4.info(" point_arr {}".format(point_arr))
                for item in point_arr:
                    # logger4.info("进入该点信息")
                    num_tp_i += 1  # 单帧里 有效点的个数
                    self.num_point[4] += 1  # 实际存入队列 点 总数
                    self.num_point_temp += 1  # 计数 识别到的异纤数量,根据PLC指令清零
                    item["speed"] = speed1  # 速度
                    item["start_time"] = start_time  # 在每组坐标的字典上添加开始时间的对应组
                    item["id_tp"] = id5_take_photo  # 拍照表ID
                    item["ID_point"] = str(num_tp) + "_" + str(num_tp_i)  # 点的ID(给自己分析用的)
                    item["times_judge"] = 0  # 判别是经过几个抓手了(给自己分析用的)
                    item["id_pic"] = self.after_pic_path[str(item["position"])]
                    if aicfg.claw_section:
                        p_num = aicfg.Judge_queue[0] if item["worldX"] < aicfg.X_choose_claw else aicfg.Judge_queue[1]
                    else:
                        p_num = 0
                    '''选择存入哪一个梯队，哪个类别等级，点信息字典'''
                    self.real_put_point_record(p_num, item["level"], item)  # 队列梯队，等级, 点信息
                # if num_tp_i > 0:
                #     logger4.info("第{}次,本轮生成{}个点--耗时：{}".format(num_tp, num_tp_i, round(time.time() - start_time, 3)))
        except Exception as e:
            logger.error(f"err -- put_record2queue: {e}")

    '''向PLC --获取批次号 '''
    def get_batch(self, sign2):  # 获得批次号
        result_big, result_small = self.read_batch(sign2)
        if len(result_big) == 0 or len(result_small) == 0:  # 大小批次长度都不应该为0
            self.batch_cotton = time.strftime("%Y-%m%d", time.localtime())
            write_mysql4([time.strftime("%Y", time.localtime()), time.strftime("%m%d", time.localtime())])
        else:
            self.batch_cotton = result_big + "-" + result_small
            write_mysql4([result_big, result_small])
        logger7.info("+++++++++++此时批次号为：{}".format(self.batch_cotton))

    '''读取批次号--PLC通讯'''
    def read_batch(self, sign1):  # 初始化时 sign1=Fasle ，
        logger.info('读取批次号--PLC通讯--1')
        result1_char1, result2_char1 = None, None
        sign2 = True  # 默认去读写
        if sign1:
            result_sign = self.PLC_ctrl[aicfg.Run_choose[1]].read_bit_data(aicfg.MELSEC_CODE.SIGN_BATCH, 1)
            if result_sign[0] == 0:  # 当信号位为0，表示无变化时，不去读取大小批次
                sign2 = False
        logger.info('读取批次号--PLC通讯--2')
        if sign2:
            result1_ascii = self.PLC_ctrl[aicfg.Run_choose[1]].read_word_data(aicfg.MELSEC_CODE.BIG_BATCH, 5)
            result1_char1 = self.ascii_to_char(result1_ascii)
            result2_ascii = self.PLC_ctrl[aicfg.Run_choose[1]].read_word_data(aicfg.MELSEC_CODE.SMALL_BATCH, 8)
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

    '''选取点类别--只能开机录入一遍'''
    def read_limit_label(self):
        self.list_zh1 = {}  # 运行时 清空原来的字段
        num_limit_label = aicfg.Choose_label
        all_limit_label = aicfg.Choose_type
        if num_limit_label >= 10:  # 小于10时，强制赋值取数
            while self.bool_get_label_PLC:
                time.sleep(0.05)  # 保证能取到 num_now = self.choose_model1
            num_limit_label = self.choose_model1 + 1
        for i in range(num_limit_label):
            for dict_p1 in all_limit_label[i]:
                self.list_zh1.update(dict_p1)
        print("此次运行，({})选择的类别：{}".format(num_limit_label, self.list_zh1))
        logger7.info("此次运行，({})选择的类别：{}".format(num_limit_label, self.list_zh1))

    '''读取队列  兼容分段+常规的 抓手读取队列规则 --2021-11-04'''
    def choose_point1(self, numAB):
        rePP1 = None; list_claw = []  # 初始置为 None
        # 分段选择
        if aicfg.claw_section:
            '''分段 抓取模式  1:[0], 2:[1], 3:[2,0], 4:[3,1], '''
            list_claw = [numAB - 1] if numAB <= 2 else [numAB - 1, numAB - 3]
        else:
            '''常规 抓取模式  1:[0], 2:[1,0], 3:[2,1,0], 4:[2,1,0], '''
            list_claw = [0] if numAB <= 1 else [1, 0] if numAB <= 2 else [2, 1, 0]
        '''由后置梯队，往前找，同一梯队中，按等级优先找'''
        for j in list_claw:
            if not self.q_1st[j].empty():
                rePP1 = self.q_1st[j].get()
                logger4.debug('抓手{}取到 第{}梯队 异纤优先 点数据 {}'.format(numAB, j + 1, rePP1))
                break  # 依次取， 一旦有取到值，跳出for循环
            elif not self.q_2nd[j].empty():
                rePP1 = self.q_2nd[j].get()
                logger4.debug('抓手{}取到 第{}梯队 色绒优先 点数据 {}'.format(numAB, j + 1, rePP1))
                break  # 依次取， 一旦有取到值，跳出for循环
            elif not self.q_3rd[j].empty():
                rePP1 = self.q_3rd[j].get()
                logger4.debug('抓手{}取到 第{}梯队 脏绒+羊屎 点数据 {}'.format(numAB, j + 1, rePP1))
                break  # 依次取， 一旦有取到值，跳出for循环
            elif not self.q_4th[j].empty():
                rePP1 = self.q_4th[j].get()
                logger4.debug('抓手{}取到 第{}梯队 异纤常规 点数据 {}'.format(numAB, j + 1, rePP1))
                break  # 依次取， 一旦有取到值，跳出for循环
            elif not self.q_5th[j].empty():
                rePP1 = self.q_5th[j].get()
                logger4.debug('抓手{}取到 第{}梯队 色绒常规 点数据 {}'.format(numAB, j + 1, rePP1))
                break  # 依次取， 一旦有取到值，跳出for循环
            elif not self.q_6th[j].empty():
                rePP1 = self.q_6th[j].get()
                logger4.debug('抓手{}取到 第{}梯队 其他 点数据 {}'.format(numAB, j + 1, rePP1))
                break  # 依次取， 一旦有取到值，跳出for循环
        return rePP1


    '''判断 指定的梯队中队列 是否为空'''
    def judge_empty_queue(self, list_echelon):
        bool_res = True  # 初始置为 全空：方便异常 或传参错误
        try:
            if isinstance(list_echelon, list):
                for echelon in list_echelon:  # 需要判断的梯队号 (列表) [0, 1, 2, 3]
                    for qu_now in self.queue_all:  # 每个类别等级 队列列表[q_1,q_2,q_3,q_4,q_5,q_6]
                        bool_res = bool_res and qu_now[echelon].empty()
                        if not bool_res:  # 当队列中有元素时，停止对比
                            break
            else:
                logger7.info("判断队列为空时，传参不为列表")
        except Exception as e:
            logger.error(f"err -- judge_empty_queue: {e}")
        return bool_res


    '''将点信息 存入队列，若满即删并记录(生产者 和消费者 存入队列使用)'''
    def real_put_point_record(self, echelon, level, point_message):  # 队列梯队，等级, 点信息
        """
        :param echelon: 队列梯队号
        :param level: 分类等级
        :param point_message: 点信息
        """
        try:
            if self.queue_all[int(level - 1)][echelon].full():  # self.queue_all[分类等级-1][梯队]
                throw1 = self.queue_all[int(level - 1)][echelon].get()  # 获取一个点，丢弃
                list_point = self.get_data_form_p_dict(throw1, 5)  # 整理点信息的字典，返回列表
                self.num_point[7] += 1  # 进入队列时，由于满队列，而被放弃的点
                if not self.sql_point_queue.full():  # 存入 点位表写入线程的队列
                    self.sql_point_queue.put(list_point)
            self.queue_all[int(level - 1)][echelon].put(point_message)  # 放到队列里
            # logger7.info("把点存入 第({})梯队的 第({})等级 队列".format(echelon + 1, level))
        except Exception as e:
            logger.error(f"err -- real_put_point_record: {e}")


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
                # self.ai_point_record.real_all_piont_put += 1  # 实际存入队列 点 总数
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

            if num_tp_i > 0:
                logger4.info("第{}次,本轮生成{}个点--耗时：{}".format(num_tp, num_tp_i, time.time() - start_time))

    '''测试PLC--抓手获取时间戳和X位置'''

    def test_send(self):  # 单独循环测试ARM2抓手3的抓取
        self.connect_PLC_thread()  # 开线程-发送PLC连接通断信号
        time.sleep(3)
        self.bool_start_signal_PLC = True
        time.sleep(3)
        '''判定本模组, 抓手个数, 抓手状态的强制信号和内容'''
        plc_ctrl_list = aicfg.PLC_ctrl_choose  # PLC的选择执行列表
        num_claw_plc = int(plc_ctrl_list[1]) + int(plc_ctrl_list[2])
        self.num_claw_state = 4 if num_claw_plc > 1 else 2  # 抓手数量
        num_claw1 = self.num_claw_state * 2  # 抓手的状态数量
        list_statu = aicfg.List_claw_statu  # 抓手的状态的赋值列表
        X_l_cfg = [aicfg.X1_LEN1, aicfg.X2_LEN1, aicfg.X3_LEN1, aicfg.X4_LEN1, ]

        for i in range(80000):
            time.sleep(0.5)
            if i % 20 == 1:
                self.bool_circulation_process_PLC = True  # PLC通讯心跳
            self.bool_ctrl_stop = True
            while self.bool_ctrl_stop:
                time.sleep(0.3)
            if self.if_need_stop == 0:
                time.sleep(4)
                logger7.info("第{}次--PLC发出停止信号".format(i))  #
                continue

            '''读取+判断 抓手状态'''
            while self.bool_send_toPLC_claw:  # 等上一次的发送成功后，或上次无发送
                time.sleep(0.001)

            self.list_claw_state = []  # 清空上一次的抓手状态
            self.bool_read_claw_state = True  # 读取+判断 抓手状态
            while len(self.list_claw_state) < 1:
                time.sleep(0.001)
                # 是否需要屏蔽抓手
                if not aicfg.Bool_use_claw:  # Bool_use_claw = True 时正常
                    for claw_i in range(num_claw1):
                        if list_statu[claw_i] < 2:
                            self.list_claw_state[claw_i] = list_statu[claw_i]  # 强制赋值-忙碌
            logger7.info("抓手状态:{}".format(self.list_claw_state))

            '''根据抓手状态来进行下一步判断'''
            zhua_a = 0  # 每次初始化 抓手选择
            for ic in range(self.num_claw_state):  # 根据现在的抓手数量
                claw_sta1 = sum(self.list_claw_state[2 * ic: 2 * ic + 2])  # 取出对应的抓手状态list[左闭右开]
                # tidui_l = aicfg.Claw_ch_q[1][ic] if aicfg.claw_section else aicfg.Claw_ch_q[0][ic]
                if claw_sta1 == 0:
                    zhua_a = ic + 1; break
            '''选择判断--取队列'''
            if zhua_a == 0:  # 锁定抓手1/2/3/4（起码有一个抓手空闲且对应队列有值）
                time.sleep(0.1); continue
            else:
                t_zhua = time.time()  # 记 是否超时的初始时间
                bool_send_time = True  # 执行发送数据的信号
                '''读取PLC时间戳'''
                self.bool_read_plc_time = [True, zhua_a]  # 读取PLC时间戳
                while self.bool_read_plc_time[0]:
                    time.sleep(0.002)
                    if time.time() - t_zhua > 1:
                        bool_send_time = False; break
                '''构造对应的X 值'''
                if aicfg.claw_section:
                    choose_xx = aicfg.X_choose_claw + X_l_cfg[zhua_a - 1][0]
                    if (zhua_a == 1) or (zhua_a == 3):
                        x = randint(aicfg.Min_value_X, choose_xx)
                    else:
                        x = randint(choose_xx, aicfg.Max_value_X)
                else:
                    x = randint(aicfg.Min_value_X, aicfg.Max_value_X)
                '''发送抓取信息'''
                if bool_send_time:
                    # logger7.info("self.time_plc:{}".format(self.time_plc))
                    end_time = self.time_plc + 3500
                    # logger7.info("end_time:{}".format(end_time))
                    sec, mill_sec = long2time(end_time)  # 毫秒转时间
                    self.send_toPLC_list = [zhua_a, int(sec), int(mill_sec), int(x)]
                    self.bool_send_toPLC_claw = True
                    logger7.info("send_PLC_message:{}".format(self.send_toPLC_list))

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
                if self.queue_gas.full():
                    point_throw = self.queue_gas.get()
                    logger5.info("{}次拍照-队列已满，删除数据:{}".format(photo_nm, point_throw))
                self.queue_gas.put(point_result1)
                print("生产者-第{}次，点信息存入队列,耗时：{}".format(photo_nm, round(time.time() - t2, 3)))
        else:
            print("生产者-第{}次--点处理--AI识别图中--无异常,耗时：{}".format(photo_nm, round(time.time() - t2, 3)))
        self.produce_point_is_OK = True

    def wait_send_PLC(self, y_l, time0):
        wait_time1 = round(y_l / self.speed2 - (time.time() - time0) - 0.04 - aicfg.PQ_T, 3)
        print("消费者--wait_time1:{}--现在时间戳：{}".format(wait_time1, time.time()))
        if wait_time1 > 0:
            time.sleep(wait_time1)
            self.bool_circulation_qp_PLC = True  # 发送给PLC 喷气指令-信号

    def get_queue(self):
        if self.queue_gas.empty():
            time.sleep(0.01)
            return None
        else:
            point = self.queue_gas.get()
            return point

    def consume_gas_injection1(self):  # 消费者-喷气模块

        # 05-12 假设喷气频率0.2s
        self.bool_check_process_PLC = False
        arm_ctrl = aicfg.ARM_number
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
                    pq_list[59 - num_pq[0]] = num_pq[1] + aicfg.PQ_X  # 修正后的喷嘴号
                # 队列满了就等待，要维持 某次的等待时间和发送数据的对应，不能错位
                print("消费者存入PLC读取队列：{}".format(point_message1[3]))
                self.pqlist_queue.put([point_message1[3], pq_list])
                time_00 = point_message1[0]
                y = point_message1[1] + aicfg.PQ_Y
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
        try:
            arr = []
            data_label = res_data["labels"]
            if len(data_label) > 0:  # 为空列表时，可以直接返回 arr = []
                data_score = res_data["scores"]
                data_point = res_data["boxes"]
                # data_ff_color = res_data["ff_color"]  # 2021-08-18
                # data_ff_type = res_data["ff_type"]  # 2021-08-18
                data_ff_color = [""] * len(data_label)  # 2021-08-18
                data_ff_type = [""] * len(data_label)  # 2021-08-18
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
                        x = (data_point[i_point][0] + data_point[i_point][2]) / 2  # 图片中的像素坐标
                        y = (data_point[i_point][1] + data_point[i_point][3]) / 2
                        worldx, worldy, worldz = image_points_to_world_plane(x, y, int(position))  # 换算过后的世界坐标
                        if worldx < aicfg.Min_value_X or worldx > aicfg.Max_value_X:
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
                        elif data_label[i_point] in ["serong", "zangmian", "shenhuangmao"]:
                            if bool_score and bool_area:
                                point_level = 2
                            else:
                                point_level = 5
                        else:
                            if bool_score and bool_area:
                                point_level = 3
                            else:
                                continue

                        map = {"position": position, "label": data_label[i_point], "score": round(data_score[i_point], 3),
                               "ff_color": data_ff_color[i_point], "ff_type": data_ff_type[i_point],
                               "level": point_level, "x": x, "y": y, "worldX": abs(worldx), "worldY": abs(worldy),
                               "x_min": data_point[i_point][0], "x_max": data_point[i_point][2],
                               "y_min": data_point[i_point][1], "y_max": data_point[i_point][3]}
                        self.num_point[2] += 1
                        arr.append(map)
            return arr  # [] or [{},{}]
        except Exception as e:
            logger.error(f"processAiData  err: {e}")
            return []

    '''从原来字典中提取信息重构成列表，为写入点位表服务'''
    def get_data_form_p_dict(self, p_dict, state):
        """
        :param p_dict:  点信息 字典
        :param state:  点的执行状态 4：抓取成功， 5：未抓取
        :return: 重构列表 或 None
        """
        try:
            list_point = [p_dict.get("id_tp"), p_dict.get("id_pic"), p_dict.get("speed"), p_dict.get("x_max"),
                          p_dict.get("y_max"), p_dict.get("x_min"), p_dict.get("y_min"), p_dict.get("worldX"),
                          p_dict.get("worldY"), state, p_dict.get("label"), p_dict.get("score"), p_dict.get("level"),
                          p_dict.get("ff_color"), p_dict.get("ff_type")]
            return list_point
        except Exception as e:
            logger.error(f"err -- get_data_form_p_dict: {e}")
            return None

    # --------------抓手--消费者--------------------
    '''消费者部分'''
    def consume_claw_injection1(self):
        """消费者 - 抓手模块"""
        '''初始值'''
        self.bool_check_process_PLC = False  # 停止自检过程中的 心跳
        # label_list1=[PLC通讯心跳-0, 监测传送带速度-1, 读取是否需要暂停-2, 清空所有队列-3, 显示抓手状态-4]
        label_list1 = [0, 0, 0, 0, 0, 0]  # 计数保存位置
        x_limit_l = aicfg.speed_to_x_list  # X值分区
        x_spd_l = aicfg.speed_PLC_X  # X值分区对应的速度值 mm/s
        bool_need_throw = False  # 把点舍去的信号
        '''抓手的偏差补偿列表'''
        X_l_cfg = [aicfg.X1_LEN1, aicfg.X2_LEN1, aicfg.X3_LEN1, aicfg.X4_LEN1, ]
        Y_l_cfg = [aicfg.Y1_LEN1, aicfg.Y2_LEN1, aicfg.Y3_LEN1, aicfg.Y4_LEN1, ]
        T_l_cfg = [aicfg.T1_LEN1, aicfg.T2_LEN1, aicfg.T3_LEN1, aicfg.T4_LEN1, ]

        '''判定本模组, 抓手个数, 抓手状态的强制信号和内容'''
        plc_ctrl_list = aicfg.PLC_ctrl_choose  # PLC的选择执行列表
        num_claw_plc = int(plc_ctrl_list[1]) + int(plc_ctrl_list[2])
        self.num_claw_state = 4 if num_claw_plc > 1 else 2  # 抓手数量
        num_claw1 = self.num_claw_state * 2  # 抓手的状态数量
        list_statu = aicfg.List_claw_statu  # 抓手的状态的赋值列表
        print("进入消费者")
        while True:
            try:
                time.sleep(0.001)  # 预防 while 语句的 睡眠
                '''PLC 发送停止信号时 的处理内容'''
                if self.if_need_stop == 0:  # PLC控制待机 0-待机，1-正常运行
                    if self.photo_n != label_list1[3]:  # 此时 self.photo_n 不会增加
                        label_list1[3] = copy.deepcopy(self.photo_n)
                        self.num_point[8] += self.count_queue_num()  # 清空队列前，所有队列中剩余的点个数
                    time.sleep(1)
                    continue
                '''正常运行时  PLC信号交互   处理内容'''
                if self.photo_n % 30 == 29:
                    if self.photo_n != label_list1[0]:  # 当在29计数时间段内，确保指执行1次
                        label_list1[0] = copy.deepcopy(self.photo_n)
                        self.bool_circulation_process_PLC = True  # PLC通讯心跳
                elif self.photo_n % 100 == 99:
                    if self.photo_n != label_list1[1]:
                        label_list1[1] = copy.deepcopy(self.photo_n)
                        self.bool_get_speed_PLC = True  # 监测传送带速度
                elif self.photo_n % 15 == 5:
                    if self.photo_n != label_list1[2]:
                        label_list1[2] = copy.deepcopy(self.photo_n)
                        self.bool_ctrl_stop = True  # 读取是否需要暂停 --暂停时生产者控制，运行时消费者控制
                '''抓手 重建OP 选择执行'''
                if aicfg.If_claw_goback:
                    if self.choose_claw_go_back():  # 抓手回零判定
                        continue

                '''确认 上一次的抓手抓取信号  发送完成'''
                while self.bool_send_toPLC_claw:  # 等上一次的发送成功后，或上次无发送
                    time.sleep(0.005)

                '''读取+判断 抓手状态'''
                self.list_claw_state = []  # 清空上一次的抓手状态
                self.bool_read_claw_state = True   # 读取+判断 抓手状态
                while len(self.list_claw_state) < 1:
                    time.sleep(0.005)
                # 是否需要屏蔽抓手
                if not aicfg.Bool_use_claw:  # Bool_use_claw = True 时正常
                    for claw_i in range(num_claw1):
                        if list_statu[claw_i] < 2:
                            self.list_claw_state[claw_i] = list_statu[claw_i]  # 强制赋值-忙碌
                # print("消费者---读取抓手状态 time:{}".format(time.time() - t4))
                '''打印 抓手状态'''
                if self.photo_n % 10 == 2:
                    if self.photo_n != label_list1[4]:  # 当在10计数时间段内，确保指执行1次
                        label_list1[4] = copy.deepcopy(self.photo_n)
                        logger7.info("消费者---抓手状态:{}".format(self.list_claw_state))

                '''根据抓手状态来进行下一步判断'''
                zhua_a = 0  # 每次初始化 抓手选择
                for ic in range(self.num_claw_state):  # 根据现在的抓手数量
                    claw_sta1 = sum(self.list_claw_state[2*ic: 2*ic + 2])  # 取出对应的抓手状态list[左闭右开]
                    tidui_l = aicfg.Claw_ch_q[1][ic] if aicfg.claw_section else aicfg.Claw_ch_q[0][ic]
                    if (claw_sta1 == 0) and (not self.judge_empty_queue(tidui_l)):
                        zhua_a = ic + 1; break

                '''选择判断--取队列'''
                if zhua_a == 0:  # 锁定抓手1/2/3/4（起码有一个抓手空闲且对应队列有值）
                    time.sleep(0.1); continue
                else:
                    point_record = self.choose_point1(zhua_a)
                    # print("---消费者---此次循坏到此刻的：{}".format(time.time() - t5))
                    # print("---消费者---取到队列时间：{}".format(time.time()- point_record.get("start_time") ))
                    if point_record is None:
                        logger.info("all record queue are empty, we can sleep")
                        time.sleep(0.5); continue

                    start_time = point_record.get("start_time")  # 拍照时刻的点的时间戳(arm:s)
                    speed_bmq1 = point_record.get("speed")  # -----传送带速度#----mm/s
                    x = point_record.get("worldX")
                    y = point_record.get("worldY")
                    num_cam = int(point_record.get("position")) - 1  # 对应相机下标
                    #  提前写点位表信息
                    list_point = self.get_data_form_p_dict(point_record, 4)
                    # print("---消费者---进入抓手判断 zhua_a：{}".format(zhua_a))
                    '''通过抓手号，取到了该抓手对应的x,y,t 的最终值'''
                    z_n = zhua_a - 1
                    x += X_l_cfg[z_n][num_cam]; y += Y_l_cfg[z_n][num_cam]; lt1 = T_l_cfg[z_n][num_cam]
                    '''预计抓手移动的所需时间内，点随传送带移动的距离'''
                    spd_x = x_spd_l[0] if x < x_limit_l[0] else (x_spd_l[1] if x < x_limit_l[1] else x_spd_l[2])  # 选择X轴速度
                    x_move_len = abs(aicfg.Throw_location[z_n] - x)  # 点到抛料位的距离(mm)
                    will_length = speed_bmq1 * (x_move_len / spd_x + aicfg.time_x_will)  # 点随传送带移动的距离(mm)
                    spend_length = speed_bmq1 * (time.time() - start_time)  # 此时点从拍摄时刻走过的距离(mm)
                    # logger7.info("(消费-{})时机判断：已花:{},预计:{},总共:{},下抓:{}".format(
                    #     zhua_a,int(spend_length), int(will_length), int(y), int(lt1 * speed_bmq1)))
                    '''判断是否来得及抓取'''
                    if float(spend_length + will_length) < y - lt1 * speed_bmq1:  # 此时，传送带未走到位，才有抓到的条件
                        '''读取PLC时间戳，带上抓手号'''
                        self.bool_read_plc_time = [True, zhua_a]  # 读取PLC时间戳
                        while self.bool_read_plc_time[0]:
                            time.sleep(0.002)
                        # print("----@@@@@@@@消费者---获取PLC时间戳(结束)   ：{}".format(time.time()))
                        '''计算抓取时间时刻 ， 并发送'''
                        end_time = self.time_plc + (y / speed_bmq1 - lt1 - (self.time_arm - start_time)) * 1000
                        sec, mill_sec = long2time(end_time)  # 毫秒转时间
                        self.send_toPLC_list = [zhua_a, int(sec), int(mill_sec), int(x)]  # 抓手号 + 抓取信息
                        self.bool_send_toPLC_claw = True  # 触发发送抓取
                        self.num_point[5] += 1  # 抓取ok次数
                        self.grab_gohome_count[z_n] += 1  # 抓手抓取计次
                        '''OK的点 写入 录入点位表的线程队列中'''
                        list_point[9] = 4  # 点位表的第10位(状态位) 写为 4
                        if not self.sql_point_queue.full():
                            self.sql_point_queue.put(list_point)
                    else:
                        '''判定来不及抓取'''
                        if self.num_claw_state == 4:  # 4抓手模式时
                            if zhua_a < 3:  # 现有规则下，只有1，2抓手会写入后续梯队
                                point_record["times_judge"] += 1
                                '''例如：抓1  分段时:第三梯队(2)|正常时:第二梯队(1)'''
                                put_num = zhua_a + 1 if aicfg.claw_section else zhua_a
                                '''队列梯队下标，等级, 点信息'''
                                self.real_put_point_record(put_num, point_record["level"], point_record)
                            else:
                                bool_need_throw = True  # 点丢弃信号
                        else:  # 2抓手模式时
                            if (not aicfg.claw_section) and (zhua_a == 1):  # 只有正常模式的抓手1会录入第二梯队
                                point_record["times_judge"] += 1
                                self.real_put_point_record(1, point_record["level"], point_record)
                            else:
                                bool_need_throw = True  # 点丢弃信号
                        '''点丢弃的执行内容'''
                        if bool_need_throw:
                            '''判断信号立马重置, 点舍去计数, 点位表的第10位(状态位) 写为 5'''
                            bool_need_throw = False; self.num_point[6] += 1; list_point[9] = 5
                            logger4.info("抓手{}-----超出极限，该点抛掉".format(zhua_a))
                            if not self.sql_point_queue.full():
                                self.sql_point_queue.put(list_point)

            except Exception as e:
                logger.error(f"err -- consume_claw_injection1: {e}")
                time.sleep(1)

    '''2021-07-15  开线程使用数据库'''
    def use_thread_sql1(self):
        th1_sql = threading.Thread(target=self.write_point_to_mysql, args=(), name="write_point_to_mysql")
        th1_sql.start()

    '''2021-06-29// 08-06'''
    def write_point_to_mysql(self):
        # 较长休眠判断信号--[1:点位表状态，[2:错误表状态
        list_need_sleep = [False, False, False]
        list_char = aicfg.ERR_LIST  # 错误列表
        # [1:供应商表写入数据库锁，[2
        bool_lock_list = [True, True]
        while True:
            try:
                time.sleep(0.001)
                '''录入点位表'''
                if self.sql_point_queue.empty():
                    list_need_sleep[0] = True
                else:
                    list_need_sleep[0] = False
                    point_list1 = self.sql_point_queue.get()
                    write_mysql(point_list1)
                    time.sleep(0.001)
                '''录入错误表'''
                if self.sql_err_queue.empty():
                    list_need_sleep[1] = True
                else:
                    list_need_sleep[1] = False
                    err_list1 = self.sql_err_queue.get()
                    num_id = 0
                    for id_record in err_list1:
                        num_id += 1
                        if int(id_record) == 1:
                            record_code = list_char.get(str(num_id))
                            list_err_record = [num_id, time.time(), record_code]
                            write_mysql2(list_err_record)
                            logger6.info("PLC-异常记录：{}".format(list_err_record))
                            time.sleep(0.001)
                '''录入客户的供应商表--一般不需要'''
                if aicfg.Bool_supplier:  # 一般都为False
                    write_mysql3()

                bool_need_sleep = list_need_sleep[0] and list_need_sleep[1]  # 仅当全是True 的时候，需要睡1秒
                if bool_need_sleep:  # 由前面的选择结果 决定 是否sleep
                    time.sleep(0.6)
            except Exception as e:
                logger.error(f"sql_write_point  err: {e}")
                time.sleep(0.1)

    '''抓手重建OP'''
    def choose_claw_go_back(self):
        if self.grab_gohome_count[0] >= 1000 and self.list_claw_state[3] == 0:
            self.num_plc_goback = 1  # 06-08 发送PLC归零--抓手编号1-4
            self.bool_claw_goback = True  # 06-08 发送PLC归零--信号
            self.grab_gohome_count[0] = 0
            logger.info("抓手1---抓手归零位--重建OP")
            return True
        elif self.grab_gohome_count[1] >= 1000 and self.list_claw_state[1] == 0:
            self.num_plc_goback = 2  # 06-08 发送PLC归零--抓手编号1-4
            self.bool_claw_goback = True  # 06-08 发送PLC归零--信号
            self.grab_gohome_count[1] = 0
            logger.info("抓手2---抓手归零位--重建OP")
            return True
        elif self.grab_gohome_count[2] >= 1000 and self.list_claw_state[7] == 0:
            self.num_plc_goback = 3  # 06-08 发送PLC归零--抓手编号1-4
            self.bool_claw_goback = True  # 06-08 发送PLC归零--信号
            self.grab_gohome_count[2] = 0
            logger.info("抓手3---抓手归零位--重建OP")
            return True
        elif self.grab_gohome_count[3] >= 1000 and self.list_claw_state[5] == 0:
            self.num_plc_goback = 4  # 06-08 发送PLC归零--抓手编号1-4
            self.bool_claw_goback = True  # 06-08 发送PLC归零--信号
            self.grab_gohome_count[3] = 0
            logger.info("抓手4---抓手归零位--重建OP")
            return True
        else:
            return False

    '''2021-11-04  统计现在队列上的点 个数，并清空'''
    def count_queue_num(self):
        num_all = 0
        num_1 = len(self.queue_all); num_2 = len(self.queue_all[0])
        for jq in range(num_2):  # 梯队数
            for ip in range(num_1):  # 等级数
                num_all += self.queue_all[ip][jq].qsize()  # 统计每个队列上的点
                self.queue_all[ip][jq].queue.clear()  # 清空队列
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
            cv2.imwrite(os.path.join(self.pic_p_use[0], path_), img)

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

    '''一般信号触发函数'''
    def thread_recevived_signal(self):
        list2_need_sleep = [False, False, False]  # 空闲等待信号(有函数被启用时就不等待)
        count_send = [0, 0, 0]  # 时间计数
        judge_count1 = [0, 0, 0]  # 判断计数
        t1_signal = time.time()
        time_up1 = int(aicfg.Frame_time * 6)
        while True:
            try:
                '''计数限制循环'''
                if count_send[0] > 10000:  # 计数限制循环
                    count_send[0] = 0
                count_send[0] += 1
                '''光源检测'''
                if count_send[0] % 60 == 3:  # 光源检测部分 --主体部分
                    if time.time() - t1_signal < 300 or count_send[0] % 120 == 3:  # 开机5分钟内检测频率高一些
                        list2_need_sleep[0] = True
                        self.new_add_global_data[0] = []
                        self.new_add_global_variables[0] = True
                        logger7.info("进入光源判断--序号：{}".format(count_send[0]))
                        guang_t1 = time.time()
                        while len(self.new_add_global_data[0]) == 0:  # 按理 应该是及时反馈
                            time.sleep(0.1)  # 等待数据传来
                            if time.time() - guang_t1 > 3:  # 当等待大于1秒时，跳出
                                break
                        time.sleep(0.3)  # 等待 图片移动完成
                        # logger7.info("2进入光源判断--序号：{}".format(count_send[0]))
                        for pic1 in self.new_add_global_data[0]:  # 对每个图片
                            n_p = 1 if pic1[1] == 0 else 5
                            path_pic = os.path.join(self.pic_p_use[n_p], pic1[0])
                            if not os.path.exists(path_pic):  # 若 图片不在nobox
                                n_p = 0 if pic1[1] == 0 else 4
                                path_pic = os.path.join(self.pic_p_use[n_p], pic1[0])
                                if not os.path.exists(path_pic):  # 若 图片不在havebox
                                    continue
                            # logger7.info("3进入光源判断--序号：{}".format(count_send[0]))
                            value_grey1 = find_grey_value(path_pic)
                            # logger.info("图片：{}---灰度值为：{}".format(pic1, value_grey1))
                            # logger7.info("4进入光源判断--序号：{}".format(count_send[0]))
                            if value_grey1 is None:
                                logger7.info("{}:读取图片或运算失败".format(pic1))
                            else:
                                if value_grey1 < aicfg.light_value:
                                    logger7.info("{}:图片亮度过低,当前值为{},将不再做AI检测".format(pic1, value_grey1))
                                    judge_count1[0] += 1
                                    break
                                # else:
                                #     logger7.info("{}:图片亮度正常---灰度值为：{}".format(pic1, value_grey1))
                if judge_count1[0] > 3:  # 光源检测部分 --发送异常信号
                    judge_count1[0] = 0  # 计数重置
                    self.new_add_global_data[1] = 33  # 光源异常--代号
                    self.new_add_global_variables[1] = True

                '''主动计数 -- 将图片/txt存入上传路径 并记录'''
                if count_send[0] % time_up1 == 1:  # 上传部分 --主体部分
                    # logger.info("进入havebox 上传部分--触发")
                    '''上传信号的 检测触发  部分'''
                    if not self.new_add_global_variables[2]:  # false :表示已有反馈 # true :表示已触发，但没反馈
                        if not list2_need_sleep[1]:  # false :表示 已执行主体 // true :表示 还没有 执行主体部分
                            # 开始触发
                            list2_need_sleep[1] = True  # 把该信号重置成:True 表示 未执行主体函数
                            self.new_add_global_data[2] = []  # 清空 图片路径 数据
                            self.new_add_global_variables[2] = True  # 触发--外部反馈--信号
                '''上传信号的 判断(反馈 和 执行)'''
                if (not self.new_add_global_variables[2]) and list2_need_sleep[1]:  # 已有反馈，且未执行
                    # logger.info("进入havebox 上传部分--执行")
                    for pic_name2 in self.new_add_global_data[2]:  # 复制到上传文件夹
                        txt_name2 = pic_name2[0].replace("jpg", "txt")  # 点信息txt文件
                        num_q = [0, 2] if pic_name2[1] == 0 else [4, 6]
                        cp_p_upload = "cp -f " + self.pic_p_use[num_q[0]] + "/" + pic_name2[0] + " " + \
                                           self.pic_p_use[num_q[1]] + "/"
                        os.system(cp_p_upload)  # 复制图片 到 当天的havebox
                        cp_p_upload_t = "cp -f " + self.pic_p_use[num_q[0]] + "/" + txt_name2 + " " + \
                                      self.pic_p_use[num_q[1]] + "/"
                        os.system(cp_p_upload_t)  # 复制txt 到 当天的havebox
                    self.write_record_num_label()  # 写入记录文件
                    list2_need_sleep[1] = False  # 表示 已经执行 上传操作

                '''主动计数 -- 将nobox存入上传路径 并记录'''
                if aicfg.If_upload_nobox:
                    if count_send[0] % (time_up1 * 21) == 2:  # 上传部分 --主体部分
                        logger.info("进入nobox 上传部分--触发")
                        if not self.new_add_global_variables[3]:  # false :表示已有反馈 # true :表示已触发，但没反馈
                            if not list2_need_sleep[2]:  # false :表示 已执行主体 true :表示 还没有 执行主体部分
                                # 开始触发
                                list2_need_sleep[2] = True  # 未执行主体函数-信号
                                self.new_add_global_data[3] = []  # 清空数据
                                self.new_add_global_variables[3] = True  # 触发--外部反馈--信号
                    if (not self.new_add_global_variables[3]) and list2_need_sleep[2]:  # 已有反馈，且未执行
                        logger.info("进入nobox 上传部分--执行")
                        for pic_name2 in self.new_add_global_data[3]:  # 复制到上传文件夹
                            print("将要拷贝的图片：{}".format(pic_name2))
                            num_q = [1, 3] if pic_name2[1] == 0 else [5, 7]
                            copy_path_upload = "cp -f " + self.pic_p_use[num_q[0]] + "/" + pic_name2[0] + " " + \
                                               self.pic_p_use[num_q[1]] + "/"
                            os.system(copy_path_upload)
                        list2_need_sleep[2] = False

                '''间隔时段 传给PLC现有识别数'''
                if aicfg.If_send_point_num:
                    if count_send[0] % 120 == 3:
                        self.bool_record_count_qp_PLC[0] = True
                    if count_send[0] % 20 == 3:
                        self.bool_record_count_qp_PLC[1] = True

                '''综合判断--需要等待的时间，和重置的信号'''
                bool_need_sleep = list2_need_sleep[0]  # 有函数被启用时就不等待
                if bool_need_sleep:  # 由前面的选择结果 决定 是否sleep
                    list2_need_sleep[0] = False
                    time.sleep(0.001)
                else:
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"thread_recevived_signal  err: {e}")
                time.sleep(0.5)

    '''记录或读取 上传记录'''
    def create_or_read_upload_record(self):
        # 创建或录入--点分类记录
        try:
            txt_name1 = self.pic_p_use[2] + "/point_record_message.txt"
            bool_name_file = os.path.isfile(txt_name1)
            if not bool_name_file:  # 不存在时，创建txt,并写入000
                point_message3 = ""
                for i_lab in range(len(self.label_path)):
                    point_message3 += self.label_path[i_lab] + "," + str(self.list_num_label[0][i_lab]) + ","
                with open(txt_name1, 'w') as tf_1:
                    tf_1.write(point_message3)
                logger7.info("创建新-点信息记录次数-txt文件,并写入 0 值")
            else:  # 文件已存在，说明已经有计数累加记录
                with open(txt_name1, 'r') as tf_2:
                    context1 = tf_2.readlines()
                    logger7.info("txt列表详情：{}".format(context1))
                    logger7.info("列表长度：{}".format(len(context1)))
                    if len(context1) == 0:
                        logger7.info("文件已存在,但上次写入异常，无字符")  # 初始值就为 0 ，不必重新赋值
                    else:
                        context2 = context1[0]
                        txt1 = context2.replace(" ", "").replace("\n", "")
                        txt2 = txt1.split(",")  # 点信息
                        for i_label in range(len(self.label_path)):
                            self.list_num_label[0][i_label] = int(txt2[i_label * 2 + 1])  # 取到文件中的次数数据，赋值到列表
                            logger7.info("已有-点信息记录次数：{}--{}".format(self.label_path[i_label],
                                                                    self.list_num_label[0][i_label]))
        except Exception as e:
            logger8.error(f"err -- create_or_read_upload_record: {e}")
            time.sleep(0.1)

    '''录入点计数信息'''
    def write_record_num_label(self):  # 录入点计数信息
        try:
            point_message3 = ""  # 清空信息
            for i_lab in range(len(self.label_path)):
                point_message3 += self.label_path[i_lab] + "," + str(self.list_num_label[0][i_lab]) + ","
            txt_name1 = self.pic_p_use[2] + "/point_record_message.txt"
            logger.info("更新-上传图片 点信息记录次数-txt文件")
            with open(txt_name1, 'w') as tf_2:
                tf_2.write(point_message3)
        except Exception as e:
            logger.error(f"err --write_record_num_label : {e}")

    '''记录或读取 循环计数记录'''
    def read_circulation_record(self):
        # 创建或录入--点分类记录
        try:
            res_mess1 = [None, None, None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 循环计数各参数设为初始状态
            txt_name_cycle = self.pic_p_use[2] + "/circulation_record_message.txt"
            bool_name_file = os.path.isfile(txt_name_cycle)
            if not bool_name_file:  # 不存在时，创建txt,并写入000
                logger8.info("未找到 循环记录文件, 判断为初始状态，循环计数各参数设为初始状态")
                return res_mess1
            else:  # 文件已存在，说明已经有计数累加记录
                with open(txt_name_cycle, 'r') as tf_cy:
                    contextc = tf_cy.readlines()
                    logger8.info("列表详情：{}".format(contextc))
                    logger8.info("列表长度：{}".format(len(contextc)))
                    if len(contextc) == 0:
                        logger8.info("文件已存在,但上次写入异常，无字符")
                        logger8.info("根据此时状况，判断为初始状态，循环计数各参数设为初始状态")
                        return res_mess1
                    else:
                        contextc2 = contextc[0]
                        txt1 = contextc2.replace(" ", "").replace("\n", "")
                        txt2 = txt1.split(",")  # 点信息
                        if len(txt2) > len(res_mess1):
                            for it in range(len(res_mess1)):
                                if it < 3:
                                    if txt2[it] != "None":
                                        res_mess1[it] = time.mktime(time.localtime(float(txt2[it])))   # 转化时间字符串
                                elif it < 4:
                                    res_mess1[it] = float(txt2[it])  # 转化 浮点数字符串
                                else:
                                    res_mess1[it] = int(txt2[it])
                            logger8.info("读取到 循环计数信息为：{}".format(res_mess1))
                            return res_mess1
                        else:
                            logger8.info("文件已存在,但上次写入异常，字符数量不对")
                            logger8.info("根据此时状况，判断为初始状态，循环计数各参数设为初始状态")
                            return res_mess1
        except Exception as e:
            logger.error(f"read_circulation_record  err: {e}")

    '''录入 循环计数信息'''
    def write_record_circulation(self, rec_mess2):  # 录入 循环计数信息
        try:
            txt_name1 = self.pic_p_use[2] + "/circulation_record_message.txt"
            # logger8.info("更新-循环计数信息-txt文件")
            cycle_message2 = ""
            for i_m in range(len(rec_mess2)):
                cycle_message2 += str(rec_mess2[i_m]) + ","
            with open(txt_name1, 'w') as tf_2:
                tf_2.write(cycle_message2)
        except Exception as e:
            logger.error(f"write_record_circulation  err: {e}")

    def check_point_count(self, time_r1, time_s1):
        try:
            if self.if_need_stop == 0:
                if time_s1[0] is None:
                    return None
                else:
                    len_s1 = round(time.time() - time_s1[0], 2)
                    return len_s1
            else:
                if time_r1[0] is None:

                    return None
                else:
                    len_r1 = round(time.time() - time_r1[0], 2)
                    return len_r1

        except Exception as e:
            logger.error(f"check_point_count  err: {e}")

    def get_run_time_length(self):
        try:
            pass

        except Exception as e:
            logger.error(f"get_run_time_length  err: {e}")

    '''循环检测--线程主体'''
    def record_point_count(self):
        logger8.info("开始  循环检测--线程")
        dict_record_data1 = aicfg.Record_data  # 配置参数
        record_data1 = [int(dict_record_data1["max_once_time_length"]) * 60, dict_record_data1["max_times"],
                        int(dict_record_data1["every_time_length"]) * 60, dict_record_data1["every_ok_count"],
                        dict_record_data1["continuous_times"], ]
        # 读取记录文件
        # res_mess1 = [None, None, None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # [0]:总-运行开始时间戳, [1]:临时-运行开始时间戳, [2]:临时-停顿开始时间戳,
        # [3]:临时-运行时长, [4]:已计时次数, [5]:标记位(1), [6]:标记位(2)(瞬时变量，可不计), [7]:下次将剩余异纤数量,
        # [8-12]:现每阶段异纤个数(5组)
        before_mess1 = self.read_circulation_record()
        logger8.info("@@@@===读取记录数据详情：{}".format(before_mess1))
        before_mess2 = copy.deepcopy(before_mess1)  # deepcopy
        queue_record_a = queue.Queue(maxsize=int(record_data1[4]))  # 存放个数的队列，长度由配置文件中决定
        for ir in range(int(record_data1[4])):  # 将存放队列写满 0 ，以保证取队列时正常
            if not queue_record_a.full():
                queue_record_a.put(before_mess2[ir + 8])
        list_check1 = [0] * int(record_data1[4])  # 记录当前的5次时间段的异纤个数  --每次会覆盖
        # list_bool1 = [0] * int(record_data1[4])  # 记录对应时间段的判断值
        before_num = copy.deepcopy(before_mess2[7])  # 上次程序的 将剩余异纤数量
        list_start_stop = [before_mess2[5], before_mess2[6]]  # 开始、停止标记位  -需要重置
        old_num = 0  # 前次记录个数
        num_run_time = before_mess2[4]  # 记录时间的段编号
        list_time_run = [before_mess2[0], before_mess2[1], None, ]  # [运行开始时刻-总，运行开始时刻-分段, ]
        list_time_stop = [before_mess2[2], None, None, ]  # [停止开始时刻,  ]
        return_data1 = [before_mess2[3], 0]  # 时间返回 [运行时间，此过程的停止时间]
        '''新增'''
        temp_stop_tlen = 0  # 一次计时中的停顿时长累计(预防一次时段中有多次停顿)
        if list_time_run[1] is not None:  # 当临时开始时间戳已有时
            # 停顿时间 = (现在时间 - 临时开始运行时间) - 临时运行时长
            temp_stop_tlen = round(time.time() - list_time_run[1], 2) - return_data1[0]
            return_data1[1] = temp_stop_tlen  # 初始同步
            if temp_stop_tlen < 0:
                logger8.info("由参数读取计算出的停顿时长为负数，估计此时本地时间异常，停顿时长强制为0")
                temp_stop_tlen = 0
            len_r1 = round(time.time() - list_time_run[1] - return_data1[1], 2)  # =现在时间-开始时间-停顿时长
            logger8.info("现在时间戳：{}，此次开始时间戳：{}，停顿时长：{}，运行时长：{}，临时累加时长：{}".format(
                time.time(), list_time_run[1], return_data1[1], len_r1, temp_stop_tlen
            ))
        bool_if_get_num = False
        logger8.info("start--cycle--!!!!")
        while True:
            time.sleep(0.1)
            try:
                '''时间部分'''
                if self.if_need_stop == 0:  # 信号停止中
                    if list_time_stop[0] is None:  # 初始 或 被满5分钟的条件 清空
                        '''把运行时间看作连续，在运行前的停顿无意义，运行中的停顿肯定在某一个时间段内'''
                        if list_time_run[0] is not None:  # 总开始时间存在
                            list_time_stop[0] = time.time()  # 写入此分段中的停顿 初始时间
                            logger8.info("第{}个时间段，停顿开始计时".format(num_run_time))
                    else:
                        return_data1[1] = round(time.time() - list_time_stop[0], 2) + temp_stop_tlen  # 更新停顿时间
                    time.sleep(1)
                    continue
                else:  # 处于运行过程中
                    if list_time_run[0] is None:  # 只会在第一次运行中执行
                        logger8.info("PLC给出运行信号，开始计时检测")
                        list_time_run[0] = time.time()  # 运行开始总计--计时
                        list_time_run[1] = time.time()  # 运行开始分段--计时
                        before_mess1[0], before_mess1[1] = list_time_run[0], list_time_run[1]  # 刷新
                        time.sleep(0.5)
                    else:
                        if list_time_stop[0] is not None:  # 保证连续运行时只做一次
                            list_time_stop[0], before_mess1[2] = None, None  # 停顿时间清空为None
                            temp_stop_tlen = copy.deepcopy(return_data1[1])  #  新增
                        len_r1 = round(time.time() - list_time_run[1] - return_data1[1], 2)  # =现在时间-开始时间-停顿时长
                        # logger8.info("现在时间戳：{}，此次开始时间戳：{}，停顿时长：{}，运行时长：{}，"
                        #              "临时累加时长：{}".format(
                        #     time.time(), list_time_run[1], return_data1[1], len_r1, temp_stop_tlen))
                        before_mess1[3] = len_r1  # 临时-运行时长
                        if len_r1 >= record_data1[2]:  # 现在分段时间 大于 限制时长时
                            '''显示时间刻度'''
                            time_array1 = time.localtime(time.time())  # 格式化时间戳为本地的时间
                            strtime1 = time.strftime("%H:%M", time_array1)
                            time_array2 = time.localtime(list_time_run[1])  # 格式化时间戳为本地的时间
                            strtime2 = time.strftime("%H:%M", time_array2)
                            logger8.info("第{}个时间段({}--{}),停顿{}分钟".format(
                                num_run_time+1, strtime2, strtime1, round(return_data1[1]/60, 1)))
                            '''重置分段计时的变量'''
                            list_time_run[1] = time.time()  # 运行开始分段--计时--满5分钟重置
                            list_time_stop[0] = None  # 停顿时间清空为None
                            return_data1[1] = 0  # 停顿时长置为0
                            temp_stop_tlen = 0  # 停顿累加值 清零
                            before_mess1[1], before_mess1[2], before_mess1[3] = list_time_run[1], None, 0

                            bool_if_get_num = True  # 获取数据开关
                            '''判断是否超过设定的最大时间'''
                            now_time_length_all = (num_run_time + 1) * record_data1[2]  # 现在运行次数*分段时间
                            if now_time_length_all >= record_data1[0] * record_data1[1]:  # >= 每遍时长*最大遍数
                                logger8.info("已经运行{}遍-每遍{}分钟".format(record_data1[1], int(record_data1[0]/60)))
                                logger8.info("发送PLC达标信号")
                                self.bool_up_to_standard = True
                                list_start_stop[1] = 1  # 触发停止
                        else:                   # 不满5分钟时，睡眠跳过
                            before_mess1[7] = before_num + self.num_point[4] - old_num  # 刷新 此段异纤数量
                            self.write_record_circulation(before_mess1)  # 写入记录
                            # logger8.info("现在记录数据详情：{}".format(before_mess1))
                            time.sleep(1)
                            continue

                '''获取异纤数量部分'''
                if bool_if_get_num:
                    bool_if_get_num = False
                    num_run_time += 1
                    before_mess1[4] = num_run_time  # 刷新 循环次数
                    # print("第{}个时间段，开始取数".format(num_run_time))
                    now_differ = copy.deepcopy(before_mess1[7])  # 此次时段增加的个数
                    before_num = 0  # 使用完就 置零
                    old_num = copy.deepcopy(self.num_point[4])  # 前次记录个数
                    if queue_record_a.full():  # 把最早的拿出来
                        throw1 = queue_record_a.get()
                    queue_record_a.put(now_differ)  # 放入最新的
                    for i in range(int(record_data1[4])):
                        list_check1[i] = queue_record_a.get()  # 把现有的全拿出来
                        queue_record_a.put(list_check1[i])
                        before_mess1[i+8] = list_check1[i]  # 刷新 每段异纤数
                    logger8.info("第{}个时间段，最近{}组异纤取数列表:{}".format(
                        num_run_time, int(record_data1[4]), list_check1))

                    if list_start_stop[0] == 0:  # 还未开始产生点
                        # 判断是否开始有点产生
                        bool_start1 = (list_check1[0] > int(record_data1[2] / 10)) and \
                                      (list_check1[1] > int(record_data1[2] / 10))
                        if bool_start1:  # 说明产生点了
                            logger8.info("判断出有效数据产生，开启判断信号")
                            list_start_stop[0] = 1
                            before_mess1[5] = 1  # 刷新 标记位1
                    if list_start_stop[0] == 1:  # 开始产生点位后
                        list_bool1 = [0] * int(record_data1[4])  # 对应 判断值列表 清零
                        for il in range(int(record_data1[4])):
                            if list_check1[il] < int(record_data1[3]):  # 当某一个时间段内的数量 小于 设定阈值
                                list_bool1[il] = 1  # 对应 判断值 =1
                        bool_l1 = (sum(list_bool1) == int(record_data1[4]))  # 达标判断
                        if bool_l1:
                            logger8.info("发送PLC达标信号")
                            self.bool_up_to_standard = True
                            list_start_stop[1] = 1  # 触发停止


                '''完成后重置所有变量'''
                if list_start_stop[1] == 1:
                    list_start_stop = [0, 0]  # 开始、停止标记位
                    return_data1 = [0, 0]  # 时间返回 [运行时间，此过程的停止时间]
                    list_time_run = [None, None, None, ]  # [运行开始时刻-总，运行开始时刻-分段, ]
                    list_time_stop = [None, None, None, ]  # [停止开始时刻,  ]
                    # old_num = 0  # 前次记录个数
                    num_run_time = 0  # 记录时间的段编号
                    for ir in range(int(record_data1[4])):  # 将存放队列写满 0 ，以保证取队列时正常
                        if queue_record_a.full():
                            throw1 = queue_record_a.get()
                        queue_record_a.put(0)
                    before_mess1 = [None, None, None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 初始状态的写入记录参数
                    self.write_record_circulation(before_mess1)  # 写入记录
                    logger8.info("现在记录数据详情：{}".format(before_mess1))
                    time.sleep(3)
                    logger8.info("达标信号给出，重置所有信号")
                    time.sleep(5)

            except Exception as e:
                logger8.error(f"record_point_count  err: {e}")
                time.sleep(1)

    def ctrl_light_alternate(self, bool_ctrl=True):
        while True:
            time.sleep(0.01)
            if self.bool_ctrl_light1[0]:  # 白光
                self.bool_ctrl_light1[0] = False
                # time.sleep(aicfg.Wait_light_time)  # 为确保灯光亮度达到合适的--等待时间
                GPIO.output(self.White_light, GPIO.HIGH)  # 触发高电平-(放大板灯灭)-白光亮
                time.sleep(aicfg.Open_light_time)  # sleep 0.1ms
                GPIO.output(self.White_light, GPIO.LOW)  # 触发低电平-(放大板灯亮)-白光灭
            if self.bool_ctrl_light1[1]:  # 紫外
                self.bool_ctrl_light1[1] = False
                # time.sleep(aicfg.Wait_light_time)  # 为确保灯光亮度达到合适的--等待时间
                GPIO.output(self.UV_light, GPIO.HIGH)  # 触发高电平-(放大板灯灭)-紫光亮
                time.sleep(aicfg.Open_light_time)  # sleep 0.1ms
                GPIO.output(self.UV_light, GPIO.LOW)  # 触发低电平-(放大板灯亮)-紫光灭

    def choose_times_print(self, list_num1=[]):
        bool_output1 = False
        if len(list_num1) == 3:
            dividend1 = self.photo_n  # 被除数
            divisor1 = list_num1[0]  # 除数
            remainder1 = list_num1[1]  # 余数
            register1 = list_num1[2]  # 寄存数
            if dividend1 % divisor1 == remainder1:
                if dividend1 != label_list1[register1]:  # 当在10计数时间段内，确保指执行1次
                    label_list1[register1] = copy.deepcopy(self.photo_n)
                    bool_output1 = True
        return bool_output1

    def start_run_4_4(self):
        '''判断进入模式'''
        if aicfg.If_test_model == 1:  # 进入正常模式
            '''正常模式'''
            if aicfg.If_need_PLC:  # 是否需要PLC参与程序 True:需要
                self.connect_plc()  # 连接PLC
            self.frist_check_AI()  # 初始化、自检
            th1_produce = threading.Thread(target=self.run_produce_AI, args=(), name="run_produce_AI")
            th1_produce.start()
            if aicfg.If_need_PLC:  # 是否需要PLC参与程序 True:需要
                th1_consume = threading.Thread(target=self.consume_claw_injection1, args=(),
                                               name="consume_claw_injection1")
                th1_consume.start()
        elif aicfg.If_test_model == 2:  # 进入仅抓手测试稳定性模式
            self.connect_plc()  # 连接PLC
            self.test_send()
        else:  # 预防配置文件出错--导致异常--记录
            logger.info("配置文件参数错误，请检查--config_armz.py/If_test_model 此参数")
            time.sleep(2)



# SIGINT信号处理
def sigint_handler(signum, frame):
    GPIO.cleanup()
    sys.exit(0)


if __name__ == '__main__':
    logging.config.fileConfig('./share_func/log.conf')
    init_flag = "init.txt"
    if os.path.exists(init_flag):  # 与守护进程形成 呼应
        os.remove(init_flag)
    # 设置信号处理
    run_or_test1 = 1  # 1：正常运行，非1：测试
    signal.signal(signal.SIGINT, sigint_handler)  # 中断进程
    signal.signal(signal.SIGTERM, sigint_handler)  # 软件终止信号
    if run_or_test1 == 1:
        service = AiHjRunService()  # 实例化
        try:
            with open(init_flag, "w+") as f:
                f.write("success")
        except:
            logger.error("write init status error =======")
        service.start_run_4_4()

