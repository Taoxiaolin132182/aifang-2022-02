# coding=utf-8
import os, sys, time, copy, signal, cv2, json, requests
import multiprocessing
import threading
import logging.config
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("erro--importing RPi.GPIO!")
# 1:点位表 2:错误表 3:供应商 4:批次 6:图片表
from share_func.utils import write_mysql, write_mysql2, write_mysql3, write_mysql4, write_mysql6
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
sys.path.append(os.path.join(START_PY_PATH, "..", "call_code"))
# 需要导入的类
from aimodel.config import *
from aimodel.cameraModel import *
from aimodel.aiModel import *
from aimodel.tritonserver import *



'''日志文件配置部分'''
logger1 = logging.getLogger('temp1')  # 相机进程相关
logger2 = logging.getLogger('temp2')
logger3 = logging.getLogger('temp3')
logger4 = logging.getLogger('temp4')
logger5 = logging.getLogger('temp5')

'''接收外部signal 部分'''
# [0]外部信号，[1]相机异常类
list_sig = [True] * 8
def judge_sig1(signum,frame):
    global list_sig
    print("接收到主动关闭信号：{}".format(signum))
    list_sig[0] = False

signal.signal(signal.SIGUSR1, judge_sig1)

'''创建-守护进程所需文件'''
def daemon_back():
    init_flag = "init.txt"
    try:
        if os.path.exists(init_flag):  # 与守护进程形成 呼应
            os.remove(init_flag)
        with open(init_flag, "w+") as f:
            f.write("success")
    except Exception as e:
        print(f"error--daemon_back:{e}")

class RunMainF1:
    def __init__(self):
        self.qu1 = multiprocessing.Queue(maxsize=4)  # error-queue 程序内错误传输队列
        self.qu2 = multiprocessing.Queue(maxsize=20)  # error-queue PLC 信号 队列
        self.qub1 = multiprocessing.Queue(maxsize=1)  # cam-trigger-queue 触发相机拍照队列
        self.qub2 = multiprocessing.Queue(maxsize=1)  # light-trigger-queue 触发交替光源队列
        self.qub3 = multiprocessing.Queue(maxsize=20)  # sql--queue 数据库表队列
        self.qub4 = multiprocessing.Queue(maxsize=1)  # aiinfer-pic-queue ai算法所需图片队列
        self.qub5 = multiprocessing.Queue(maxsize=1)  # aiinfer-pointdeal-queue ai算法生成点数据队列

        mgr1 = multiprocessing.Manager()  # 实例化一个共享数据
        self.p_pic = mgr1.list()  # 图片路径列表
        pass


    '''等待外部信号 + 内部异常(主进程调用)'''
    def wait_sign(self):
        global list_sig
        bool_sig1 = True
        list_err1 = [11, 22, 33] # 错误代号
        print("开始等待外部信号 + 内部异常")
        print("The process's PID is:", os.getpid())
        while bool_sig1:
            '''外部信号判断'''
            if not list_sig[0]:
                print("类中接收到 关闭程序的信号，等待2秒")
                time.sleep(2); bool_sig1 = False  # 退出程序信号
            '''内部-程序进程错误'''
            if not self.qu1.empty():
                # 需要写对应 error_data 的判断操作
                error_data = self.get_queue(self.qu1)
                if error_data is not None:
                    res_d1 = self.put_queue(self.qu2, list_err1[error_data[0]])
                    time.sleep(8)  # 等待 PLC进程发送完成
                bool_sig1 = False  # 退出程序信号

            time.sleep(2)  # 等待一段时间
        return bool_sig1

