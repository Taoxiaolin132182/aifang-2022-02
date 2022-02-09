# coding=utf-8
import sys, os, time, signal, copy, queue, cv2, json, requests
import logging.config
import threading
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.dummy import Pool as processPool
from random import randint
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!")

# import share_func.utils
from share_func.utils import transform_conveyer_speed, time2long, long2time, find_grey_value, caculate_nearly_point
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




class AiFangRunService:
    def __init__(self):
        self.gl_num_a = [0, 0, 0, 0, 0, 0, 0, 0, 0,]
        self.gl_bool_a = [False, False, False, False, False, False, ]


    


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

