# coding=utf-8
'''(2021-12-03) - (天宇羊毛-1.1) - (2抓手) - (ARM1) 模组配置'''

'''此模块特征(不同主机，会有不同)'''
ARM_number = 1  # ARM 1号
Path_upload = "ty1_1.1_arm1_"  # 上传图片路径标记
Mechine_function = "claw"  # 设备模式  claw - 抓手模式， gas - 喷气模式
If_need_PLC = True  # True:正常使用PLC， False:屏蔽PLC相关功能
If_test_model = 1  # 1:正常模式， 2:测试夹爪模式
If_decode_model = False  # True:正常使用删除模型， False:屏蔽 删除模型功能---不删除
If_claw_goback = False  # True:正常使用--需要抓手归零， False:屏蔽 -- 抓手不执行归零
if_need_input_xyt = False  # True: 需要读取PLC端录入的抓手补偿参数，  False: 直接使用配置文件中的参数

Ctrl_light = False  # 控制灯光变量： True = 需要使用GPIO交替控制， False = 使用 白光常亮模式
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

Frame_time = 1.35  # 拍照间隔时长(秒) - 生产者循环中
Bool_sleep_produce = False  # 生产者循环中停顿时间--开启变量(True:执行停顿)
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

# PLC抓手轴速度
speed_to_x_list = [500, 1000]  # X值分区
speed_PLC_X = [500, 600, 800]  # X值分区对应的速度值 mm/s

Speed_of_csd = 200  # 传送带速度 200mm/s(预设)
Speed_rate = 0.0653  # 传送带速度比率：天宇1.1 --32hz--214mm/s
Min_value_X = 30  # 抓取限位X最小(基于传送带边缘)
Max_value_X = 1770  # 抓取限位X最大(基于传送带边缘)
time_x_will = 0.25   # 抓手轴X方向运动的时间补偿，可能通讯有延时或是加减速耗时
light_value = 91  # 最低光源亮度值(小于该值代表光源亮度异常)

# 抓手偏移量 --3相机:[A,C,B] / 2相机:[A,B,None]
X1_LEN1 = [213, 213, 213]        # 抓手1的X轴距离补偿
Y1_LEN1 = [1661.5, 1661.5, 1661.5]        # 抓手1的Y轴距离补偿
T1_LEN1 = [0.46, 0.46, 0]        # 抓手1的下抓时间补偿(减去的时间，值越大，下抓时刻越早)

X2_LEN1 = [213, 213, 213]      # 抓手2的X轴距离补偿
Y2_LEN1 = [1375, 1375, 0]        # 抓手2的Y轴距离补偿
T2_LEN1 = [0.42, 0.42, 0]        # 抓手2的下抓时间补偿

X3_LEN1 = [200, 200, 200]         # 抓手3的X轴距离补偿
Y3_LEN1 = [1500, 1500, 1500]       # 抓手3的Y轴距离补偿
T3_LEN1 = [0.55, 0.55, 0.55]         # 抓手3的下抓时间补偿

X4_LEN1 = [200, 200, 200]       # 抓手4的X轴距离补偿
Y4_LEN1 = [2500, 2500, 2500]       # 抓手4的Y轴距离补偿
T4_LEN1 = [0.55, 0.55, 0.55]         # 抓手4的下抓时间补偿

# 判断羊毛有无参数
Jujge_thre = 150
Jujge_num_thre = 2000

claw_section = False  # True：抓手分段  || False：抓手一致
X_choose_claw = 900  # 通过X值来决定给哪个抓手来抓(基于传送带边缘)  2021-11-04
Judge_queue = [0, 1]  # [x小于阈值时放入第一梯队，x大于等于阈值时放入第二梯队] 2021-11-04
Throw_location = [2200, 2200, 2200, 2200]  # 各抓手的抛料位的x值[1号抓手，2号，3号，4号，]
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
AI_model_choose = 3
# AI_model_cfg_path = "/mnt/data/data/aimodel/20210813_yangrong_model/wool_jetpack44_v1_0_trt_config.json"
# AI_model_cfg_path = "/mnt/data/data/aimodel/wxmf_sansimian_20210816_cleanzm/cotton_jetpack44_v1_0_trt_config.json"
# AI_model_cfg_path = "/mnt/data/data/aimodel/wxmf_sansimian_20210816/cotton_jetpack44_v1_0_trt_config.json"
AI_model_cfg_path = "/mnt/data/data/aimodel/wool_double_model_20210812/wool_double_jetpack44_v1_0_trt_config.json"
AI_save_pic_bool = True  # True:存原图  / False: 不执行
AI_draw_pic_bool = False  # True:把原图分类+画点txt  / False: 不执行
Camera_id = [["35024012", "A", "1"],
             ["35024020", "C", "2"],
             ["39024088", "B", "3"]]  # 天宇羊毛1.1-ARM1 对应相机号
