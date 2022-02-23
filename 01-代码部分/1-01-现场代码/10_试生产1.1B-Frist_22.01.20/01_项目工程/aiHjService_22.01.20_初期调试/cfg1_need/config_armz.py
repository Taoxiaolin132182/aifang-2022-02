# coding=utf-8
'''(2022-01-24) - (试生产1.1B-NO.3) - (4抓手) - (ARM1) 模组配置'''

'''此模块特征(不同主机，会有不同)'''
ARM_number = 1  # ARM 1号
Path_upload = "ssc_1.1B_arm1_"  # 上传图片路径标记
Mechine_function = "claw"  # 设备模式  claw - 抓手模式， gas - 喷气模式
Check_exist_wool = False  # True:需要检测羊毛有无， False:不检测羊毛有无
If_need_PLC = True  # True:正常使用PLC， False:屏蔽PLC相关功能
If_test_model = 2  # 1:正常模式， 2:测试夹爪模式
If_decode_model = True  # True:正常使用删除模型， False:屏蔽 删除模型功能---不删除

If_claw_goback = False  # True:正常使用--需要抓手归零， False:屏蔽 -- 抓手不执行归零
If_send_point_num = False  # True:给PLC发送现在的识别数量， False:屏蔽 -- 不发送
If_upload_nobox = False  # True: 上传nobox， False: 不传

Ctrl_light = False  # 控制灯光变量： True = 需要使用GPIO交替控制， False = 使用 白光常亮模式
Pin_num = [13, 12]  # 触发光源 GPIO [白光引脚号，紫光引脚号]
Wait_light_time = 0.02  # 为确保灯光亮度达到合适的--等待时间
Open_light_time = 0.2  # 亮灯时长

'''计数检测'''
Record_data = {
    "max_once_time_length": 35,  # 每遍时长-(分钟)
    "max_times": 2,              # 最大遍数-(次)
    "every_time_length": 5,      # 单次时间间隔-(分钟)
    "every_ok_count": 1,       # 单次达标数量-(个)
    "continuous_times": 5,       # 连续次数-(个)
}
# 循环最大遍数：[0]:(True|False)是否启用录入功能,[1]:触发状态,[2]:更新状态,[3]:启用录入功能时的默认的遍数
Run_max_times = [False, False, False, 1]

Frame_time = 1.2  # 拍照间隔时长(秒) - 生产者循环中
Update_times = 60  # 上传频率 次数  (上传快：6  || 慢：60)
Bool_sleep_produce = False  # 生产者循环中停顿时间--开启变量(True:执行停顿/ False:正常模式)
Sleep_time_produce = 1.75  # 生产者循环中停顿时间
Bool_use_claw = True  # True:正常模式 / False:屏蔽抓手
List_claw_statu = [1, 1, 1, 1, 1, 1, 1, 1]   # 0:空闲 / 1:忙碌  / >1 不赋值
Need_time_PLC = 1  # ARM1： 负责主要接收/发送参数的PLC-用[1]
'''数据相关'''
# 程序选择AI返回的label种类
# 强制指定：1-3 ，大于10 则读取PLC选项
Choose_label = 1  # 1,异纤  2，异纤+脏棉 3,异纤+脏棉+mpg 4, 。。。+ yangshi
#  --{"yixian": [[0.32, 0.4], [800, 800]]}  --{类别：[[分数基础值，划分值],[面积基础值，划分值]]}
Choose_type = [
    [{"yixian": [[0.32, 0.4], [800, 800]]}],
    [{"serong": [[0.25, 0.5], [800, 2500]]},
     {"zangmian": [[0.1, 0.5], [800, 2500]]},
     {"shenhuangmao": [[0.25, 0.5], [800, 2500]]}],
    [{"yangshi": [[0.5, 0.5], [10000, 10000]]},
     {"mpg": [[0.15, 0.25], [800, 800]]},
     {"zhonghuangmao": [[0.5, 0.5], [10000, 10000]]}]]

# 同帧-去重的距离限制
Length_same_point_x = 80
Length_same_point_y = 35
#PLC抓手轴速度
speed_to_x_list = [500, 1000]  # X值分区
speed_PLC_X = [700, 1200, 1200]  # X值分区对应的速度值 mm/s

# 喷气值修改
PQ_X = 0
PQ_Y = 0
PQ_T = 0.2

