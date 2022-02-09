import os
import sys
import time

'''
@author maoyanwei
本测试模块用于演示和测试保存数据到数据库
'''

#添加包路径
START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, "..","..", ".."))
#需要导入的类
from base import log
from base.timer_thread import simple_task_thread
from save_take_photo import take_photo_context
from save_take_photo import save_take_photo
from save_image_record import image_record_context
from save_image_record import save_image_record
from save_point_record import point_record_context
from save_point_record import save_point_record
from save_err_record import err_context, save_err #2020_12_16
from save_supplier import supplier_context, save_supplier #2021,03,26
from save_batch import batch_context, save_batch # 2021,3,29

from utils import write_mysql, write_mysql2, write_mysql3, write_mysql4, write_mysql5, write_mysql6

def test_main():
    #本模块需要初始化自己的日志系统

    oPointRecordContext = ["A","B","C","D","E","F","G"]

    log.init_log("save_db")
    log.info("===================================")

    #若要处理一些定时任务，比如自动删除旧的数据，需要开启下面定时任务线程
    oTaskThread = simple_task_thread("simple_task")
    oTaskThread.start()

    # #工厂编号
    # supplier_context_before = ""
    # supplier_context_now = ["武城发洋", "武城银海", "武城银恒", "新疆利华第一棉花加工厂", "沙湾利华第四加工厂"]
    # supplier_context_short = ["WC-FY1", "WC-YH1", "WC-YH2", "XJ-LHDYMHJGC", "SW-LHDSJGC"]
    # supplier_list1 = point_record().supplier
    # osave_supplier = save_supplier()
    # for i in range(len(supplier_list1)):
    #
    #     supplier_context_before = supplier_context()
    #     supplier_context_before.number = supplier_list1[i][1] #编号
    #     supplier_context_before.Chinese_name = supplier_list1[i][0] #中文
    #     supplier_context_before.for_short = supplier_list1[i][2] #简写
    #
    #     if not osave_supplier.execute(supplier_context_before):
    #         print("插入t_supplier_context失败")
    #         return
    #     #end if
    #     print("插入t_supplier_context成功，记录ID为：%s" % supplier_context_before.number)
    #
    # #大小批次
    # batch_now = ""
    # batch_primary = ["a1234","b1234","c1234","d1234","e1234"]
    # batch_secondary = ["a12345","b12345","c12345","d12345","e12345"]
    # osave_batch = save_batch()
    #
    # for i in range(min(len(batch_primary), len(batch_secondary))):
    #
    #     batch_now = batch_context()
    #     batch_now.primary_batch = batch_primary[i] #大批次
    #     batch_now.secondary_batch = batch_secondary[i] #小批次
    #
    #
    #     if not osave_batch.execute(batch_now):
    #         print("插入t_supplier_context失败")
    #         return
    #     #end if
    #     print("插入t_supplier_context成功，记录ID为：%s" % batch_now.id)

    #错误记录表
    oSaveErrRec = save_err()
    oErrRecordContext = err_context()
    oErrRecordContext.err_code = 12  # 错误代码
    oErrRecordContext.err_time = time.time()
    oErrRecordContext.err_instructions = "sadwew"
    if not oSaveErrRec.execute(oErrRecordContext):
        print("插入t_err_record失败")
        return
    # end if
    print("插入t_err_record成功，记录ID为：%s" % oErrRecordContext.id)


    #构造存储t_take_photo_record操作，这个对象可以反复使用，非线程安全
    oSaveTakePhoto = save_take_photo()
    #现在演示插入新记录到t_take_photo_record
    oTakePhotoContext = take_photo_context()
    oTakePhotoContext.batch_no = "no111" #批次
    oTakePhotoContext.photo_begin_time = time.time() #拍照开始时间
    oTakePhotoContext.photo_end_time = oTakePhotoContext.photo_begin_time + 10 #拍照结束时间
    oTakePhotoContext.call_ai_begin_time = oTakePhotoContext.photo_begin_time + 1 #调用AI开始时间
    oTakePhotoContext.call_ai_end_time = oTakePhotoContext.photo_begin_time + 3 #调用AI结束时间

    if not oSaveTakePhoto.execute(oTakePhotoContext):
        print("插入t_take_photo_record失败")
        return
    #end if
    print("插入t_take_photo_record成功，记录ID为：%s" % oTakePhotoContext.take_photo_id)
    #现在演示更新刚才插入的记录
    oTakePhotoContext.batch_no = "no222" #批次
    oTakePhotoContext.state = 0 #状态[0:无效;1:有效]
    if not oSaveTakePhoto.execute(oTakePhotoContext):
        print("更新t_take_photo_record失败")
        return
    #end if
    print("更新t_take_photo_record成功")

    #构造存储t_image_record操作，这个对象可以反复使用，非线程安全
    oSaveImageRec = save_image_record()
    #现在演示插入新记录到t_image_record
    oImgRecordContext = image_record_context()
    oImgRecordContext.take_photo_id = oTakePhotoContext.take_photo_id #拍照编号
    oImgRecordContext.image_path = "/test/data" #图片地址
    oImgRecordContext.photo_begin_time = time.time() #拍照开始时间
    oImgRecordContext.photo_end_time = oImgRecordContext.photo_begin_time + 10 #拍照结束时间
    oImgRecordContext.call_ai_begin_time = oImgRecordContext.photo_begin_time + 1 #调用AI开始时间
    oImgRecordContext.call_ai_end_time = oImgRecordContext.photo_begin_time + 3 #调用AI结束时间

    if not oSaveImageRec.execute(oImgRecordContext):
        print("插入t_image_record失败")
        return
    #end if
    print("插入t_image_record成功，记录ID为：%s" % oImgRecordContext.image_id)
    #现在演示更新刚才插入的记录
    oImgRecordContext.image_path = "/test/data22" #图片地址
    oImgRecordContext.state = 0 #状态[0:无效;1:有效]

    if not oSaveImageRec.execute(oImgRecordContext):
        print("更新t_image_record失败")
        return
    #end if
    print("更新t_image_record成功")

    #构造存储t_point_record操作，这个对象可以反复使用，非线程安全
    oSavePointRec = save_point_record()
    #现在演示插入新记录到t_point_record
    for i in range(6):
        oPointRecordContext[i] = point_record_context()
        oPointRecordContext[i].take_photo_id = oTakePhotoContext.take_photo_id #拍照编号
        oPointRecordContext[i].image_id = oImgRecordContext.image_id #图片编号
        oPointRecordContext[i].speed = 3 #传送带速度
        oPointRecordContext[i].type = 1  # 分类
        oPointRecordContext[i].threshold = 2  # 阈值
        oPointRecordContext[i].level = 3  # 等级
        oPointRecordContext[i].point_xmax = 1 #点的最大x坐标
        oPointRecordContext[i].point_ymax = 2 #点的最大y坐标
        oPointRecordContext[i].point_xmin = 3 #点的最小x坐标
        oPointRecordContext[i].point_ymin = 4 #点的最小y坐标
        oPointRecordContext[i].point_xcenter = 5 #点的中心x坐标
        oPointRecordContext[i].point_ycenter = 6 #点的中心y坐标
        oPointRecordContext[i].state = 1 #状态[1:新增;2;超出边缘;3:重复;4:成功抓取;5:来不及抓取]
        if not oSavePointRec.execute(oPointRecordContext[i]):
            print("插入t_point_record失败")
            return
        #end if
        print("插入t_point_record成功，记录ID为：%s" % oPointRecordContext[i].point_id)
        #现在演示更新刚才插入的记录
        oPointRecordContext[i].speed = 5 #传送带速度
        oPointRecordContext[i].state = 2 #状态[1:新增;2;超出边缘;3:重复;4:成功抓取;5:来不及抓取]
        oPointRecordContext[i].is_del = 0 #是否删除[0:是;1:否]
        if not oSavePointRec.execute(oPointRecordContext[i]):
            print("更新t_point_record失败")
            return
        #end if
        print("更新t_point_record成功")

    #最后，工程退出的时候，要停止定时任务线程
    oTaskThread.join()

    #以下可写可不写
    del oSaveTakePhoto
    del oTaskThread