# ----------------------预先启动函数-----
    '''程序开始准备阶段'''
    def prepare_work1(self):
        self.create_file_path1()

        pass

    '''创建各类文件夹'''
    def create_file_path1(self):
        # 获取日期时间，生成对应文件夹
        self.p_pic = [None] * 9  # 照片存放路径
        date_today = self.check_date_time()  # 检查本地时间和网络时间
        if date_today is not None:
            date_path1 = date_today + "_inter"
        else:
            date_path1 = time.strftime("%Y_%m%d", time.localtime()) + "_lost"
        self.p_pic[0] = "/mnt/data/data/image_original/img_" + date_path1
        date_path2 = aicfg.Path_upload + date_path1
        pre_path_list1 = ["/mnt/data/data/image_original/", "/mnt/data/data/upload_image/", "/mnt/data/data/image/",
                          "/mnt/data/data/image/havebox/", "/mnt/data/data/image/nobox/"]
        '''[0]ori, [1]have-W, [2]no-W, [3]up-have-W, [4]up-no-W, 
                   [5]have-UV, [6]no-UV, [7]up-have-UV, [8]up-no-UV'''
        self.p_pic[1] = os.path.join(pre_path_list1[3], date_path2 + "_W")
        self.p_pic[2] = os.path.join(pre_path_list1[4], date_path2 + "_W")
        self.p_pic[3] = os.path.join(pre_path_list1[1], date_path2 + "_have_W")
        self.p_pic[4] = os.path.join(pre_path_list1[1], date_path2 + "_no_W")
        if aicfg.Ctrl_light:
            self.p_pic[5] = os.path.join(pre_path_list1[3], date_path2 + "_UV")
            self.p_pic[6] = os.path.join(pre_path_list1[4], date_path2 + "_UV")
            self.p_pic[7] = os.path.join(pre_path_list1[1], date_path2 + "_have_UV")
            self.p_pic[8] = os.path.join(pre_path_list1[1], date_path2 + "_no_UV")

        for ip in range(len(pre_path_list1) + len(self.p_pic)):
            if ip < len(pre_path_list1):
                path_p1 = pre_path_list1[ip]
            else:
                new_n = int(ip - len(pre_path_list1))
                path_p1 = self.p_pic[new_n]
                logger2.info("pic_path({})：{}".format(new_n, path_p1))
            if path_p1 is None:
                break
            else:
                if not os.path.exists(path_p1):
                    os.makedirs(path_p1)
        for iph in range(len(pre_path_list1) - 2):  # 最上级的路径赋权限
            chmod_code1 = "chmod -R 777 " + pre_path_list1[iph] + " &"
            os.system(chmod_code1)

    '''2021-07-07  检查本机系统时间和网络时间'''
    def check_date_time(self):
        list_num1 = [0, True, 0, True]  # internet循环 计数，信号  check_time循环 计数，信号
        beijinTime = None; now_date = None
        while list_num1[1]:
            time.sleep(0.001)
            if list_num1[0] > 1:
                logger2.info("获取网络时间失败")
                list_num1[1] = False; list_num1[3] = False; continue
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
                    logger2.info(beijinTimeStr)
                    beijinTime = time.mktime(time.strptime(beijinTimeStr, "%Y/%m/%d %X"))  # 将beijinTimeStr转为时间戳格式
                    now_date = time.strftime("%Y_%m%d", time.localtime(beijinTime))
                    list_num1[1] = False  # 跳出 internet 循环
            except Exception as e:
                logger2.info(f"err---internet: {e}")
                time.sleep(1)

        while list_num1[3]:  # check_time 循环信号
            time.sleep(0.001)
            if list_num1[2] >= 30:  # 失败计数
                logger2.info("本机系统时间与网络时间不同步--all")
                list_num1[3] = False;  continue
            try:
                if beijinTime is not None:
                    now_time = time.time()
                    if abs(int(beijinTime) - int(now_time)) > 3600:
                        logger2.info("本机系统时间与网络时间不同步--匹配{}次".format(list_num1[2]))
                        list_num1[2] += 1; time.sleep(1)
                    else:
                        logger2.info("本机系统时间与网络时间一致 -- 验证通过")
                        list_num1[3] = False
                        now_date = time.strftime("%Y_%m%d", time.localtime())
                else:
                    logger2.info("获取网络时间失败")
                    list_num1[3] = False
            except Exception as e:
                logger2.info(f"err---check_time: {e}")
                time.sleep(1)
        logger2.info("现在日期：{}".format(now_date))
        return now_date

