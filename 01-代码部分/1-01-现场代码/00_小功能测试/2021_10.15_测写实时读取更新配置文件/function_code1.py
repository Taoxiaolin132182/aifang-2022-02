# coding=utf-8

import time
import os
import sys
import json
import copy
import threading
START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH))


def write_dict_to_txt1():
    pass

'''读取txt input:完整路径  output: 是否异常结果'''
def read_txt1(path_txt1):
    bool_read_ok = False
    try:
        if os.path.exists(path_txt1):
            print("\n==================\n开始读取txt信息\n")
            print("{} 此文件存在".format(path_txt1))
            # encoding=  gbk utf-8 ansi
            with open(path_txt1, "rb") as f_str:
                message1 = json.load(f_str)
                print("读取内容为：\n{}".format(message1))
                print("信息个数：{}".format(len(message1)))
                print("信息类型：{}".format(type(message1)))
                for km, vm in message1.items():
                    print("key:{}  对应的值 ：{}，值的类型为：{}".format(km, vm, type(vm)))
                    if isinstance(vm, list):
                        print("数据组数：{}".format(len(vm)))
                        for num_a in vm:
                            print("数据：{} 的类型为：{}".format(num_a, type(num_a)))
            print("读取txt配置文件，完成")
            bool_read_ok = True
        else:
            print("{} 该文件不存在".format(path_txt1))
    except Exception as e:
        print(f"read_txt1  err: {e}")
    return bool_read_ok



def test_use_cfg():
    for ie in range(1000):
        try:
            pass

        except Exception as e:
            print(f"test_use_cfg  err: {e}")
            time.sleep(5)

'''测试 字符 存在于 字符串中'''
def test_wq():
    str1 = "sfa  eqewafawe   dsaavLOVE QWDwe23edw 24qded 3qes"
    str1.replace()
    bool_judge1 = "LOVE" in str1
    print("bool_judge1:{}".format(bool_judge1))


'''获取当前文件的所在路径'''
def get_my_path():
    now_path = os.path.abspath(__file__)  # 包含文件本身名称
    now_path_up = os.path.dirname(now_path)
    print("\n当前脚本所在路径为：{}".format(now_path_up))
    return now_path_up

'''时间戳转换指定时间格式'''
def change_to_strtime(timestamp1):
    time_array1 = time.localtime(timestamp1)  # 格式化时间戳为本地的时间
    strtime1 = time.strftime("%Y_%m%d_%H%M%S", time_array1)
    # print("现在的格式时间:{}".format(strtime1))
    return strtime1





'''
1、研究txt更新引起的修改、访问、创建时间的变化
    直接替换时，修改、创建时间会变成替换时刻的时间
2、读取txt配置 的逻辑
    2.1、确认或创建 备份文件夹
    2.2、确认要用的文件存在，
            存在时，读取txt信息
                读取成功时，备份文件
                读取异常时，发起 恢复最新备份 信号
            不存在时，发起 恢复最新备份 信号
3、获取真实 备份配置文件数量
4、如果有 恢复最新备份 信号
    恢复最新备份，读取txt信息
        读取成功时，提示检测新文件
        读取异常时，结束进程
5、检查，删除多余的备份文件
'''
'''读取备份列表'''
def before_read_prepare1():
    config_file1 = "config_aifang.txt"  # 读取-需要备份的文件名
    max_backup = 5  # 备份文件上限数量
    main_path1 = "/opt/app/ai-product-haijiang/ai-hj-service/aiHjService/"  # 主路径
    config_backup1 = "backup_conf"  # 备份路径
    bool_read_backup = False  # 标准路径下，无配置文件，或读取文件错误时，读取备份文件
    # 确认或创建 备份文件夹
    if not os.path.exists(main_path1 + config_backup1):
        os.makedirs(main_path1 + config_backup1)
        chmod_code1 = "chmod -R 777 " + main_path1 + config_backup1 + " &"
        os.system(chmod_code1)
    # 确认要用的文件存在
    if os.path.exists(main_path1 + config_file1):
        # try-  读取文件 ，正常时备份，异常时读取备份
        bool_res1 = read_txt1(main_path1 + config_file1)  # 读取txt 信息
        if bool_res1:
            # 先做备份
            str_now_time = change_to_strtime(time.time())  # 此刻的时间格式
            rename_txt_file = "backup_" + str_now_time + "_" + config_file1  # 备份命名
            print("备份配置文件，文件重命名为：{}".format(rename_txt_file))
            cmd_str1 = "cp " + main_path1 + config_file1 + " " + main_path1 + config_backup1 \
                       + "/" + rename_txt_file + " &"
            os.system(cmd_str1)  # 复制到 备份路径 下
            chmod_code3 = "chmod -R 777 " + main_path1 + config_backup1 + "/" + rename_txt_file + " &"
            os.system(chmod_code3)
        else:
            print("读取txt信息 异常")
            bool_read_backup = True
    else:
        print("标准路径下，无所需配置txt文件，请检查")
        bool_read_backup = True
        pass

    real_backup_list = []  # 符合标准的备份文件
    list_file = os.listdir(main_path1 + config_backup1)  # 读取路径下的文件列表
    print("共有{}个文件".format(len(list_file)))
    for name_file in list_file:
        if ("config_aifang" in name_file) and (".txt" in name_file):
            real_backup_list.append(name_file)  # 符合标准的备份文件
    print("共有{}个真实备份 配置文件".format(len(real_backup_list)))
    # print("排序前的list of name:\n{}".format(real_backup_list))
    # @@读取备份文件
    if bool_read_backup:  # 需要 读取备份文件时
        # bool_read_backup = False
        if len(real_backup_list) > 0:  # 当存在备份文件时
            real_backup_list.sort()
            print("排序后的list of name:\n{}".format(real_backup_list))
            backup_name = real_backup_list[-1]  # 最新的备份文件名
            print("把备份文件:{} 还原".format(backup_name))
            cmd_str2 = "cp " + main_path1 + config_backup1 + "/" + backup_name + " " + \
                       main_path1 + config_file1 + " &"
            os.system(cmd_str2)  # 复制到 备份路径 下
            chmod_code2 = "chmod -R 777 " + main_path1 + config_file1 + " &"
            os.system(chmod_code2)
            time.sleep(1)  # 等待 备份恢复动作 执行完成
            bool_res2 = read_txt1(main_path1 + config_file1)  # 读取txt 信息
            if bool_res2:
                print("由于新的txt配置文件异常，恢复读取了{}, 请注意检测更新".format(backup_name))
            else:
                print("恢复的备份文件，读取到的信息异常，退出程序")
                time.sleep(2)
                os._exit(0)
        else:
            print("备份路径下，无备份文件")
            time.sleep(2)
            os._exit(0)
            # 这边要有返回 return
    # @@删除多余的备份文件
    now_file_num = len(real_backup_list) - max_backup  # 多余数量
    if now_file_num > 0:
        print("备份文件数量超限,需要删除{}个".format(now_file_num))
        real_backup_list.sort()  # 排序--升序
        # print("排序后的list of name:\n{}".format(real_backup_list))
        for itr in range(now_file_num):
            path_need_remove1 = main_path1 + config_backup1 + "/" + real_backup_list[itr]
            print("第{}个，要删除的文件：{}".format(itr + 1, real_backup_list[itr]))
            os.remove(path_need_remove1)




'''主调用函数'''
def main_func1():
    before_read_prepare1()
    # get_my_path()
    # read_txt1()
    # th1 = threading.Thread(target=test_use_cfg, args=(), name="test_use_cfg")
    # th1.start()
    # test_wq()

if __name__ == "__main__":
    main_func1()