if_need_input_xyt = False  # True: 启用录入PLC端的抓手补偿，False: 不启用
# True: 启用 读取txt文件(web录入) 抓手补偿，False: 不启用
if_read_web_file = [True, r"/mnt/data/data/aimodel/af-config.txt"]
# 抓手偏移量 --3相机:[A,B,C] / 2相机:[A,B,None]
X1_LEN1 = [270, 270, 270]             # 抓手1的X轴距离补偿
Y1_LEN1 = [610, 610, 610]             # 抓手1的Y轴距离补偿
T1_LEN1 = [0.46, 0.46, 0.46]       # 抓手1的下抓时间补偿(减去的时间，值越大，下抓时刻越早)

X2_LEN1 = [275, 275, 275]             # 抓手2的X轴距离补偿
Y2_LEN1 = [1240, 1240, 1240]       # 抓手2的Y轴距离补偿
T2_LEN1 = [0.46, 0.46, 0.46]       # 抓手2的下抓时间补偿

X3_LEN1 = [280, 280, 280]              # 抓手3的X轴距离补偿
Y3_LEN1 = [1605, 1605, 1605]     # 抓手3的Y轴距离补偿
T3_LEN1 = [0.46, 0.46, 0.46]        # 抓手3的下抓时间补偿

X4_LEN1 = [280, 280, 280]               # 抓手4的X轴距离补偿
Y4_LEN1 = [2235, 2235, 2235]      # 抓手4的Y轴距离补偿
T4_LEN1 = [0.46, 0.46, 0.46]         # 抓手4的下抓时间补偿

Speed_of_csd = 300  # 传送带速度 600mm/s(预设)
Speed_rate = 0.0591  # 传送带速度比率：试生产1.1B  50hz -2022-0124
Min_value_X = 30  # 抓取限位X最小
Max_value_X = 1770  # 抓取限位X最小
time_x_will = 0.15   # 抓手轴X方向运动的时间补偿，可能通讯有延时或是加减速耗时
light_value = 95  # 最低光源亮度值(小于该值代表光源亮度异常)
UV_threshold = 130  # 紫光模式识别的阈值

claw_section = False  # True：抓手分段  || False：抓手一致
X_choose_claw = 1132  # 通过X值来决定给哪个抓手来抓(基于传送带边缘)  2021-11-04
Judge_queue = [0, 1]  # [x小于阈值时放入第一梯队，x大于等于阈值时放入第二梯队] 2021-11-04
Throw_location = [2220, 2220, 2220, 2220]  # 各抓手的抛料位的x值[1号抓手，2号，3号，4号，] (分段：0/600; 正常 2200)
Claw_ch_q = [[[0], [0, 1], [0, 1, 2], [0, 1, 2]],
             [[0], [1], [0, 2], [1, 3]]]  # [正常:[各抓手改判空的梯队号], 分段:[各抓手...]]

'''AI相关'''
# AI模型配置文件路径
AI_model_detection = [
    [1, "yolo3", "model_detection_core"],
    [2, "atss", "model_atss_detection"],
    [3, "double", "model_detection_wool_double"],
    [4, "single", "model_detection_wool_single"],
]
# 模型：1:无锡远纺的，2：三丝棉、羊绒，3：羊毛双模型
AI_model_choose = 2
AI_color_label = False  # True : 使用异纤颜色分类模型，False ： 不使用(一般不使用)
# AI_model_cfg_path = "/mnt/data/data/aimodel/20210813_yangrong_model/wool_jetpack44_v1_0_trt_config.json"
AI_model_cfg_path = "/mnt/data/data/aimodel/wxmf_sansimian_20220106/cotton_jetpack44_v1_0_trt_config.json"
# AI_model_cfg_path = "/mnt/data/data/aimodel/wxmf_sansimian_20210816/cotton_jetpack44_v1_0_trt_config.json"
# AI_model_cfg_path = "/mnt/data/data/aimodel/wool_double_model_20210812/wool_double_jetpack44_v1_0_trt_config.json"
AI_save_pic_bool = True  # True:存原图  / False: 不执行
AI_draw_pic_bool = False  # True:把原图分类+画点txt  / False: 不执行
Camera_id = [["36124439", "A", "1"],
             ["43124233", "C", "2"],
             ["36124440", "B", "3"]]  # 试生产1.1B--ARM1 对应相机号