#end def

if __name__ == '__main__':
    # test_main()
    # list1 = ["asadaf","ewqdqdq"]
    # write_mysql4(list1)
    time_now_1 = time.time()
    run_list = [1,2,3,4,5,6]

    list_1 = [1, 2, 251.542, 2000, 2000, 1000, 1000, 542, 234, 5, "zangmian", 0.75, 1]
    list_2 = [12, time.time(), "grab_error"]
    list_4 = ["dsswe1323", "sdf2#ff"]
    list_5 = [list_4[0] + "_" + list_4[1], time_now_1, 1,  time_now_1 + 0.5, time_now_1 + 0.6, time_now_1 + 1]
    list_6 = [3423, "/mnt/data/data/image/nobox/2021_0331/", time_now_1, 1, time_now_1 + 0.5, time_now_1 + 0.6, time_now_1 + 1]

    if 1 in run_list: #点位表
        # list_1 = [1,2,251.542,2000,2000,1000,1000,542,234,5,"zangmian",0.75,1]
        write_mysql(list_1)
    if 2 in run_list: #错误表
        # list_2 = [12,time.time(),"grab_error"]
        write_mysql2(list_2)
    if 3 in run_list: #供应商表
    #录入供应商，只录入一次
        write_mysql3()
    if 4 in run_list: #大小批次表
        # list_4 = ["dsswe1323","sdf2#ff"]
        write_mysql4(list_4)

    if 5 in run_list: #录入-拍照表
        # list_5 = [list_4[0]+"_"+list_4[1],time_now_1,time_now_1 + 0.5,time_now_1+0.6,time_now_1+1,1]
        id5 = write_mysql5(list_5)
        print("拍照表：{}".format(id5))
    if 6 in run_list: #录入-图片表
        # list_6 = [3423,"/mnt/data/data/image/nobox/2021_0331/",time_now_1,time_now_1 + 0.5,1]
        id6 = write_mysql6(list_6)
        print("图片表：{}".format(id6))
#end if
