# coding=utf-8
import json, os, time, copy



'''时间戳转换指定时间格式'''
def change_to_strtime(timestamp1):
    time_array1 = time.localtime(timestamp1)  # 格式化时间戳为本地的时间
    strtime1 = time.strftime("%Y-%m-%d %H:%M:%S", time_array1)
    # print("现在的格式时间:{}".format(strtime1))
    return strtime1

def get_file_time(f_path):
    name_time = ["修改", "创建", ]
    c_path1_time = []
    c_path1_time.append(os.path.getmtime(f_path))  # 文件修改时间
    # c_path1_time.append(os.path.getatime(f_path))  # 文件访问时间
    c_path1_time.append(os.path.getctime(f_path))  # 文件创建时间
    # for i in range(len(c_path1_time)):
    #     t_format = change_to_strtime(c_path1_time[i])
    #     print("{}时间：{}".format(name_time[i], t_format))

    return c_path1_time

def load_config(configPath):
    with open(configPath, encoding='utf-8-sig') as f:
        config = json.load(f)
    return config


def main_func_read():
    f_time1 = []
    bool_start_run = True
    path_cfg = "./arm_cfg.json"
    while bool_start_run:
        time.sleep(0.1)
        now_time = get_file_time(path_cfg)
        if f_time1 == now_time:
            print("从文件的时间属性上看，文件未更新，循环等待")
            time.sleep(5)
            continue
        else:
            f_time1 = copy.deepcopy(now_time)
        data_cfg = load_config(path_cfg)
        # print("返回的数据 类型：{}".format(type(data_cfg)))
        # print("返回的数据 内容：{}".format(data_cfg))
        for k1, v1 in data_cfg.items():
            print("键:{} 对应的值类型是:{},内容是:{}".format(k1, type(v1), v1))
        time.sleep(5)




if __name__ == "__main__":
    main_func_read()