# ----------------------相机相关控制-----
    '''相机相关控制进程'''
    def cam_ctrl_1(self):
        # 初始化相机，及报错
        # 循环接收信号 和触发拍照，保持返回的图片内存，存储，等
        light_n = 1; cam_p_ex = None  # 交替拍照场景下的相机参数
        if aicfg.Ctrl_light:  # 控制灯光交替线程--是否需要开启线程
            cam_p_ex = self.init_cam_exchange()  # 生成交替拍照的参数列表
        res_in_c, camMod = self.init_camera()  # 初始化相机，返回结果和拍照类
        bool_run = True if res_in_c == 0 else False  # 根据初始化结果来决定是否进入循环
        while bool_run:
            time.sleep(0.05)  # 只关系到拍照间隔的精准性，不影响拍照时间时间戳
            res_ct1 = self.get_queue(self.qub1)  # 接收拍照的触发信号
            if res_ct1 is None:  # 假定 res_ct1 = [num]
                continue
            # 调用拍照
            light_n = self.light_deal1(light_n, cam_p_ex, camMod)  # 光源设置函数，返回光色信号
            t1_c = time.time()  # 拍照时间戳
            res_t_pic = camMod.takePic()  # 拍照函数，返回图片名
            name_p1 = self.deal_tp_name(t1_c, res_t_pic, light_n)  # 根据光色信号，整理图片名和时间戳
            # 这边要写把图像内存等信息 传给self.qub4
            list_data_for_infer = [int(res_ct1[0]), light_n, name_p1, copy.deepcopy(camMod.cameraData)]
            self.put_queue(self.qub4, list_data_for_infer)  # 传给AI的处理进程中 =[拍照号，光色,图片名,图像缓存,]
            if aicfg.AI_save_pic_bool:
                res = camMod.savePic(self.p_pic[0])
                if len(res) == len(aicfg.Camera_id):
                    sql_data_pic1 = [101, int(res_ct1[0]), name_p1]
                    self.put_queue(self.qub3, sql_data_pic1)  # 传给图片表的处理进程中
                else:
                    logger2.info("第{}次拍照的存图失败".format(res_ct1[0]))
                    print("第{}次拍照的存图失败".format(res_ct1[0]))




        pass

    '''初始化相机'''
    def init_camera(self):
        num_camera_init = 1  # 相机初始化结果
        cameraModel = None
        try:
            t1_cam = time.time()
            logger1.info("开始初始化相机")
            model_path1 = aicfg.AI_model_cfg_path  # 加载配置文件路径
            model_config = load_config(model_path1)  # 转换配置文件
            cameraModel = camera_model(model_config)  # 实例化 相机的 类
            result_camera = cameraModel.cameraInit()
            print("相机初始化返回:{}".format(result_camera))
            logger1.info("相机初始化返回:{}".format(result_camera))
            if result_camera is None:
                print("相机初始化--调用服务--失败")
                logger1.info("相机初始化--调用服务--失败")
            else:
                if int(result_camera.get("return_code")) != 0:
                    print("相机初始化--调用服务--服务内部--失败")
                    logger1.info("相机初始化--调用服务--服务内部--失败")
                else:
                    num_camera_init = 0
                    print("初始化相机用时：{}s".format(round(time.time() - t1_cam, 3)))
                    logger1.info("初始化相机用时：{}s".format(round(time.time() - t1_cam, 3)))
        except Exception as e:
            logger1.info(f"error--init_camera:{e}")

        if num_camera_init > 0:  # 连同异常，None, 失败 这些结果
            print("相机初始化--失败 --退出程序")
            logger1.info("相机初始化--失败 --退出程序")
            self.put_queue(self.qu1, [0, "camera"])
        return num_camera_init, cameraModel

    '''初始化相机配置参数(交替)'''
    def init_cam_exchange(self):
        list_cam_param = [[], []]  # 相机参数列表 [[白光参数],[紫光参数]]  2021_09_26
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
                list_cam_param[0].append(cpnow1)
                list_cam_param[1].append(cpnow2)
        print("整理后，相机需要刷入的参数列表：{}".format(list_cam_param))
        logger1.info("整理后，相机需要刷入的参数列表：{}".format(list_cam_param))
        return list_cam_param

    ''' 整理拍照返回的图片名(拍照时间戳，图片名，灯光信号)'''
    def deal_tp_name(self, time1, list_n, ln):
        d_name = [[], [time1]]  # 重置返回参数
        for list_cam in aicfg.Camera_id:
            for name_pic in list_n:
                if list_cam[0] in name_pic:
                    # [[name,0],[name,1],[]]  ---按配置文件中的相机号排序
                    d_name[0].append([name_pic, ln])  # 单项元素为: [图片名, 灯光号]
                    continue
        return d_name  # d_name = [[[name,ln],[name2,ln],],[time]]

    '''循环内的 灯光交替信号处理'''
    def light_deal1(self, ln, cam_list, cameraModel):  # (光源交替信号值,相机曝光参数, )
        if aicfg.Ctrl_light:
            bool_ctrl_light1 = [False, False]  # 每次重置 光源控制
            lnr = 1 - ln  # 信号 0-1 交换
            bool_ctrl_light1[lnr] = True  # 光源触发
            if len(cam_list[0]) > 0:  # 当有相机参数不同时[0][1] 的 len 一致
                for cam_p1 in cam_list[lnr]:  # 某光的具体参数
                    cameraModel.dfsGetPhoto.setCameraParamManu(cam_p1)  # 设入参数
            self.put_queue(self.qub2, bool_ctrl_light1)
        else:
            lnr = 0  # 信号，强制为白光
        return lnr

