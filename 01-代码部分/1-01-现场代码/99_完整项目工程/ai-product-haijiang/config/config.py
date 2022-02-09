import os
import sys
import configparser
#-------------------------------------------------------------------------------------------------
#！！参数在此配置！！

#是否本机调试
DEBUG_MODE = False

if DEBUG_MODE:
    from . import config_dev as user_config
else:
    from . import config_prod as user_config
#end if

#APP名
APP_NAME = "ai-product-haijiang"
#日志位置
LOG_PATH = os.path.join("/", "opt", "logs", APP_NAME)
#日志保留天数
LOG_DAYS = 0.5 if DEBUG_MODE else 7
#是否日志中打印每个filter耗时
LOG_FILTER_TIME = False

#图片保存位置
DISK_SAVE_PATH = os.path.join("/", "opt", "data", APP_NAME)
#保存图片质量0-100
IMAGE_QUALITY = 96
#保存图片格式
IMAGE_FORMAT = ".jpg"

#默认初始处理队列大小
INIT_AUTO_QUEUE_SIZE = 100

'''
当DISK_SAVE_PATH所在磁盘剩余空间百分比不足DISK_FREE_LIMIT1时，
删除DISK_SAVE_PATH目录中最早的文件，确保有DISK_FREE_LIMIT2的剩余空间
'''
DISK_FREE_LIMIT1 = 20
DISK_FREE_LIMIT2 = 40

'''
当记录数到达LIMIT_DB_RECORD_NUM_1时，删除到LIMIT_DB_RECORD_NUM_2的范围内
'''
LIMIT_DB_RECORD_NUM_1 = 1200 if DEBUG_MODE else 280 * 10000
LIMIT_DB_RECORD_NUM_2 = 1000 if DEBUG_MODE else 250 * 10000

#Db存储数据库
DB_CONFIG = user_config.DB_CONFIG
#需要检查并删除过时记录的表配置
CHECK_DB_CONFIG = {
                    "tables" : ("t_image_record", "t_point_record", "t_take_photo_record"),
                    "keys" : ("image_id", "point_id", "take_photo_id")
                  }

#配置项里的mac id
SAVE_MAC_ID = ""

#-------------------------------------------------------------------------------------------------

if __name__ != '__main__':
    try:
        os.makedirs(LOG_PATH)
    except Exception as e:
        pass
    #end if

    #上传要求图片目录加上配置文件里的mac
    try:
        conf = configparser.ConfigParser()
        conf.read(os.path.join("/", "opt", "config", "mac_addr.conf"))
        SAVE_MAC_ID = str(conf.get("common", "mac"))
        del conf
        # SAVE_MAC_ID = str("48b02d18548c")
        DISK_SAVE_PATH = os.path.join(DISK_SAVE_PATH, SAVE_MAC_ID)
    except Exception as e3:
        print("get mac config failed: %s" % e3)
    #end if

    try:
        os.makedirs(DISK_SAVE_PATH)
    except Exception as e2:
        pass
    #end if

#end if

