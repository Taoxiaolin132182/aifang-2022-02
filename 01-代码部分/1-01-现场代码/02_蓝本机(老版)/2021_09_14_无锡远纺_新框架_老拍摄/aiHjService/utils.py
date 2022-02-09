# coding:utf-8

import json
import os
import datetime
import time
import logging.config
import requests
import copy
from PIL import Image
import config_armz as ai_config

from point_deal_record import point_record

from save_point_record import point_record_context, save_point_record
from save_err_record import err_context, save_err #2020_12_16
from save_supplier import supplier_context, save_supplier #2021,03,26
from save_batch import batch_context, save_batch # 2021,3,29
from save_take_photo import take_photo_context, save_take_photo
from save_image_record import image_record_context, save_image_record

logging.config.fileConfig('log.conf')
logger6 = logging.getLogger('sql')

oSavePointRec = save_point_record()
oSaveErrRec = save_err()
osave_supplier = save_supplier()
osave_batch = save_batch()
oSave_takephoto = save_take_photo()
oSave_image = save_image_record()



# 2020.10.31 1hz = 6.53mm/s,PLC的值1005，是10.05hz
def transform_conveyer_speed(hz_speed):
    return round(hz_speed * ai_config.Speed_rate, 3)


'''时间转毫秒'''
def time2long(sec, mill_sec):
    return sec * 1000 + mill_sec

'''毫秒转时间'''
def long2time(num):
    sec = num // 1000
    mill_sec = num % 1000
    return sec, mill_sec


'''同步拍照时，各相机之间去重'''
def check_point_nearby(pointOne, pointTwo):  # （消费者调用，内部）
    return (abs(pointOne.get("worldX") - pointTwo.get("worldX")) < ai_config.Length_same_point_x) and (
            abs(pointOne.get("worldY") - pointTwo.get("worldY")) < ai_config.Length_same_point_y)


'''针对于抓手和传送带的X值的限制'''
'''无锡远纺高处机台参数(400,2150)'''
def check_point_out_range(data1, min_value=ai_config.Min_value_X, max_value=ai_config.Max_value_X):  # 基于设备的参数限制
    x1a = float(data1.get("worldX"))
    # logger.info('此时X的值为:{}'.format(x1a))
    # if x1a < 223 or x1a > 2003: #(395 + 20),,,(0+395+1820-15)
    if x1a < min_value or x1a > max_value:
        return False
    else:
        return True


'''写入数据库'''

#录入点数据
def write_mysql(list1):
    # 现在演示插入新记录到t_point_record
    oPointRecordContext = point_record_context()
    oPointRecordContext.take_photo_id = int(list1[0])  # 拍照编号
    oPointRecordContext.image_id = int(list1[1])  # 图片编号
    oPointRecordContext.speed = list1[2]  # 传送带速度
    oPointRecordContext.type = list1[10]  # 分类
    oPointRecordContext.threshold = list1[11]  # 阈值
    oPointRecordContext.level = int(list1[12])  # 等级
    oPointRecordContext.point_xmax = int(list1[3])  # 点的最大x坐标
    oPointRecordContext.point_ymax = int(list1[4])  # 点的最大y坐标
    oPointRecordContext.point_xmin = int(list1[5])  # 点的最小x坐标
    oPointRecordContext.point_ymin = int(list1[6])  # 点的最小y坐标
    oPointRecordContext.point_xcenter = int(list1[7])  # 点的中心x坐标
    oPointRecordContext.point_ycenter = int(list1[8])  # 点的中心y坐标
    oPointRecordContext.state = int(list1[9])  # 状态[1:新增;2;超出边缘;3:重复;4:成功抓取;5:来不及抓取]
    if not oSavePointRec.execute(oPointRecordContext):
        logger6.info("插入t_point_record失败")
        return
    # end if
    logger6.info("插入t_point_record成功，记录ID为：%s" % oPointRecordContext.point_id)


#录入错误代码
def write_mysql2(list2):
    # 现在演示插入新记录到t_point_record
    oErrRecordContext = err_context()
    oErrRecordContext.err_code = int(list2[0]) #错误代码
    oErrRecordContext.err_time = list2[1]
    oErrRecordContext.err_instructions = list2[2]
    if not oSaveErrRec.execute(oErrRecordContext):
        logger6.info("插入t_err_record失败")
        return
    # end if
    logger6.info("插入t_err_record成功，记录ID为：%s" % oErrRecordContext.id)
