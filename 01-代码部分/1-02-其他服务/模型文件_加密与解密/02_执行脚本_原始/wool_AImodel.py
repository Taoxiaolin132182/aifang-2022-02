import os
import time

def test1():
    try:
        print(1)
        path_time_Hm1 = time.strftime("%Y_%m_%d__%H_%M", time.localtime())
        str_write1 = 'touch test_' + path_time_Hm1 + '.txt &'
        os.system('cd /mnt/data/data/1test_write/')
        print(2)
        os.system('touch test001.txt &')
        print(3)
        os.system(str_write1)
    except Exception as e:
        print("error:{}".format(e))

def test2():
    '''2021-07-27  加密解压张家港羊毛模型--分AB两个模型，测试解压2个模型，需要时间33秒'''
    try:
        t1 = time.time()
        print(1)
        os.system('cd /mnt/data/data/aimodel/')  # 进入加密模型所在路径
        print(2)
        os.system('chmod -R 777 /mnt/data/data/aimodel/tianyu_AI_model_A.des3 &')  # 对加密模型 赋予权限
        time.sleep(0.5)
        os.system('chmod -R 777 /mnt/data/data/aimodel/tianyu_AI_model_B.des3 &')  # 对加密模型 赋予权限
        print(3)
        '''加密解压'''
        os.system(
            "dd if=/mnt/data/data/aimodel/tianyu_AI_model_A.des3|openssl des3 -d -pbkdf2 -k 'W!e@l&c#^$o%m*e'|tar zxf - > /mnt/data/opt/logs/load1.log 2>&1")
        print(4)
        os.system('chmod -R 777 Awool_yolov3.pb &')
        # print(5)
        # os.system('mv Awool_yolov3.pb /mnt/data/data/aimodel/')
        #
        # '''加密解压'''
        # os.system(
        #     "dd if=/mnt/data/data/aimodel/tianyu_AI_model_B.des3|openssl des3 -d -pbkdf2 -k 'W!e@l&c#^$o%m*e'|tar zxf - > /mnt/data/opt/logs/load2.log 2>&1")
        # print(4)
        # os.system('chmod -R 777 Bwool_yolov3.pb &')
        # print(5)
        # os.system('mv Bwool_yolov3.pb /mnt/data/data/aimodel/')
        '''删除文件'''
        # os.system('rm -rf wool_yolov3.pb &')
        l_time = time.time() - t1
        print("all time:{}".format(l_time))
        '''加密压缩'''
        # os.system('tar -zcf - wool_yolov3.pb|openssl des3 -salt -pbkdf2 -k 'W!e@l&c#^$o%m*e'|dd of=34_test.des3 > /mnt/data/data/1test_write/save.log 2>&1')
        # # print(3)
        # os.system('chmod -R 777 b_test_wool_yolov3.des3 &')

    except Exception as e:
        print("error:{}".format(e))



if __name__ == "__main__":
    # test1()
    test2()