# Camera_id = [["13914456", "A", "1"],
#              ["39024066", "C", "2"],
#              ["35024021", "B", "3"]]  # 蓝本机对应相机号
# Camera_id = [["13914456", "A", "1"],
#              ["35024021", "B", "2"]]  # 蓝本机对应相机号--临时被拆一个

Camera_param_change = [[[2.10, 10.0], [1800, 20000], [0.41, 0.41]],
                       [[2.10, 10.0], [1800, 20000], [0.41, 0.41]],
                       [[2.10, 10.0], [1800, 20000], [0.41, 0.41]],
                       ["Gain", "Exposure", "Gamma"],]
# 调用ai服务的地址
# AI_INFER_ADDRESS = 'http://localhost:8000/infer'
AI_MODELINIT_ADDRESS = 'http://localhost:8000/aimodelInit'
AI_INFER_ADDRESS = 'http://localhost:8000/aiInfer'
AI_CAMINIT_ADDRESS = 'http://localhost:8000/cameraInit'
AI_TAKEPIC_ADDRESS = 'http://localhost:8000/takePic'
AI_SAVEPIC_ADDRESS = 'http://localhost:8000/savePic'
AI_JUDGEPIC_ADDRESS = 'http://localhost:8000/judgeBlurryPic'


'''PLC相关'''
# mobus server地址
arm1_ip = '192.168.1.118'  # 主机1 IP --ssc-1.1-0915
arm2_ip = '192.168.1.119'  # 主机2 IP
PLC_ip_main = '192.168.1.110'  # 触摸屏IP(需要通讯时)
PLC_ip_frist = '192.168.1.111'  # 第一抓取模组  --ssc-1.1-0915
PLC_ip_second = '192.168.1.112'  # 第二抓取模组  --ssc-1.1-0915
PLC_ip_third = '192.168.1.x'  # 添加的控制PLC
PLC_port = 10002  # PLC端口号
PLC_ctrl_choose = [0, 1, 1, 0]  # 选择要连接的PLC模块
Run_choose = [0, 1, 2, 3]  # [main, frist, second] 若有需要，可更改(如交换了前后组抓手，等)
# tip:(无锡现场:[0,1,0]  试生产1.1:[1,1,0]  试生产1.2(4抓手):[1,1,1] )

ERR_LIST = {"1":"1grab_time_abnormal","2":"2grab_time_abnormal","3":"None","4":"None",
            "5":"None","6":"None","7":"arm_lose_power","8":"1servo_not_ready","9":"2servo_not_ready",
            "10":"light_fault","11":"emergency_stop","12":"arm_connect_break","13":"camera_fault",
            "14":"AI_fault","15":"1grab_point_error","16":"2grab_point_error","17":"1grab_process_error",
            "18":"2grab_process_error","19":"1hand_down_time_abnormal","20":"2hand_down_time_abnormal",
            "21":"1hand_grab_time_abnormal",
            "22":"2hand_grab_time_abnormal","23":"1hand_up_time_abnormal","24":"2hand_up_time_abnormal",
            "25":"1hand_back_time_abnormal",
            "26":"2hand_back_time_abnormal","27":"None","28":"None","29":"None",
            "30":"None","31":"None","32":"None","33":"None"}#故障列表

Bool_supplier = False  # 是否需要录入客户的供应商表

'''1.0相机相关设置'''
# 是否连接摄像头 本地连接摄像头设置为True, 未连接设为False
CAMERA_ON = True
# 模拟保存照片
MOCK_SAVE_IMAGE = False
MOCK_SAVE_IMAGE_RESULT_TIME = 0.005
# 摄像头参数
CAMERA_CTRL_WIDTH = 2448
CAMERA_CTRL_HEIGHT = 2048
CAMERA_DEVICE_TUPLE = ("39024076", "48024027", "48024034")
CAMERA_DEVICE_POSITION_MAP = {"39024076":"1","48024027":"2","48024034":"3"}
CAMERA_SAVE_IMAGE = {"39024076": "A", "48024027": "C", "48024034": "B"}#左A右C中B
# CAMERA_DEVICE_TUPLE = ("39024067", "39024071", "39024068")
# CAMERA_DEVICE_POSITION_MAP = {"39024067":"1","39024071":"2","39024068":"3"}
# CAMERA_SAVE_IMAGE = {"39024067": "A", "39024071": "C", "39024068": "B"}#左A右C中B