#录入供应商-无锡远纺03-29
def write_mysql3(list3= []):
    # 现在演示插入新记录到t_point_record
    bool_judge1 = False #True的时候可以录入，一般为False
    if bool_judge1:
        if not point_record().supplier_bool:
            logger6.info("已有供应商存入数据，不进行再次插入")
        else:

            point_record().supplier_bool = False
            supplier_list1 = point_record().supplier
            oSupplierContext = supplier_context()
            logger6.info(len(supplier_list1))
            for i in range(len(supplier_list1)):
                # print(i)
                oSupplierContext.number = supplier_list1[i][1] #编号
                oSupplierContext.Chinese_name = supplier_list1[i][0] #中文
                oSupplierContext.for_short = supplier_list1[i][2] #简写
                if not osave_supplier.execute(oSupplierContext):
                    logger6.info("插入t_供应商 失败")
                    return
                # end if
                logger6.info("插入t_供应商 成功，记录ID为：%s" % oSupplierContext.number)
    else:
        logger6.info("程序内设置,已有供应商存入数据,不可录入")

#录入大小批次
def write_mysql4(list4):
    # 现在演示插入新记录到t_point_record
    oBatchContext = batch_context()
    oBatchContext.primary_batch = list4[0] #大批次
    oBatchContext.secondary_batch = list4[1] #小批次
    if not osave_batch.execute(oBatchContext):
        logger6.info("插入t_大小批次 失败")
        return
    # end if
    logger6.info("插入t_大小批次 成功，记录ID为：%s" % oBatchContext.id)
#录入-拍照表
def write_mysql5(list5):
    # 现在演示插入新记录到t_takephoto_record
    oTakephotoContext = take_photo_context()
    oTakephotoContext.batch_no = list5[0]  # 批次
    oTakephotoContext.photo_begin_time = list5[1]  # 开始拍照
    oTakephotoContext.photo_end_time = list5[1]  # 结束拍照（图片传回）
    oTakephotoContext.call_ai_begin_time = list5[1]  # 开始调用AI
    oTakephotoContext.call_ai_end_time = list5[1]  # AI返回结果
    oTakephotoContext.state = list5[2]  # 状态：默认为1-有效

    if not oSave_takephoto.execute(oTakephotoContext):
        logger6.info("插入t_拍照表 失败")
        return None
    # end if
    logger6.info("插入t_拍照表  成功，记录ID为：%s" % oTakephotoContext.take_photo_id)
    return oTakephotoContext.take_photo_id
#录入-图片表
def write_mysql6(list6):
    # 现在演示插入新记录到t_image_record
    oImageContext = image_record_context()
    oImageContext.take_photo_id = list6[0]  # 拍照编号
    oImageContext.image_path = list6[1]  # 图片路径
    oImageContext.photo_begin_time = list6[2]  # 开始拍照
    oImageContext.photo_end_time = list6[2]  # 结束拍照（图片传回）
    oImageContext.call_ai_begin_time = list6[2]  # 开始拍照
    oImageContext.call_ai_end_time = list6[2]  # 结束拍照（图片传回）
    oImageContext.state = list6[3]  # 状态：默认为1-有效

    if not oSave_image.execute(oImageContext):
        logger6.info("插入t_图片表 失败")
        return None
    # end if
    logger6.info("插入t_图片表  成功，记录ID为：%s" % oImageContext.image_id)
    return oImageContext.image_id

'''计算图片的灰度值'''


def find_grey_value(imgpath):
    try:
        img1 = Image.open(imgpath)
        img1.thumbnail((1, 1))
        avg_color = img1.getpixel((0, 0))
        grey_value = round(0.3 * avg_color[0] + 0.6 * avg_color[1] + 0.1 * avg_color[2])
        logger6.info('grey_value {}'.format(grey_value))
        # if grey_value < 90:
        #     print("现场光源亮度过低")
        return grey_value
    except Exception as ex:
        logger6.info(ex)
        logger6.info('ERROR: light_detection fault')
        return None


'''调用ai处理'''


def call_ai_service(image_path, timeout=10):
    try:
        response = requests.get(ai_config.AI_INFER_ADDRESS,
                                params={'imagePath': image_path}, timeout=timeout)  # 返回的是一个包含服务器资源的Response对象

        response.content.decode("utf-8")  # response.content返回的类型是bytes，可以通过decode()方法将bytes类型转为str类型
        strs = json.loads(response.text)
        return strs
    except Exception as ex:
        logger6.info(ex)
        logger6.info('ERROR: call ai service faild')
        return None

'''AI模型初始化(需要路径参数，模型的配置文件)'''
def call_model_init(configPath, timeout=60):
    try:
        print("configPath:", configPath)
        response = requests.get(ai_config.AI_MODELINIT_ADDRESS,
                                params={'configPath': configPath}, timeout=timeout)  # 返回的是一个包含服务器资源的Response对象
        response.content.decode("utf-8")  # response.content返回的类型是bytes，可以通过decode()方法将bytes类型转为str类型
        strs = json.loads(response.text)
        print("strs:", strs)
        return strs
    except Exception as ex:
        logger6.info(ex)
        logger6.info('ERROR: call_model_init faild')
        return None

