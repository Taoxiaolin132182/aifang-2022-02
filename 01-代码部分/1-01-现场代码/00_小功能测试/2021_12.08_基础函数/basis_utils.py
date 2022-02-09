# coding=utf-8
import os, time, copy, json


'''(001)读取 json文件 '''
def load_config(configPath):
    with open(configPath, encoding='utf-8-sig') as f:
        config = json.load(f)
    return config

'''(002)时间戳转换指定时间格式'''
def change_to_strtime(timestamp1):
    time_array1 = time.localtime(timestamp1)  # 格式化时间戳为本地的时间
    strtime1 = time.strftime("%Y-%m-%d %H:%M:%S", time_array1)
    # print("现在的格式时间:{}".format(strtime1))
    return strtime1

'''(003)时间格式转换时间戳'''
def change_to_timestamp(str_time):
    timearray2 = time.strptime(str_time, "%Y/%m/%d.%H:%M:%S")  # 输入 和 转换 需要匹配的格式
    time_stamp2 = time.mktime(timearray2)
    # print("时间戳：{}".format(time_stamp2))
    return time_stamp2

'''(待验证)检测路径存不存在，不存在创建'''
def check_path(path):
    bool_exist = False
    if os.path.exists(path):
        bool_exist = True
    else:
        os.makedirs(path)








if __name__ == "__main__":
    pass