A_CAMERA_PARAMETER = {
    "Exposure Auto": "Off",
    "Exposure": 1500,
    "Gamma": 0.41,
    "Gain Auto": "Off",
    "Gain": 2.10,
    "Whitebalance Auto": "Off",
    "Whitebalance Mode": "WhiteBalanceMode_Temperature",
    "Whitebalance Temperature": 7200,
    "Trigger Debouncer": 560000.0,
    "Trigger Delay (us)": 800.0,
    "Trigger Mode": "On",
    # "Trigger Activation": "RisingEdge"
    "Trigger Activation": "FallingEdge"
}

C_CAMERA_PARAMETER = {
    "Exposure Auto": "Off",
    "Exposure": 1500,
    "Gamma": 0.41,
    "Gain Auto": "Off",
    "Gain": 2.10,
    "Whitebalance Auto": "Off",
    "Whitebalance Mode": "WhiteBalanceMode_Temperature",
    "Whitebalance Temperature": 7200,
    "Trigger Debouncer": 560000.0,
    "Trigger Delay (us)": 800.0,
    "Trigger Mode": "On",
    # "Trigger Activation": "RisingEdge"
    "Trigger Activation": "FallingEdge"
}

B_CAMERA_PARAMETER = {
    "Exposure Auto": "Off",
    "Exposure": 1800,
    "Gamma": 0.41,
    "Gain Auto": "Off",
    "Gain": 2.10,
    "Whitebalance Auto": "Off",
    "Whitebalance Mode": "WhiteBalanceMode_Temperature",
    "Whitebalance Temperature": 7200,
    "Trigger Debouncer": 560000.0,
    "Trigger Delay (us)": 800.0,
    "Trigger Mode": "On",
    # "Trigger Activation": "RisingEdge"
    "Trigger Activation": "FallingEdge"
}

class PLC_address:

    '''本机读取'''

    '''M地址'''
    Claw1_state = "M1000"  # 抓手1 的抓手状态 - 本机读取(空闲就为0)
    Claw2_state = "M1001"  # 抓手2 的抓手状态 - 本机读取
    Claw1_ctrl_state = "M1002"  # 抓手1 的是否手动状态 - 本机读取(自动为0)
    Claw2_ctrl_state = "M1003"  # 抓手1 的是否手动状态 - 本机读取(自动为0)

    Clear_num_record = "M70"  # 读取是否需要清零-识别数量 2021-08-05
    Err_record = "M500"  # PLC 异常记录初始位2020——1212
    Start_and_stop = "M350"  # 喷气设备的启停信号
    Start_give_cotton = "M110"  # 给棉开始信号  2021-11-29

    '''D地址'''
    Err_status = "D112"  # PLC 异常记录更新位（有变化才写入）2020——1212
    Max_run_times = "D999"  # 棉花最大运行遍数
    Make_up_xyt = "D999"  # 抓手的xyt 补偿参数
    '''本机写入'''

    '''M地址'''
    Go_back1 = "M1050"  # 让抓手1 归零-重建OP - 本机写入(写1就去归零)
    Go_back2 = "M1051"  # 让抓手2 归零-重建OP - 本机写入(写1就去归零)
    Up_to_standard = "M100"  # 异纤检测数量--达标信号
    Pop_up = "M301"  # 给PLC1 的弹窗信号

    '''D地址'''
    Point_record = "D500"  # 写入点的识别数量 2021-08-05
    Show_times = "D90"  # 显示给PLC的运行遍数
    Show_minute = "D92"  # 显示给PLC的分钟数(整数)


