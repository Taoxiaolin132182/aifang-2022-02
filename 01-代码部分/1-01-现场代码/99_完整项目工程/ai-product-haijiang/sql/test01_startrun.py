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
    try:
        t1 = time.time()
        print(1)
        os.system('cd /mnt/data/data/1test_write/')
        print(2)
        os.system('chmod -R 777 /mnt/data/data/1test_write/a_test_wool_yolov3.des3 &')
        print(3)
        '''加密解压'''
        os.system(
            "dd if=/mnt/data/data/1test_write/34_test.des3|openssl des3 -d -pbkdf2 -k 'W!e@l&c#^$o%m*e'|tar zxf - > /mnt/data/data/1test_write/load1.log 2>&1")
        print(4)
        os.system('chmod -R 777 wool_yolov3.pb &')
        print(5)
        os.system('mv wool_yolov3.pb /mnt/data/data/1test_write/')
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


def test3():#新刷arm后，简化调试部署流程的代码
    try:
        t1 = time.time()
        print(1)
        os.system('cd /mnt/data/')
        # if True:
        if not os.path.exists("/mnt/data/data/"):
            os.makedirs("/mnt/data/data/")
        if not os.path.exists("/mnt/data/data/image/"):
            os.makedirs("/mnt/data/data/image/")
        if not os.path.exists("/mnt/data/data/image/havebox/"):
            os.makedirs("/mnt/data/data/image/havebox/")
        if not os.path.exists("/mnt/data/data/image/nobox/"):
            os.makedirs("/mnt/data/data/image/nobox/")
        if not os.path.exists("/mnt/data/data/image_original/"):
            os.makedirs("/mnt/data/data/image_original/")
        if not os.path.exists("/mnt/data/data/upload_image/"):
            os.makedirs("/mnt/data/data/upload_image/")
        if not os.path.exists("/mnt/data/data/aimodel/"):
            os.makedirs("/mnt/data/data/aimodel/")
        if not os.path.exists("/mnt/data/data/log_txl/"):
            os.makedirs("/mnt/data/data/log_txl/")
        if not os.path.exists("/mnt/data/data/2test_remove/"):
            os.makedirs("/mnt/data/data/2test_remove/")
        os.system('chmod -R 777 /mnt/data/data/ &')
        # if True:
        if not os.path.exists("/mnt/data/opt/"):
            os.makedirs("/mnt/data/opt/")
        if not os.path.exists("/mnt/data/opt/logs/"):
            os.makedirs("/mnt/data/opt/logs/")
        if not os.path.exists("/mnt/data/opt/logs/ai-product-haijiang/"):
            os.makedirs("/mnt/data/opt/logs/ai-product-haijiang/")
        if not os.path.exists("/mnt/data/opt/logs/ai-product-haijiang/ai-cotton-api-server-release"):
            os.makedirs("/mnt/data/opt/logs/ai-product-haijiang/ai-cotton-api-server-release")
        if not os.path.exists("/mnt/data/opt/logs/txl01/"):
            os.makedirs("/mnt/data/opt/logs/txl01/")
        if not os.path.exists("/mnt/data/opt/logs/ai-auto-upload-data/"):
            os.makedirs("/mnt/data/opt/logs/ai-auto-upload-data/")
        if not os.path.exists("/mnt/data/opt/logs/ai-auto-upload-data/ai-common-upload-db/"):
            os.makedirs("/mnt/data/opt/logs/ai-auto-upload-data/ai-common-upload-db/")
        if not os.path.exists("/mnt/data/opt/logs/ai-auto-upload-data/ai-common-upload-file/"):
            os.makedirs("/mnt/data/opt/logs/ai-auto-upload-data/ai-common-upload-file/")

        os.system('chmod -R 777 /mnt/data/opt/ &')

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
    test3()