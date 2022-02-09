# coding= utf-8

import os

# Log save path
LOG_DIR = f"{os.path.dirname(os.path.realpath(__file__))}/../logs"

'''模组配置'''
# 摄像头参数
CAMERA_CTRL_WIDTH = 2448
CAMERA_CTRL_HEIGHT = 2048
CAMERA_SAVE_IMAGE = {"39024076": "A", "48024027": "C", "48024034": "B"}  # 左A右C中B -仁杰羊毛-ARM1 --2021_0317
# CAMERA_SAVE_IMAGE = {"48024031": "A", "48024039": "B"}  # 左A右B - 试生产1.2 ARM1
# CAMERA_SAVE_IMAGE = {"13914456": "A", "35024021": "B"}  # 左A右C中B --蓝本临时
# CAMERA_SAVE_IMAGE = {"13914456": "A", "39024066": "C", "35024021": "B"}  # 左A右C中B --蓝本临时
A_CAMERA_PARAMETER = {
    "Trigger Debouncer": 560000.0,
    "Trigger Delay (us)": 800.0,
    "Trigger Mode": "On",
    # "Trigger Activation": "RisingEdge"
    "Trigger Activation": "FallingEdge",
    "CD_busy": False,  # CD参数必须要以CD_开始
    "Whitebalance Auto": "Off",
    "Whitebalance Mode": "WhiteBalanceMode_Temperature",
    "Whitebalance Temperature": 7200,
    # "Whitebalance Green": 64,
    # "Whitebalance Blue": 115,
    # "Whitebalance Red": 125
    "Gain Auto": "Off",
    "Gain": 2.10,
    "Exposure Auto": "Off",
    "Exposure": 1500,
    "Gamma": 0.41,
}

C_CAMERA_PARAMETER = {
    "Trigger Debouncer": 560000.0,
    "Trigger Delay (us)": 800.0,
    "Trigger Mode": "On",
    # "Trigger Activation": "RisingEdge"
    "Trigger Activation": "FallingEdge",
    "CD_busy": False,  # CD参数必须要以CD_开始
    "Whitebalance Auto": "Off",
    "Whitebalance Mode": "WhiteBalanceMode_Temperature",
    "Whitebalance Temperature": 7200,
    # "Whitebalance Green": 64,
    # "Whitebalance Blue": 115,
    # "Whitebalance Red": 125
    "Gain Auto": "Off",
    "Gain": 2.10,
    "Exposure Auto": "Off",
    "Exposure": 1500,
    "Gamma": 0.41,
}

B_CAMERA_PARAMETER = {
    "Trigger Debouncer": 560000.0,
    "Trigger Delay (us)": 800.0,
    "Trigger Mode": "On",
    # "Trigger Activation": "RisingEdge"
    "Trigger Activation": "FallingEdge",
    "CD_busy": False,  # CD参数必须要以CD_开始
    "Whitebalance Auto": "Off",
    "Whitebalance Mode": "WhiteBalanceMode_Temperature",
    "Whitebalance Temperature": 7200,
    # "Whitebalance Green": 64,
    # "Whitebalance Blue": 115,
    # "Whitebalance Red": 125
    "Gain Auto": "Off",
    "Gain": 2.10,
    "Exposure Auto": "Off",
    "Exposure": 1800,
    "Gamma": 0.41,
}