class MELSEC_CODE:
    TONGS_STATUS1 = "M1000"  # 1X轴抓取中du
    START_STATUS1 = "M1001"  # 1X轴开始抓取du
    HOMING_STATUS1 = "M1002"  # 1x轴归位中du
    CTRL_STATUS1 = "M1003" #1X轴手动状态du(也是忙碌状态)
    TONGS_HOMING1 = "M1050"  # 1上位机归位信号xie

    TONGS_STATUS2 = "M1100"  # 2X轴抓取中
    START_STATUS2 = "M1101"  # 2X轴开始抓取
    HOMING_STATUS2 = "M1102"  # 2x轴归位中
    CTRL_STATUS2 = "M1103"  # 2X轴手动状态du(也是忙碌状态)
    TONGS_HOMING2 = "M1150"  # 2上位机归位信号

    STOP_ALL1 = "M91"  # 做完当前数据点，暂停待机（读）
    SLEEP_PLC = "M1402"  # 60s无异纤，给PLC信号
    DO_ONE_TIME_PLC = "M1450"  # 已运行20分钟，整包羊毛走一遍的时间点信号
    START_OK = "M50"  # 程序确认开启完成信号,PLC断电不保存信号位
    CHANGE_OK = "M1454"  # 整包羊毛走2遍 完成信号

    ERR_RECORD = "M500"  # PLC 异常记录初始位2020——1212
    ERR_STATUS = "D112"  # PLC 异常记录更新位（有变化才写入）2020——1212


    # TONGS_STOP = "M1010" #stop
    GRAB_TIME_SEC1 = "D1000"  # 抓取时间戳秒(写入)
    GRAB_TIME_MILLSEC1 = "D1002"  # 抓取时间戳毫秒(写入)
    GRAB_POSITION1 = "D1004"  # X轴抓取坐标(写入)
    FEEDBACK_COORDINATES1 = "D1006"#x
    FEEDBACK_SPEED1 = "D1008"#x
    # TONGS_STOP1 = "D1010"  # stopx

    GRAB_TIME_SEC2 = "D1100"  # 抓取时间戳秒(写入)
    GRAB_TIME_MILLSEC2 = "D1102"  # 抓取时间戳毫秒(写入)
    GRAB_POSITION2 = "D1104"  # X轴抓取坐标(写入)
    FEEDBACK_COORDINATES2 = "D1106"
    FEEDBACK_SPEED2 = "D1108"
    # TONGS_STOP2 = "D1110"  # 2stop

    MELSEC_TIME_SEC = "D2000"  # 时间戳秒d
    MELSEC_TIME_MILLSEC = "D2002"  # 时间戳毫秒d
    TONGS_X_SPEED1 = "D2004"  # X轴电机速度d
    TONGS_ORIGIN_COORDINATES1 = "D2006"  # X轴原点坐标d
    TONS_LIMIT_AFTER_COORDINATES1 = "D2008"  # x AFTER limit
    TONS_LIMIT_PRE_COORDINATES1 = "D2010"  # x pre limit
    TONG_CURRENT_COORDINATES1 = "D2012"  # X轴当前坐标
    ZANGMIAN1_POINT1 = "D2014"  # 1一号脏棉回收站坐标
    ZANGMIAN2_POINT1 = "D2016"  # 1二号脏棉回收站坐标

    TONGS_X_SPEED2 = "D2104"  # 2X轴电机速度
    TONGS_ORIGIN_COORDINATES2 = "D2106"  # 2X轴原点坐标
    TONS_LIMIT_AFTER_COORDINATES2 = "D2108"  # x AFTER limit
    TONS_LIMIT_PRE_COORDINATES2 = "D2110"  # x pre limit
    TONG_CURRENT_COORDINATES2 = "D2112"  # 2X轴当前坐标
    ZANGMIAN1_POINT2 = "D2114"  # 2一号脏棉回收站坐标
    ZANGMIAN2_POINT2 = "D2116"  # 2二号脏棉回收站坐标

    '''新增传送带速度'''
    CSD_SPEED1 = "D200"  # 新增传送带速度
    '''新增识别种类'''
    CHOOSE_MODEL = "D1200"
    # CSD_SPEED1 = "D2018"  # 新增传送带速度
    '''新增自检信号'''
    ZJ_XINHAO = "D1210" #88为正常，77为无意义覆盖信号 ，0为PLC通讯问题，11为相机超时，22为AI返回为空（需要PLC开机写0）
    ARM_XINHAO = "D1212"#从1~100循环自增
    ZI_TEST1 = "D2502" #测试数据位
    SIGN_BATCH = "M1450" #批次信号位
    BIG_BATCH = "D1300" #大批次
    SMALL_BATCH = "D1310" #小批次
    PENQI = "D101"  # 喷气号1-60号：D101-D160