# Camera_id = [["13914456", "A", "1"],
#              ["39024066", "C", "2"],
#              ["35024021", "B", "3"]]  # 蓝本机对应相机号
# Camera_id = [["13914456", "A", "1"],
#              ["35024021", "B", "2"]]  # 蓝本机对应相机号--临时被拆一个

Camera_param_change = [[[2.10, 10.0], [1800, 20000], [0.41, 0.41]],
                       [[2.10, 10.0], [1800, 20000], [0.41, 0.41]],
                       [[2.10, 10.0], [1800, 20000], [0.41, 0.41]],
                       ["Gain", "Exposure", "Gamma"],]


'''PLC相关'''
# mobus server地址
arm1_ip = '192.168.1.128'  # 主机1 IP --ssc-1.2
arm2_ip = '192.168.1.129'  # 主机2 IP
PLC_ip_main = '192.168.1.254'  # 触摸屏IP(需要通讯时)
PLC_ip_frist = '192.168.1.250'  # 第一抓取模组  --ssc-1.2
PLC_ip_second = '192.168.1.xx'  # 第二抓取模组  --ssc-1.2
PLC_ip_third = '192.168.1.xx'  # 添加的出棉机控制PLC  --ssc-1.2 #2021-10-15
PLC_port = 10002  # PLC端口号
PLC_ctrl_choose = [0, 1, 0, 0]  # 选择要连接的PLC模块
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
            "30":"None","31":"None","32":"None","33":"None"} # 故障列表

Bool_supplier = False  # 是否需要录入客户的供应商表

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
    Max_run_time = "D"  # 达标的最大遍数 2021-12-02
    Claws_xyt = "D"  # 抓手补偿位起始值

    '''本机写入'''

    '''M地址'''
    Go_back1 = "M1050"  # 让抓手1 归零-重建OP - 本机写入(写1就去归零)
    Go_back2 = "M1051"  # 让抓手2 归零-重建OP - 本机写入(写1就去归零)
    Up_to_standard = "M100"  # 异纤检测数量--达标信号
    Pop_up = "M301"  # 给PLC1 的弹窗信号
    CHANGE_OK = "M1454"  # 整包羊毛走2遍 完成信号

    '''D地址'''
    Point_record = "D500"  # 写入点的识别数量 2021-08-05


class MELSEC_CODE:
    TONGS_STATUS1 = "M1000"  # 1X轴抓取中du
    START_STATUS1 = "M1001"  # 1X轴开始抓取du
    HOMING_STATUS1 = "M1002"  # 1x轴归位中du
    CTRL_STATUS1 = "M1003"  # 1X轴手动状态du(也是忙碌状态)
    TONGS_HOMING1 = "M1050"  # 1上位机归位信号xie

    TONGS_STATUS2 = "M1100"  # 2X轴抓取中
    START_STATUS2 = "M1101"  # 2X轴开始抓取
    HOMING_STATUS2 = "M1102"  # 2x轴归位中
    CTRL_STATUS2 = "M1103"  # 2X轴手动状态du(也是忙碌状态)
    TONGS_HOMING2 = "M1150"  # 2上位机归位信号

    STOP_ALL1 = "M1400"  # 做完当前数据点，暂停待机（读）
    SLEEP_PLC = "M1402"  # 60s无异纤，给PLC信号
    # DO_ONE_TIME_PLC = "M1450"  # 已运行20分钟，整包羊毛走一遍的时间点信号
    START_OK = "M50"    # 程序确认开启完成信号,PLC断电不保存信号位
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
    ZJ_XINHAO = "D1210"  # 88为正常，77为无意义覆盖信号 ，0为PLC通讯问题，11为相机超时，22为AI返回为空（需要PLC开机写0）
    ARM_XINHAO = "D1212"  # 从1~100循环自增
    ZI_TEST1 = "D2502"   # 测试数据位
    SIGN_BATCH = "M1450"  # 批次信号位
    BIG_BATCH = "D1300"  # 大批次
    SMALL_BATCH = "D1310"  # 小批次
    PENQI = "D101"  # 喷气号1-60号：D101-D160



