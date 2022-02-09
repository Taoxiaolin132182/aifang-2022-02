# coding=utf-8
import os, time







def test1():
    str1 = '6.5G\t/mnt/data/data/image/\n'
    list1 = str1.split("G")
    print("分割后：{}".format(list1))
    print("这个路径中占用 {}G 磁盘空间".format(float(list1[0])))



def cmd_code1():
    max_space = [500, 200]
    path1 = ["/mnt/data/data/image/", "/mnt/data/data/upload_image/"]
    for i in range(len(path1)):
        cmd1 = "du -sh " + path1[i]
        pid1 = os.popen(cmd1)
        message1 = pid1.readlines()  # type: list
        print("message-({}):{}".format(i, message1))
        # ['65G\t/mnt/data/data/image/\n']
        if "G" in message1[0]:
            list1 = message1[0].split("G")
            print("{} 这个路径中占用 {}G 磁盘空间".format(path1[i], float(list1[0])))
            if float(list1[0]) > max_space[i]:
                print("占用空间过大，按需求删除文件夹")
                cmd_del = "rm -rf " + path1[i] + " &"
                os.system(cmd_del)
                time.sleep(5)
        elif "M" in message1[0]:
            list1 = message1[0].split("M")
            print("{} 这个路径中占用 {}M 磁盘空间".format(path1[i], int(list1[0])))


def run_func1():
    # cmd_code1()
    test1()
    pass


if __name__ == "__main__":
    run_func1()