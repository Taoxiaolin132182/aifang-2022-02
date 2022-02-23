# coding:utf-8
import json
import os
import sys
import datetime
import time
import logging.config
import requests
import copy
from PIL import Image

# 添加包路径
START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, ".."))
from share_func.choose_arm import back_to_arm_num
# from choose_arm import back_to_arm_num
arm_num = back_to_arm_num()

if arm_num == 1:
    import cfg1_need.config_armz as ai_config
elif arm_num == 2:
    import cfg2_need.config_armz as ai_config

from sql_need.save_point_record import point_record_context, save_point_record
from sql_need.save_err_record import err_context, save_err  # 2020_12_16
from sql_need.save_supplier import supplier_context, save_supplier  # 2021,03,26
from sql_need.save_batch import batch_context, save_batch  # 2021,3,29
from sql_need.save_take_photo import take_photo_context, save_take_photo
from sql_need.save_image_record import image_record_context, save_image_record

logging.config.fileConfig('/opt/app/ai-product-haijiang/ai-hj-service/aiHjService/share_func/log.conf')
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
    oPointRecordContext.ff_color = list1[13]  # 异纤颜色
    oPointRecordContext.ff_type = list1[14]  # 异纤种类
    oPointRecordContext.batch_no = list1[15]  # 批次号
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
    # logger6.info("插入t_point_record成功，记录ID为：%s" % oPointRecordContext.point_id)


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
    bool_judge1 = True #True的时候可以录入，一般为False
    if bool_judge1:
        global supplier
        supplier_list1 = supplier
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
    # logger6.info("插入t_拍照表  成功，记录ID为：%s" % oTakephotoContext.take_photo_id)
    return oTakephotoContext.take_photo_id
#录入-图片表
def write_mysql6(list6):
    # 现在演示插入新记录到t_image_record
    oImageContext = image_record_context()
    oImageContext.take_photo_id = list6[0]  # 拍照编号
    oImageContext.batch_no = list6[4]  # 批次号
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
    # logger6.info("插入t_图片表  成功，记录ID为：%s" % oImageContext.image_id)
    return oImageContext.image_id

'''计算图片的灰度值'''


def find_grey_value(imgpath):
    try:
        img1 = Image.open(imgpath)
        img1.thumbnail((1, 1))
        avg_color = img1.getpixel((0, 0))
        grey_value = round(0.3 * avg_color[0] + 0.6 * avg_color[1] + 0.1 * avg_color[2])
        # logger6.info('grey_value {}'.format(grey_value))
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


def caculate_nearly_point(ai_result, cam_count=3):  # 计算是否是相机重复取同一点，或相近点
    # 有值时，不为空，且进入此处，最少一个值
    # ai_result = {"1":[{},{}],}
    real_point_arr = []
    if cam_count < 3:  # 2颗相机 or 更少
        if len(ai_result) == 1:
            for k1, v1 in ai_result.items():
                for data1 in v1:
                    if check_point_out_range(data1):
                        real_point_arr.append(data1)
        else:
            result2 = ai_result.get("2")  # 3是中间相机（此设备的特例）
            zj_result = copy.deepcopy(result2)
            if "1" in ai_result.keys():
                result1 = ai_result.get("1")
                for data3 in result2:  # data3 = {}
                    for data1 in result1:
                        if check_point_nearby(data1, data3):  # 点接近
                            if data3 in zj_result:
                                zj_result.remove(data3)
                                break
                real_point_arr.extend(result1)  # 一次性添加多个值
            if len(zj_result) > 0:
                real_point_arr.extend(zj_result)
    else:
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


'''本文件中调用sql函数的测试'''
def test_sql_write():
    time_now_1 = time.time()
    run_list = [1, 2, 3, 4, 5, 6]


    list_2 = [12, time.time(), "grab_error"]
    list_4 = ["dsswe1323", "sdf2#ff"]
    batch_txt = list_4[0] + "-" + list_4[1]
    list_5 = [batch_txt, time_now_1, 1]
    list_6 = [3423, "/mnt/data/data/image/nobox/2021_0331/", time_now_1, 1, batch_txt]
    list_1 = [1, 2, 251.542, 2000, 2000, 1000, 1000, 542, 234, 5, "zangmian", 0.75, 1, "red", "bomo", batch_txt]

    if 1 in run_list:  # 点位表
        # list_1 = [1,2,251.542,2000,2000,1000,1000,542,234,5,"zangmian",0.75,1]
        write_mysql(list_1)
    if 2 in run_list:  # 错误表
        # list_2 = [12,time.time(),"grab_error"]
        write_mysql2(list_2)
    if 3 in run_list:  # 供应商表
        # 录入供应商，只录入一次
        write_mysql3()
    if 4 in run_list:  # 大小批次表
        # list_4 = ["dsswe1323","sdf2#ff"]
        write_mysql4(list_4)

    if 5 in run_list:  # 录入-拍照表
        # list_5 = [list_4[0]+"_"+list_4[1],time_now_1,time_now_1 + 0.5,time_now_1+0.6,time_now_1+1,1]
        id5 = write_mysql5(list_5)
        print("拍照表：{}".format(id5))
    if 6 in run_list:  # 录入-图片表
        # list_6 = [3423,"/mnt/data/data/image/nobox/2021_0331/",time_now_1,time_now_1 + 0.5,1]
        id6 = write_mysql6(list_6)
        print("图片表：{}".format(id6))


