#coding=utf-8
'''123高处模组配置'''
#识别选择
CHOOSE_MODEL = 1  #1,异纤  2，异纤+脏棉

ARM_NUM = 1 #1号ARM
#工控机配置
DEBUG_MODE = True
# 是否连接摄像头 本地连接摄像头设置为True, 未连接设为False
CAMERA_ON = True
CAMERA_OFF_MOCK_TIME = 2 #模拟摄像机启动时间

JIBIAN = True # 是否有摄像机参数文件校正畸变

#debug camera
DEBUG_CAMERA = False
BOOL_SLEEP = False
SLEEP_TIME = 4.1

# 模拟ai接口返回, ai接口可调用设为False, 不可调用用mock设为True
MOCK_MODE = False
MOCK_AI_RESULT_TIME = 0.015 #模拟ai接口返回时间
# 模拟保存照片
MOCK_SAVE_IMAGE = False
MOCK_SAVE_IMAGE_RESULT_TIME = 0.005
# mobus server地址
MELSEC_SERVER_IP_F = '192.168.1.254'
MELSEC_SERVER_IP = '192.168.1.250'
MELSEC_SERVER_PORT = 10002

# 摄像头参数
CAMERA_CTRL_WIDTH = 2448
CAMERA_CTRL_HEIGHT = 2048
CAMERA_DEVICE_TUPLE = ("13024367", "12024382", "13024376")
CAMERA_DEVICE_POSITION_MAP = {"13024367":"1","12024382":"2","13024376":"3"}
CAMERA_SAVE_IMAGE = {"13024367": "A", "12024382": "C", "13024376": "B"}#左A右C中B
# CAMERA_DEVICE_TUPLE = ("39024067", "39024071", "39024068")
# CAMERA_DEVICE_POSITION_MAP = {"39024067":"1","39024071":"2","39024068":"3"}
# CAMERA_SAVE_IMAGE = {"39024067": "A", "39024071": "C", "39024068": "B"}#左A右C中B
Choose_type = [["yixian"], ["yixian", "zangmian"]]
# 传送带速度
CONVEYER_SPEED = 754.2
# 抓手在横杆上的速度
TONGS_X_SPEED = 1.2
# 抓手时间
TONGS_TIME = 0
# 设备间隔距离
DEVICE_LENTH = 10000
# 拍照间隔时间 毫秒
# TAKE_PHOTO_INTERVAL = 6650
TAKE_PHOTO_INTERVAL = 0
#去重的距离限制
REAL_POINT_LIMIT = 35
MIDDLE_DIFF_Y = 25

X1_LEN1 = 0 #抓手1的Y轴距离补偿
Y1_LEN1 = -40 #抓手1的Y轴距离补偿
T1_LEN1 = -0.17 #抓手1的下抓时间补偿
# T1_LEN2 = -0.7 #抓手1的下抓时间补偿
X2_LEN1 = 0 #抓手1的Y轴距离补偿
Y2_LEN1 = 665 + 5 #抓手2的Y轴距离补偿
T2_LEN1 = -0.25 #抓手2的下抓时间补偿

#要减去的X，Y的参数值
LEFT_DIFF_Y = 55
DIFF_X = 0
Classification_threshold = 0.3
Suspected_threshold = 0.1
Other_threshold = 0.1

#要上传图片的路径
Path_upload = "wx1_arm1_"

MAX_RAIL_LENTH = 20000
ERR_LIST = {"1":"1grab_time_abnormal","2":"2grab_time_abnormal","3":"None","4":"None",
            "5":"None","6":"None","7":"arm_lose_power","8":"1servo_not_ready","9":"2servo_not_ready",
            "10":"light_fault","11":"emergency_stop","12":"arm_connect_break","13":"camera_fault",
            "14":"AI_fault","15":"1grab_point_error","16":"2grab_point_error","17":"1grab_process_error",
            "18":"2grab_process_error","19":"1hand_down_time_abnormal","20":"2hand_down_time_abnormal","21":"1hand_grab_time_abnormal",
            "22":"2hand_grab_time_abnormal","23":"1hand_up_time_abnormal","24":"2hand_up_time_abnormal","25":"1hand_back_time_abnormal",
            "26":"2hand_back_time_abnormal","27":"None","28":"None","29":"None","30":"None","31":"None","32":"None","33":"None"}#故障列表

A_CAMERA_PARAMETER = {
    "Exposure Auto": "Off",
    "Exposure": 2600,
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
    # "Whitebalance Green": 64,
    # "Whitebalance Blue": 115,
    # "Whitebalance Red": 125
}

C_CAMERA_PARAMETER = {
    "Exposure Auto": "Off",
    "Exposure": 2800,
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
    # "Whitebalance Green": 64,
    # "Whitebalance Blue": 115,
    # "Whitebalance Red": 125
}

B_CAMERA_PARAMETER = {
    "Exposure Auto": "Off",
    "Exposure": 2800,
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
    # "Whitebalance Green": 64,
    # "Whitebalance Blue": 115,
    # "Whitebalance Red": 125
}
# "Gain Auto": "off",

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

    STOP_ALL1 = "M1400"#做完当前数据点，暂停待机（读）
    SLEEP_PLC = "M1402"#60s无异纤，给PLC信号
    DO_ONE_TIME_PLC = "M1450"  # 已运行20分钟，整包羊毛走一遍的时间点信号
    START_OK = "M50" #程序确认开启完成信号,PLC断电不保存信号位
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

# 调用ai服务的地址
AI_INFER_ADDRESS = 'http://localhost:8000/infer'

AI_MOCK_RESULT_LIST = [
    {
        "return_code": 0,
        "return_message": "success",
        "data": {
            "boxes": [
                [
                    1552.3125,
                    59.083335876464844,
                    1727.625,
                    249
                ],
                [
                    1820.0625,
                    1589.3333740234375,
                    1973.0625,
                    1749.3333740234375
                ],
                [
                    482.90625,
                    276.5,
                    654.234375,
                    362.66668701171875
                ],
                [
                    275.12109375,
                    297.66668701171875,
                    373.93359375,
                    394.3333435058594
                ]
            ],
            "scores": [
                0.8373541235923767,
                0.7823050618171692,
                0.7804604172706604,
                0.6749081611633301
            ],
            "labels": [
                0,
                0,
                0,
                0
            ]
        }
    },
    {
        "return_code": 0,
        "return_message": "success",
        "data": {
            "boxes": [
                [
                    1839.1875,
                    1297.3333740234375,
                    1925.25,
                    1462.666748046875
                ],
                [
                    78.193359375,
                    44,
                    304.8046875,
                    322.66668701171875
                ],
                [
                    815.6015625,
                    858.6666870117188,
                    858.234375,
                    918.6666870117188
                ]
            ],
            "scores": [
                0.36077889800071716,
                0.3519790470600128,
                0.2142765074968338
            ],
            "labels": [
                0,
                0,
                0
            ]
        }
    },
    {
        "return_code": 0,
        "return_message": "success",
        "data": {
            "boxes": [],
            "scores": [],
            "labels": []
        }
    }
]
