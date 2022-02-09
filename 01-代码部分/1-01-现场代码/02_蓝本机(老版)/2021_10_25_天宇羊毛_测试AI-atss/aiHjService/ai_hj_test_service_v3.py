# coding=utf-8
import logging.config
import os
import signal
import sys
import cv2
from ai_hj_run_service import AiHjRunService
from utils import transform_conveyer_speed, time2long, long2time, write_mysql, find_grey_value, call_ai_service
from utils import caculate_nearly_point, write_mysql2
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!This is probably because you need superuser privileges.")
from count_down_latch import count_down_latch

import config_armz as aiCottonConfig

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
from base import log

logger = logging.getLogger('main')
logger2 = logging.getLogger('remover')
logger4 = logging.getLogger('recorder')

log.init_log("save_db")
log.info("===================================")


'''测试拍照'''


def test_camera1(run_service):
    for i in range(20):
        run_service.takePhoto()
        time.sleep(0.3)
    time.sleep(3)
    pass


def test_init_service(run_service):
    # modbus的IP和端口

    run_service.connect_plc()



def test_initCamera(run_service):
    """
    初始化相机参数，启动相机捕捉画面
    :return 是否全部初始化成功
    """
    isAllCameraInited = True
    cameraCtrlList = []
    for deviceItem in aiCottonConfig.CAMERA_DEVICE_TUPLE:  # 相机设备元组
        if aiCottonConfig.CAMERA_ON:
            oCtrl = tiscamera_ctrl(aiCottonConfig.CAMERA_CTRL_WIDTH, aiCottonConfig.CAMERA_CTRL_HEIGHT)  # 某个相机实例
            logger.info(1)
            bResult = oCtrl.open_device(deviceItem, run_service)  # 打开相机设备，调用函数，返回False
            if bResult:
                logger.info(2)
                bResult = oCtrl.start_capture()  # 开始拍摄，准备好就返回true
                logger.info(3)
                if not bResult:
                    isAllCameraInited = False
                    break
            else:
                isAllCameraInited = False
                break
            run_service.set_camera_param(oCtrl, deviceItem)  # 设置某个相机（实例及标号）#刷入相机取像参数
            cameraCtrlList.append(oCtrl)  # 都添加到相机列表
    # end for
    run_service.oCtrl1 = cameraCtrlList

    return isAllCameraInited  # 相机已经准备好


def test_runPLC(run_service):
    try:
        for ju in range(1, 800000):
            print("---------------------------------------")
            print("第{}次读取时间".format(ju))
            data = run_service.read_data(0)
            print('data', data)
            start_time = time2long(data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_SEC),
                                               data.get(aiCottonConfig.MELSEC_CODE.MELSEC_TIME_MILLSEC))
            print("时间戳是：{}".format(start_time))
            end_time = 4500 + start_time  # 下抓时间
            end_time2 = 8500 + start_time  # 下抓时间
            print("发送时间戳是：{}".format(end_time))
            sec, mill_sec = long2time(end_time)  # 毫秒转时间
            sec2, mill_sec2 = long2time(end_time2)  # 毫秒转时间
            junow = ju % 10
            x = 2100 - junow * 180
            if x < 2000 and x > 500:
                print("发送数据为：{} - {} ，@{}".format(sec, mill_sec, x))
                # print("2-----start_time ----", start_time)
                # print("2-----end_time ----", end_time)
                # print("2-----sec ----", sec)
                # print("2-----mill_sec ----", mill_sec)
                # print("2-----x ------", x)
                # run_service.write_data(int(sec), int(mill_sec), int(x - 30), 0, 0, 1)
                time.sleep(4)
                # run_service.write_data(int(sec2), int(mill_sec2), int(x + 30), 0, 0, 2)
                # time.sleep(6)
    except Exception as e:
        logger.info(f"err---frist_check: {e}")


def test_readPLC(run_service):
    try:
        print("----------开始自检----------")

        '''PLC的读写'''
        test_a = 11
        if test_a == 1:
            print("读取传送带速度")
            namesp = aiCottonConfig.MELSEC_CODE.CSD_SPEED1
            resultsp = run_service._melsec_ctrl.read_dword_data(namesp, 1)  # 读取
            if resultsp is not None:
                print("读取PLC 成功")
                print("参数值：{}".format(resultsp))  # 返回值是resultsp = [1000]
            else:
                print("无法读取PLC")
            time.sleep(10)
        print("-----PLC部分自检")
        #--------------------读取批次号---------------
        t1 = time.time()
        result1_ascii = run_service._melsec_ctrl.read_word_data("D1300", 5)  # 读取
        print("D1300  ASCII:{}".format(result1_ascii))
        result1_char1 = ascii_to_char(result1_ascii)
        print("D1300  char:{}".format(result1_char1))

        result2_ascii = run_service._melsec_ctrl.read_word_data("D1310", 8)  # 读取
        print("D1310  ASCII:{}".format(result2_ascii))
        result2_char1 = ascii_to_char(result2_ascii)
        print("D1310  char:{}".format(result2_char1))

        print("spend time:{} s".format(round(time.time() - t1, 6)))
        #--------------------------------------------
        time.sleep(10)
        name1 = aiCottonConfig.MELSEC_CODE.ZI_TEST1
        data = [123, 456, 789, 1024]
        name2 = aiCottonConfig.MELSEC_CODE.ZJ_XINHAO
        data2 = [77]
        result1 = run_service._melsec_ctrl.write_word_data(name1, data)  # 写入
        print('result1', result1)
        if result1 is not None:
            if result1:
                print("数据写入PLC 成功")
            else:
                print("数据写入PLC 失败")
            time.sleep(0.3)
            result2 = run_service._melsec_ctrl.read_dword_data(name1, 4)  # 读取
            if result2 is not None:
                print("读取PLC 成功")
                print("PLC起始地址：{}，数据为{}".format(name1, result2))
                time.sleep(0.3)
                data = [222, 222, 222, 222]
                result1 = run_service._melsec_ctrl.write_dword_data(name1, data)  # 写入重置
                result3 = run_service._melsec_ctrl.write_dword_data(name2, data2)  # 写入重置自检信号位
            else:
                print("无法读取PLC")
        else:
            print("数据未能写入PLC，请检查原因（IP，端口，集线器模式）")

    except Exception as e:
        logger.info(f"err---frist_check: {e}")