# ----------------------AI 识别进程-----
    '''AI 识别 进程总控'''
    def infer_ctrl_1(self):
        print("开启了 AI 识别 进程")
        bool_ctrl_cycle = False
        bool_ini, detection_a = self.init_aimodel()
        if bool_ini:
            # 这边要传出错误，给主进程信号，触发退出程序，发送信号给PLC
            pass
        else:
            bool_ctrl_cycle = True

        while bool_ctrl_cycle:
            time.sleep(0.001)
            try:
                data_a1 = self.get_queue(self.qub4)
                if data_a1 is None:  # =[光色,图片名,图像缓存,]
                    time.sleep(0.01); continue
                else:
                    ai_point_data = []; bool_ai_infer = 0; t_ai = time.time()
                    for num_cam in range(len(aicfg.Camera_id)):
                        sn = aicfg.Camera_id[num_cam][0]  # 指定的相机号
                        oriImg = data_a1[3][sn][0]  # oriImg 原始图片数据
                        img_name = data_a1[3][sn][1]  # 当前预测的图片
                        if data_a1[1] == 0:
                            img = data_a1[3][sn][2]  # 处理后的图片
                            res = detection_a[0].aiInfer(oriImg, img, img_name)  # AI识别  res ={}
                        else:
                            res = detection_a[1].detect(oriImg, img_name, aicfg.UV_threshold)

                        # print("第{}次到AI识别结束用时-真实：{}s".format(str(data_a1[0]), round(time.time() - t_ai, 3)))
                        # if self.photo_n in range(20, 60) and (num_cam > 0):
                        #     res = {'boxes': [[627.5390625, 401.0, 1032.510986328125, 886.2000122070312]],
                        #            'scores': [0.76], 'labels': ["yixian"]}  # 虚拟一个点
                        # print("AI识别--返回：{}".format(res))
                        if len(res["labels"]) > 0:  # 有识别才录入
                            list_data_name = [num_cam + 1, res]
                            ai_point_data.append(list_data_name)  # [[1,{box...}],[2,,{box...}]]
                        bool_ai_infer += 1  # AI识别完成信号
                    '''发送结果给 点处理队列'''
                    if bool_ai_infer == len(aicfg.Camera_id):
                        point_d = [data_a1[0], ]
                        self.put_queue(self.qub5, )

            except Exception as e:
                logger1.info(f"error--infer_ctrl_1:{e}")
                time.sleep(0.6)

    def init_aimodel(self):
        # 模型初始化
        bool_ai_init_err = True
        detectionModel = [None, None]; t_in = time.time()
        logger3.info("start init Triton_server")
        model_path1 = aicfg.AI_model_cfg_path  # 加载配置文件路径
        name_aifile = model_path1.split("/")[-2]
        print("加载的模型文件为：{}".format(name_aifile))
        logger3.info("加载的模型文件为：{}".format(name_aifile))
        model_config = load_config(model_path1)  # 加载模型路径
        tritonserverModel = tritonserver(model_config)  # tritonserver init
        tritonserverModel.kill_tritonserver()  # 杀掉可能已经启动的tritonserver模块
        connect_flag = tritonserverModel.start_tritonserver()  # 启动算法服务模块
        if connect_flag:
            print("Triton_server is ready")
            logger3.info("Triton_server is ready")
        else:
            print("aimodelInit error Triton_server is not ready")
            logger3.info("aimodelInit error Triton_server is not ready")
        if bool_ai_init_err:
            # 这边要传出错误，给主进程信号，触发退出程序，发送信号给PLC
            pass
            return bool_ai_init_err, detectionModel
        # 检测模型初始化
        try:
            logger3.info("start init ai_model")
            bool_ai_init_err = False
            if aicfg.AI_model_choose == 1:
                detectionModel[0] = model_detection_core(model_config)
            elif aicfg.AI_model_choose == 2:
                detectionModel[0] = model_atss_detection(model_config)
            elif aicfg.AI_model_choose == 3:
                detectionModel[0] = model_detection_wool_double(model_config)
            elif aicfg.AI_model_choose == 4:
                detectionModel[0] = model_detection_wool_single(model_config)
            else:
                bool_ai_init_err = True
                print("请对应配置文件, 缺失：AI/AI_model_choose")
                logger3.info("请对应配置文件, 缺失：AI/AI_model_choose")
            logger3.info("检测模型初始化:{}".format(aicfg.AI_model_choose))
            if aicfg.Ctrl_light:  # 控制灯光交替线程--是否需要开启线程
                detectionModel[1] = fluorescence_model()
                print("检测UV模型初始化")
                logger3.info("检测UV模型初始化")
        except Exception as e:
            bool_ai_init_err = True
            logger3.error(f"init -error: {e}")
        if bool_ai_init_err:
            # 这边要传出错误，给主进程信号，触发退出程序，发送信号给PLC
            pass
        return bool_ai_init_err, detectionModel

    '''AI 识别 正常灯光'''
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
    '''AI 识别 进程总控'''


