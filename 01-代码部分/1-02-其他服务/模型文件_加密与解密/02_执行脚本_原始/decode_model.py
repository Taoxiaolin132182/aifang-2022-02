# coding=utf-8
import os
import time
import sys
bool_can_run = False

# 添加包路径
START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
# sys.path.append(os.path.join(START_PY_PATH, "..", ".."))
sys.path.append("/mnt/data/data/")
import aimodel.cfg_decode as cfg_dc

''' 对加密模型进行解密'''


def main_func():
    '''2021-0906  '''
    try:
        t1 = time.time()
        print("进行解密程序")
        path_need_file = cfg_dc.path_job + cfg_dc.path_model + cfg_dc.model_last_name[0]  # 被加密文件的路径
        path_new_file = cfg_dc.path_job + cfg_dc.path_model + cfg_dc.model_last_name[1]  # 原始文件的路径
        print("判断加密文件是否存在")
        if os.path.exists(path_need_file):
            code1 = 'chmod -R 777 ' + path_need_file + ' &'
            os.system(code1)  # 赋权限
            print("赋权限完成，准备加密解压")
            '''解密解压  --使用完整路径进行加密，tar + P'''
            code2 = "dd if=" + path_need_file +\
                    "|openssl des3 -d -pbkdf2 -k 'W!e@l&c#^$o%m*e'|tar zxPf - > /mnt/data/opt/logs/load1.log 2>&1"
            os.system(code2)
            print("解密解压完成")
            code3 = 'chmod 777 ' + path_new_file + ' &'
            os.system(code3)
            print("赋权限给新生成文件")
            # code4 = 'mv ' + cfg_dc.model_last_name[1] + ' ' + cfg_dc.path_job + cfg_dc.path_model
            # os.system(code4)
        else:
            print("没有模型加密文件：{}".format(path_need_file))
        if cfg_dc.model_count > 1:
            path_need_file2 = cfg_dc.path_job + cfg_dc.path_model_add + cfg_dc.model_last_name_add[0]
            path_new_file2 = cfg_dc.path_job + cfg_dc.path_model_add + cfg_dc.model_last_name_add[1]  # 原始文件的路径
            print("2--判断加密文件是否存在")
            if os.path.exists(path_need_file2):
                code21 = 'chmod -R 777 ' + path_need_file2 + ' &'
                os.system(code21)
                print("2---赋权限完成，准备加密解压")
                '''解密解压  --使用完整路径进行加密，tar + P'''
                code22 = "dd if=" + path_need_file2 + \
                        "|openssl des3 -d -pbkdf2 -k 'W!e@l&c#^$o%m*e'|tar zxPf - > /mnt/data/opt/logs/load2.log 2>&1"
                os.system(code22)
                print("2---解密解压完成")
                code23 = 'chmod 777 ' + path_new_file2 + ' &'
                os.system(code23)
                print("2---赋权限给新生成文件")
                # code24 = 'mv ' + cfg_dc.model_last_name_add[1] + ' ' + cfg_dc.path_job + cfg_dc.path_model_add
                # os.system(code24)
            else:
                print("2---没有模型加密文件：{}".format(path_need_file2))

        l_time = time.time() - t1
        print("all time:{}".format(l_time))

    except Exception as e:
        print("decode----error:{}".format(e))


def encryption():
    '''2021-0906  '''
    try:
        t1 = time.time()
        print("进行加密程序")
        path_real_model = cfg_dc.path_job + cfg_dc.path_model + cfg_dc.model_last_name[1]  # 原始文件路径
        path_well_model = cfg_dc.path_job + cfg_dc.path_model + cfg_dc.model_last_name[0]  # 加密后存放路径
        if os.path.exists(path_real_model):
            print("路径存在，准备加密")
            print("{}".format(path_real_model))
            # 使用完整路径进行加密，tar + P
            code1 = "tar -zcPf - " + path_real_model + \
                    "|openssl des3 -salt -pbkdf2 -k 'W!e@l&c#^$o%m*e'|dd of=" + path_well_model
            os.system(code1)
            print("赋权限")
            code3 = 'chmod 777 ' + path_well_model + ' &'
            os.system(code3)
            if cfg_dc.if_need_remove_old:
                code4 = 'rm -f ' + path_real_model + ' &'
                os.system(code4)
        if cfg_dc.model_count > 1:  # 判断是否需要加密第二个模型
            path_real_model2 = cfg_dc.path_job + cfg_dc.path_model_add + cfg_dc.model_last_name_add[1]
            path_well_model2 = cfg_dc.path_job + cfg_dc.path_model_add + cfg_dc.model_last_name_add[0]
            if os.path.exists(path_real_model2):
                print("路径存在，准备加密")
                print("{}".format(path_real_model2))
                # 使用完整路径进行加密，tar + P
                code21 = "tar -zcPf - " + path_real_model2 + \
                        "|openssl des3 -salt -pbkdf2 -k 'W!e@l&c#^$o%m*e'|dd of=" + path_well_model2
                os.system(code21)
                print("赋权限")
                code23 = 'chmod 777 ' + path_well_model2 + ' &'
                os.system(code23)
                if cfg_dc.if_need_remove_old:
                    code24 = 'rm -f ' + path_real_model2 + ' &'
                    os.system(code24)
        l_time = time.time() - t1
        print("all time:{}".format(l_time))
        print("加密完成--已放入对应路径")

    except Exception as e:
        print("encryption----error:{}".format(e))

if __name__ == "__main__":
    if os.path.exists("/mnt/data/data/aimodel/cfg_decode.py"):
        if cfg_dc.choose_code == 1:
            main_func()  # 解密
        elif cfg_dc.choose_code == 2:
            encryption()  # 加密
    else:
        print("配置文件的路径异常")