def ascii_to_char(list_int):
    char_batch1 = ""
    for j in range(len(list_int)):
        if list_int[j] == 0:
            continue
        if list_int[j] < 256:
            result_b = chr(list_int[j])  # ASCII码 转成 字符
            print("ASCII码:{} 转成 字符:{}".format(list_int[j], result_b))
            char_batch1 += result_b
        else:
            code_ascii = bin(list_int[j])
            print('code_ascii:{}'.format(code_ascii))
            int1 = code_ascii[-8:]
            int2 = code_ascii[:-8]
            char_a = [int1, int2]
            for i in range(len(char_a)):
                print('2-code{}：{}'.format(i + 1, char_a[i]))
                test_b2 = int(char_a[i], 2)
                result_b = chr(test_b2)  # ASCII码 转成 字符
                print("ASCII码:{} 转成 字符:{}".format(test_b2, result_b))

                char_batch1 += result_b
    print('char_batch1:{}'.format(char_batch1))
    return char_batch1



def test_takepic(run_service):
    try:
        print("----------开始自检----------")

        '''PLC的读写'''

        '''相机模块自检'''
        print("-----等待相机模块加载完成")
        # data = run_service.read_data(2)

        time.sleep(3)
        print("-----Camera部分自检")
        bool_speed = True
        bool_del_aimodel = False
        for jn in range(1, 4000000):
            # time.sleep(1)
            print("第{}次拍照".format(jn))
            # data = run_service.read_data(0)
            # print('data', data)
            # name01 = aiCottonConfig.MELSEC_CODE.CSD_SPEED1
            # while bool_speed:
            #     bReadData = run_service._melsec_ctrl.read_dword_data(name01, 1)
            #     speed2 = transform_conveyer_speed(bReadData[0])
            #     if speed2 < 20:
            #         time.sleep(1)
            #     else:
            #         bool_speed = False
            # bool_speed = True
            image_path = run_service.generate_path(str(jn))  # 返回图片存放路径，组
            run_service._count_down_latch = count_down_latch(len(aiCottonConfig.CAMERA_DEVICE_TUPLE))
            bResult = run_service.take_photo(image_path)
            if not bResult:
                logger.info("相机拍照超时，take photo timeout!")
                logger.info("请检查相机ID  触发参数")
                # data2 = [11]
                # result3 = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入自检信号位
            else:
                time.sleep(1.1)
                '''AI模块自检————调用ai识别'''
                # logger.info("-----AI服务部分自检")
                # ai_result = {}
                # ai_status = True
                # for key in run_service.cameraCtrlListDic:
                #     position = aiCottonConfig.CAMERA_DEVICE_POSITION_MAP[key]  # 相机对应的位置
                #     res = call_ai_service(run_service.cameraCtrlListDic[key])  # 调用ai服务，#返回字符串
                #     if res is None:
                #         ai_status = False
                #         break
                #     ai_result[position] = run_service.processAiData(res.get("data").get("0"), position)
                #     # 返回像素点坐标，相机位置，世界坐标的字典 的列表
                # if not ai_status:
                #     logger.info('AI 返回为None，AI服务出错')
                # #     # data2 = [22]
                # #     # result3 = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入自检信号位
                # else:
                #     logger.info("ai_result ----{}".format(ai_result))
                #     if bool_del_aimodel:
                #         os.system('rm -f /mnt/data/data/aimodel/cotton_model.pb &')
                #         bool_del_aimodel = False
                #         logger.info(
                #             "==========removed aimodel --{}".format(
                #                 time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime())))
                #         time.sleep(1)
                #     # data2 = [88]
                #     # result3 = self._melsec_ctrl.write_dword_data(name2, data2)  # 写入自检信号位
                #     print("----------完成自检----------")
    except Exception as e:
        logger.info(f"err---frist_check: {e}")


def test_print():
    for i in range(100):
        logger.info("测试，第{}次---".format(i + 1))
        time.sleep(2)


# SIGINT信号处理
def sigint_handler(signum, frame):
    GPIO.cleanup()
    sys.exit(0)


if __name__ == '__main__':
    logging.config.fileConfig('log.conf')
    # 设置信号处理
    run_or_test1 = 11  # 1：正常运行，非1：测试
    signal.signal(signal.SIGINT, sigint_handler)  # 中断进程
    signal.signal(signal.SIGTERM, sigint_handler)  # 软件终止信号
    if run_or_test1 == 1:
        service = AiHjRunService()
        service.init_service()  # 调用函数（初始化modbus,及相机）
        service.start()
    else:
        service = AiHjRunService()
        PLC_or_camare1 = 33  # 22：PLC  33：Camera 44:一起初始化
        if PLC_or_camare1 == 22:
            test_init_service(service)
            test_b = 11  # 1：读取PLC测试
            if test_b == 1:
                test_readPLC(service)
            else:
                test_runPLC(service)
        elif PLC_or_camare1 == 33:
            # test_init_service(service)
            test_initCamera(service)
            test_a = 1  # 1：拍照测试
            if test_a == 1:
                test_takepic(service)
        elif PLC_or_camare1 == 44:
            test_init_service(service)
            test_initCamera(service)
        else:
            test_print()