# ----------------------PLC 通讯进程-----
    '''PLC通讯相关 的进程'''
    def PLC_ctrl_1(self):
        pass

# ----------------------一般循环线程-----
    '''一般循环线程所在的进程'''
    def general_cycle_fun1(self):

        th4_signal = threading.Thread(target=self.ctrl_light_alternate, args=(), name="ctrl_light_alternate")
        th4_signal.start()

        '''信息录入数据库--线程---循环'''
        th1_sql = threading.Thread(target=self.write_point_to_mysql, args=(), name="write_point_to_mysql")
        th1_sql.start()

        th1_sql.join()  # 进程中，进行线程阻塞，防止该进程退出


    ''' # 控制灯光交替线程--是否需要开启线程'''
    def ctrl_light_alternate(self):
        print("开启灯光控制线程")
        logger1.info("开启灯光控制线程")
        # 相机引脚号
        White_light = 13  # 白光 引脚
        UV_light = 12  # 紫外 引脚
        # GPIO初始化
        GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(White_light, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(UV_light, GPIO.OUT, initial=GPIO.LOW)

        bool_ctrl_l = False
        if aicfg.Ctrl_light:
            bool_ctrl_l = True
            print("开启交替拍照的灯光控制线程")
            logger1.info("开启交替拍照的灯光控制线程")
        else:
            GPIO.output(White_light, GPIO.HIGH)  # 触发高电平-(放大板灯灭)-白光亮
            print("灯光模式为：白光常亮")
            logger1.info("灯光模式为：白光常亮")

        while bool_ctrl_l:
            time.sleep(0.01)
            try:
                l_data1 = self.get_queue(self.qub2)
                if l_data1 is None:
                    continue
                if l_data1[0]:  # 白光
                    GPIO.output(White_light, GPIO.HIGH)  # 触发高电平-(放大板灯灭)-白光亮
                    time.sleep(aicfg.Open_light_time)  # sleep 0.1ms
                    GPIO.output(White_light, GPIO.LOW)  # 触发低电平-(放大板灯亮)-白光灭
                if l_data1[1]:  # 紫外
                    GPIO.output(UV_light, GPIO.HIGH)  # 触发高电平-(放大板灯灭)-紫光亮
                    time.sleep(aicfg.Open_light_time)  # sleep 0.1ms
                    GPIO.output(UV_light, GPIO.LOW)  # 触发低电平-(放大板灯亮)-紫光灭
            except Exception as e:
                logger1.error(f"err---ctrl_light_alternate: {e}")
                time.sleep(0.01)

    '''信息录入数据库 2021-11-23'''
    def write_point_to_mysql(self):
        list_char = aicfg.ERR_LIST  # 错误列表
        '''录入客户的供应商表--一般不需要'''
        if aicfg.Bool_supplier:  # 一般都为False
            write_mysql3()
        while True:
            time.sleep(0.001)
            try:
                '''获取sql 队列'''
                data_s1 = self.get_queue(self.qub3)
                if data_s1 is None:
                    time.sleep(0.05); continue  # 3图+5个点 / 一帧
                else:
                    '''录入数据库表'''
                    if data_s1[0] == 101:  # 图片表代号
                        data_p = data_s1[2]  # d_name = data_p = [[[name,ln],[name2,ln],],[time]]
                        for name_p in data_p[0]:
                            list_6 = [data_s1[1], name_p[0], data_p[1], 1]  # [拍照号，图片名，时间戳，1状态]
                            id6_pic = write_mysql6(list_6)  # 录入图片表
                            '''把图片表返回到数据处理进程'''
                    elif data_s1[0] == 202:  # 点位表代号
                        write_mysql(data_s1[1])
                    elif data_s1[0] == 303:  # 错误表代号
                        num_id = 0
                        for id_record in data_s1[1]:
                            num_id += 1
                            if int(id_record) == 1:
                                record_code = list_char.get(str(num_id))
                                list_err_record = [num_id, time.time(), record_code]
                                write_mysql2(list_err_record)
                                logger1.info("PLC-异常记录：{}".format(list_err_record))
                    elif data_s1[0] == 404:  # 错误表代号
                        write_mysql4(data_s1[1])  # data_s1[1] = [result_big, result_small]

            except Exception as e:
                logger1.error(f"sql_write_point  err: {e}")
                time.sleep(0.1)

#----------------------基础函数-----
    '''放入队列的函数，防None'''
    def put_queue(self, queue1, data1):
        data_th = None  # 返回值预置为 None
        if data1 is not None:  # 当传入的data1 不为 None 时
            if queue1.full():  # 当要put 的队列 满时
                data_th = queue1.get()  # 取出第一个扔掉(保持在手)
            queue1.put(data1)
        return data_th
    '''从队列中拿数据，若队列空则返回None'''
    def get_queue(self, queue2):
        data_g = None  # 返回值预置为 None
        if not queue2.empty():
            data_g = queue2.get()
        return data_g


    '''主控程序--启动各进程'''
    def start_run(self):
        pre_p0 = multiprocessing.Process(target=self.prepare_work1, daemon=True)
        pre_p0.start()

        gen_p1 = multiprocessing.Process(target=self.general_cycle_fun1, daemon=True)
        gen_p1.start()

        cam_p1 = multiprocessing.Process(target=self.cam_ctrl_1, daemon=True)
        cam_p1.start()

        infer_p1 = multiprocessing.Process(target=self.infer_ctrl_1, daemon=True)
        infer_p1.start()

        print("所有进程已经全部开始")
        bool_res1 = self.wait_sign()
        if not bool_res1:
            print("进入退出程序")
            time.sleep(0.5); sys.exit(0)



if __name__ == "__main__":
    logging.config.fileConfig("./log.conf")
    serv1 = RunMainF1()
    daemon_back()  # 删除原来的初始txt，并创建新的txt
    serv1.start_run()