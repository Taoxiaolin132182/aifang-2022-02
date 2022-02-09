import os, time

def use_decode_cmd():
    print("开始解压")
    t1 = time.time()
    str_cmd1 = "/mnt/data/data/2test_remove/try_decode/decode_model > /opt/logs/txl01/decode.log 2>&1 &"
    os.system(str_cmd1)
    print("结束解压，耗时：{}".format(round(time.time() - t1, 3)))


def main_func1():
    use_decode_cmd()


if __name__ == "__main__":
    main_func1()