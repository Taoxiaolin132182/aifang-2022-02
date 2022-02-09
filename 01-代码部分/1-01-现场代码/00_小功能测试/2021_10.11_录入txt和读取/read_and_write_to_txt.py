import time
import os
import copy
'''测试 将time.time() 写入 txt文件，能不能读取出来'''
list_to_txt = [
    "临时-运行开始时间戳", "总-运行开始时间戳", "已计时次数",
    "临时-停顿开始时间戳", "临时-停顿时长",
    "现有个数(1)", "现有个数(2)", "现有个数(3)", "现有个数(4)", "现有个数(5)",
    "标记位(1)", "标记位(2)", "下次将剩余异纤数量",
]

def create_or_read_circulation_record():
    # 创建或录入--点分类记录
    # 格式：
    t_test1 = time.time()
    list_to_txt_a = [t_test1 + 10, None, None, 653.32, 8, 200, 300, 400, 500, 600, 1, 1, 432]
    txt_name1 = r"C:\copy_read_pic\duqu_pic\dtxt_read\circulation_record_message.txt"
    # txt_name1 = r"/mnt/data/data/circulation_record_message.txt"
    bool_name_file = os.path.isfile(txt_name1)
    if not bool_name_file:  # 不存在时，创建txt,并写入000
        tf_1 = open(txt_name1, 'w')
        # t_now1 = time.time()
        # point_message3 = str(t_now1)

        point_message3 = ""
        for i_label in range(len(list_to_txt_a)):
            point_message3 += str(list_to_txt_a[i_label]) + ","
        print("point_message3:{}".format(point_message3))
        tf_1.write(point_message3)
        # tf_1.write("\n")
        # tf_1.write("\n")
        tf_1.close()
        print("创建新-点信息记录次数-txt文件,并写入 0 值")
    else:  # 文件已存在，说明已经有计数累加记录
        now_a = 11
        if now_a == 1:
            for i in range(3):
                time.sleep(2)
                write_record_num_label(list_to_txt_a)
        else:
            tf_2 = open(txt_name1, 'r')
            context1 = tf_2.readlines()
            print("txt列表：{}".format(context1))
            print("列表长度：{}".format(len(context1)))
            if len(context1) == 0:
                print("文件已存在,但上次写入异常，无字符")
                # for i_label in range(len(self.label_path)):
                #     self.list_num_label[0][i_label] = 0  # 取到文件中的次数数据，赋值到列表
                #     print("已有-点信息记录次数：{}--{}".format(self.label_path[i_label], self.list_num_label[0][i_label]))
            else:
                list_from_txt_a = []
                context2 = context1[0]
                txt1 = context2.replace(" ", "").replace("\n", "")
                print("txt1:{}".format(txt1))

                txt2 = txt1.split(",")  # 点信息
                print("读取字符列表个数{}：{}".format(len(txt2), txt2))
                for it in range(len(list_to_txt_a)):
                    if it < 3:
                        if txt2[it] == "None":
                            data1 = None
                        else:
                            data1 = time.mktime(time.localtime(float(txt2[it])))   # 转化时间字符串
                        print("data1(0-2):{}".format(data1))
                    elif it < 4:
                        data2 = float(txt2[it])  # 转化 浮点数字符串
                        print("data2(3):{}".format(data2))
                    else:
                        data3 = int(txt2[it])
                        print("data3(4---):{}".format(data3))


def write_record_num_label(namea):  # 录入点计数信息
    txt_name1 = r"C:\copy_read_pic\duqu_pic\dtxt_read\circulation_record_message.txt"
    # txt_name1 = r"/mnt/data/data/circulation_record_message.txt"
    bool_name_file = os.path.isfile(txt_name1)
    if bool_name_file:
        print("更新-点信息记录次数-txt文件")
        tf_2 = open(txt_name1, 'w')
        point_message3 = ""
        for i_label in range(len(namea)):
            point_message3 += str(namea[i_label]) + ","
        tf_2.write(point_message3)
        # tf_2.write("\n")
        tf_2.close()

def test1():
    lda = None
    print("lda: {}".format(lda))
    print("type of lda: {}".format(type(lda)))
    print("str of lda: {}".format(str(lda)))

def test2():
    num_a = 23
    print("1--num_a:{}".format(num_a))
    res_a = 0
    print("1--res_a:{}".format(res_a))
    res_a += copy.deepcopy(num_a)
    print("2--res_a:{}".format(res_a))
    num_a = 43
    print("3--num_a:{}".format(num_a))
    print("3--res_a:{}".format(res_a))


def main_func1():
    test2()
    # create_or_read_circulation_record()

if __name__ == "__main__":
    main_func1()