'''调用ai接口(需要路径参数)'''
def call_ai_infer(name_sn, timeout=35):
    try:

        # print("name_sn:{},time:{}".format(name_sn, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')))
        t1 = time.time()
        response = requests.get(ai_config.AI_INFER_ADDRESS,
                                params={'sn': name_sn}, timeout=timeout)  # 返回的是一个包含服务器资源的Response对象
        print("name_sn:{},all-time:{}".format(name_sn, round(time.time() - t1, 4)))
        response.content.decode("utf-8")  # response.content返回的类型是bytes，可以通过decode()方法将bytes类型转为str类型
        strs = json.loads(response.text)

        # print("return- call_ai_infer:{}".format(strs))
        return strs
    except Exception as ex:
        logger6.info(ex)
        logger6.info('ERROR: call_ai_infer faild')
        return None

''' 摄像头初始化(不需要路径参数)'''
def call_camera_init(timeout=60):
    try:
        response = requests.get(ai_config.AI_CAMINIT_ADDRESS, timeout=timeout)  # 返回的是一个包含服务器资源的Response对象
        response.content.decode("utf-8")  # response.content返回的类型是bytes，可以通过decode()方法将bytes类型转为str类型
        strs = json.loads(response.text)
        return strs
    except Exception as ex:
        logger6.info(ex)
        logger6.info('ERROR: call_camera_init faild')
        return None

'''拍照(不需要路径参数)'''
def call_take_pic(timeout=1):
    try:
        response = requests.get(ai_config.AI_TAKEPIC_ADDRESS, timeout=timeout)  # 返回的是一个包含服务器资源的Response对象
        response.content.decode("utf-8")  # response.content返回的类型是bytes，可以通过decode()方法将bytes类型转为str类型
        strs = json.loads(response.text)
        return strs
    except Exception as ex:
        logger6.info(ex)
        logger6.info('ERROR: call_take_pic faild')
        return None

'''保存图片(需要路径参数) 只传一个路径，3张全部保存同一个路径'''
def call_save_pic(pic_dir, timeout=1):
    try:
        # print("pic_dir:{}".format(pic_dir))
        response = requests.get(ai_config.AI_SAVEPIC_ADDRESS,
                                params={'pic_dir': pic_dir}, timeout=timeout)  # 返回的是一个包含服务器资源的Response对象
        response.content.decode("utf-8")  # response.content返回的类型是bytes，可以通过decode()方法将bytes类型转为str类型
        strs = json.loads(response.text)
        return strs
    except Exception as ex:
        logger6.info(ex)
        logger6.info('ERROR: call_save_pic faild')
        return None


'''图片模糊判断(不需要路径参数)'''
def call_judge_pic(timeout=1):
    try:
        response = requests.get(ai_config.AI_JUDGEPIC_ADDRESS, timeout=timeout)  # 返回的是一个包含服务器资源的Response对象
        response.content.decode("utf-8")  # response.content返回的类型是bytes，可以通过decode()方法将bytes类型转为str类型
        strs = json.loads(response.text)
        return strs
    except Exception as ex:
        logger6.info(ex)
        logger6.info('ERROR: call_judge_pic faild')
        return None


'''计算最近的异纤距离'''


def caculate_nearly_point(ai_result):  # 计算是否是相机重复取同一点，或相近点
    # 有值时，不为空，且进入此处，最少一个值
    # ai_result = {"1":[{},{}],}
    real_point_arr = []
    if len(ai_result) == 1 or ("3" not in ai_result.keys()):
        for k1, v1 in ai_result.items():
            for data1 in v1:
                if check_point_out_range(data1):
                    real_point_arr.append(data1)
    else:
        result3 = ai_result.get("3")  # 3是中间相机（此设备的特例）
        zj_result = copy.deepcopy(result3)
        if "1" in ai_result.keys():
            result1 = ai_result.get("1")
            for data3 in result3:  # data3 = {}
                for data1 in result1:
                    if check_point_nearby(data1, data3):  # 点接近
                        if data3 in zj_result:
                            zj_result.remove(data3)
                            break
            real_point_arr.extend(result1)  # 一次性添加多个值
        if "2" in ai_result.keys():
            result2 = ai_result.get("2")
            for data3 in result3:
                for data2 in result2:
                    if check_point_nearby(data2, data3):  # 点接近
                        if data3 in zj_result:
                            zj_result.remove(data3)
                            break
            real_point_arr.extend(result2)  # 一次性添加多个值
        if len(zj_result) > 0:
            real_point_arr.extend(zj_result)
    if len(real_point_arr) > 1:
        # 2021-0702 要加个数限制和筛选排序
        new_s = sorted(real_point_arr, key=lambda e: e.__getitem__('worldY'))  # 按Y排序
        # print(" after sort real_point_arr ",new_s)
        return new_s  # new_s = [{},{}...]
    else:
        return real_point_arr
