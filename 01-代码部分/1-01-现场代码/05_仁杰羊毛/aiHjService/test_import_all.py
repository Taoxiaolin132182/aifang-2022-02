# coding=utf-8
import logging.config
import os
import cfg1_need.config_armz as ai_cfg

logger7 = logging.getLogger('needrecoed')


def test1():
    test_str1 = ai_cfg.Path_upload
    print(test_str1)



if __name__ == '__main__':
    logging.config.fileConfig('./share_func/log.conf')
    init_flag = "init.txt"
    if os.path.exists(init_flag):  # 与守护进程形成 呼应
        os.remove(init_flag)
    # 设置信号处理
    run_or_test1 = 1  # 1：正常运行，非1：测试
    if run_or_test1 == 1:
        try:
            f = open(init_flag, "w+")  # 与守护进程形成 呼应
            f.write("success")
            f.close()
            # for i in range(100):
            #     print("写入log-OK:{}".format(i))
            #     logger7.info("写入log-OK:{}".format(i))
            test1()
        except:
            logger7.error("write init status error =======")