supplier_bool = True #True 为 可以录入
# 棉花厂供应商
supplier = [
    ['武城发洋', '37050', 'WC-FY1'],
    ['武城银海', '37087', 'WC-YH1'],
    ['武城银恒', '37125', 'WC-YH2'],
    ['新疆利华第一棉花加工厂', '65070', 'XJ-LH-DYMH-JGC1'],
    ['沙湾利华第四加工厂', '65111', 'SW-LH-DS-JGC1'],
    ['铁门关利华尉犁塔里木加工厂', '65149', 'TMG-LH-WLTLM-JGC1'],
    ['呼图壁云龙', '65257', 'HTBYL1'],
    ['昌吉利华佃坝', '65267', 'CJ-LH-DB1'],
    ['昌吉下巴湖', '65324', 'CJ-XBH1'],
    ['玛纳斯沣泽', '65343', 'MNS-FZ1'],
    ['铁门关利华尉犁琼库勒分公司', '65348', 'TMG-LH-WLQKL-FGS1'],
    ['新疆利华第三棉花加工厂', '65379', 'XJ-LH-DSMH-JGC1'],
    ['新疆鸿力棉业有限公司海楼乡包孜墩轧花厂', '65397', 'XJ-HLMY-YXGS-HLXBZDZHC1'],
    ['新疆利华第四棉花加工厂', '65427', 'XJ-LH-DSMH-JGC2'],
    ['新疆利华第五棉花加工厂', '65504', 'XJ-LH-DWMH-JGC1'],
    ['沙湾利华第八加工厂', '65550', 'SW-LH-DB-JGC1'],
    ['昌吉利华老龙河', '65572', 'CJ-LH-LLH1'],
    ['沙湾利华第三棉花加工厂', '65590', 'SW-LH-DS-MHJGC1'],
    ['乌苏福兴棉业', '65794', 'WS-FX-MY1'],
    ['胡杨河利华乌苏高泉', '66003', 'HYH-LH-WSGQ1'],
    ['石河子银康棉业', '66017', 'SHZ-YK-MY1'],
    ['哈密银天棉业', '66023', 'HM-YT-MY1'],
    ['阿拉尔鹏越', '66025', 'ALE-PY1'],
    ['阿拉尔市鹏硕棉业', '66033', 'ALES-PY-MY1'],
    ['石河子银耀棉业', '66060', 'SHZ-YY-MY1'],
    ['石河子利华下野地一分厂', '66064', 'SHZ-LH-XYD-YFC1'],
    ['石河子银安棉业', '66065', 'SHZ-YA-MY1'],
    ['新疆屯南圣洁棉麻', '66073', 'XJ-TNSJ-MM1'],
    ['新疆水控国棉科技铁门关乌鲁克轧花一厂', '66077', 'XJ-SKGMKJ-TMG-WLKZHYC1'],
    ['新疆胡杨河利华乌苏科克兰木', '66091', 'XJ-HYH-LH-WSKKLM1'],
    ['新疆锦硕源', '66142', 'XJ-JSY1'],
    ['石河子都邦天云', '66196', 'SHZ-DBTY1'],
    ['农一师棉麻鹏飞棉业', '66208', 'NYS-MM-PFMY1'],
    ['铁门关利华', '66209', 'TMG-LH1'],
    ['石河子宝达棉业', '66217', 'SHZ-BD-MY1'],
    ['石河子利华下野地二分公司', '66220', 'SHZ-LH-XYD-EFC1'],
    ['阿拉尔利华绿园镇分公司', '66234', 'ALE-LH-LYZ-FGS1'],
    ['五家渠永盛棉业', '66253', 'WJQ-YS-MY1'],
    ['六师五家渠国懋棉麻', '66256', 'LS-WJQ-GM-MM1'],
    ['五家渠市龙佰力', '66264', 'WJQS-LBL1'],
    ['石河子银鹏棉业', '66066', 'SHZ-YP-MY1']
]

if __name__ == '__main__':

    print("参数配置--config/Path_upload:{}".format(ai_config.Path_upload))
    test_sql_write()