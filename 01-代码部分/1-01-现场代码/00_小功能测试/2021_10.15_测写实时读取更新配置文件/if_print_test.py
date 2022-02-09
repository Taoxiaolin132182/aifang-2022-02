import time
import os










bool_ctrl1 = True   #  True False


'''控制print 是否打印 函数'''
def ctrl_print(mess,bool_show=True):
    if bool_show:
        print(mess)
    else:
        print("don't show message")



def test_print():
    str = "sda 32213"
    ctrl_print(str, bool_ctrl1)

    list_12 = [13, 424, "24242"]
    ctrl_print(list_12, bool_ctrl1)

    str_ne = "ddse: sdsd{}".format(list_12)
    ctrl_print(str_ne, bool_ctrl1)


def test_path_comb1():
    path1 = "/mnt/data/"
    path2 = "conf_backup"
    path3 = "err_conf/"
    name_path1 = os.path.join(path1, path2, path3)
    print(name_path1)

def test_deal_path():
    main_path1 = "/opt/app/ai-product-haijiang/ai-hj-service/aiHjService"  # 主路径
    main_path1 = deal_path(main_path1)
    print("main_path1:{}".format(main_path1))

def deal_path(path_d1):
    try:
        if path_d1[-1] == "/" and isinstance(path_d1, list):
            path_d1 = path_d1[:-1]
        return path_d1
    except Exception as e:
        print(f"deal_path  err: {e}")
        return path_d1

def test_use_one_line():
    num1 = 21
    if num1 > 10:
        print("现在的数字是：{}  大于10".format(num1))
        time.sleep(0.5)
        print("sign-1")
        time.sleep(0.5)
        print("sign-2")
    else:
        print("现在的数字是：{}  小于等于10".format(num1)); time.sleep(0.5); print("sign-3")
        time.sleep(0.5); print("sign-4")

    print("\n")
    print("ok") if num1 > 10 else print("ng")


def create_2dimension_list():
    cols = 3; rows = 2  #2行3列
    # show_num = (i + 1) + j * cols  # 元素递增
    list1 = [[(i + 1) + j * cols for i in range(cols)] for j in range(rows)]  # 外层为行，里层为列
    print(list1)

    print([x*y for x in range(1,4) for y in [1,3,5]])  # 越靠左，相当于越在上层
    # 结果：[1, 3, 5, 2, 6, 10, 3, 9, 15]


def os_path_test():
    str1 = "/mnt/data/data/"
    str2 = "aimodel/"
    res1 = os.path.join(str1, str2)
    print("res1结果是：{}".format(res1))

    str3 = "/mnt/data/data/aimodel/"
    str4 = ""
    res2 = os.path.join(str3, str4)
    print("res2结果是：{}".format(res2))


def test_if():
    bool_record1 = 0; bool_add_nobox = 4
    bool_record1 = 1 if (bool_add_nobox % 3 == 1) else 0
    print(bool_record1)

    dict_1 = {
        "a": 1, "b": 2, "c": 3, "d": 4,
    }
    print(len(dict_1))


def test_dict_get():
    try:
        dict1 = {
            "a": 1, "b": 2, "c": 3, "d": 4,
        }
        # print("1:---{}".format(dict1["f"]))
        # print("2:---{}".format(dict1['a']))
        print("3:---{}".format(dict1.get("f")))
        # print("4:---{}".format(dict1.get('a')))

    except Exception as e:
        print(f"err --test_dict_get : {e}")

'''录入点计数信息'''
def write_record_num_label():  # 录入点计数信息
    label_path = ["level-1", "level-2", "level-3", "level-4", "level-5"]  # 上传规则-等级-2021.08.09
    list_num_label = [[0, 0, 0, 0, 0], [500, 500, 500, 500, 500]]  # 上传规则-数量-2021.08.09
    for i in range(400):
        try:
            for j in range(len(list_num_label[0])):
                list_num_label[0][j] = i
            point_message3 = ""  # 清空信息
            for i_lab in range(len(label_path)):
                point_message3 += label_path[i_lab] + "," + str(list_num_label[0][i_lab]) + ","
            txt_name1 = "/mnt/data/data/upload_image/point_record_message.txt"
            print("更新-上传图片 点信息记录次数-txt文件")
            with open(txt_name1, 'w') as tf_2:
                tf_2.write(point_message3)
        except Exception as e:
            print(f"err --write_record_num_label : {e}")
        time.sleep(5)


def test_and_judge():
    # bool1 = True
    # list_j = [True, True, False, True, False]
    # for i_b in list_j:
    #     bool1 = bool1 and i_b
    #     print(bool1)
    #
    # bool_res = True if isinstance(bool1, list) else False
    # print("bool_res:{}".format(bool_res))
    list_a = [1,2,3,4]
    for num in list_a:
        choose_point1(num)

def choose_point1(numAB):
    claw_section = False  # True | False
    rePP1 = None; list_claw = []  # 初始置为 None
    if claw_section:
        '''分段 抓取模式  1:[0], 2:[1], 3:[2,0], 4:[3,1], '''
        list_claw = [numAB - 1] if numAB <= 2 else [numAB - 1, numAB - 3]
    else:
        '''常规 抓取模式  1:[0], 2:[1,0], 3:[2,1,0], 4:[2,1,0], '''
        list_claw = [0] if numAB <= 1 else [1, 0] if numAB <= 2 else [2, 1, 0]
    print(list_claw)

def choose_point2():
    list_ch = [20, 100]
    test_num = [0, 2, 30, 322]
    for num in test_num:
        res = 1 if num < list_ch[0] else (2 if num < list_ch[1] else 3)
        print(res)

def print_str_cut1():
    path1 = "/mnt/data/data/aimodel/20211105_yangrong_model/wool_jetpack44_v1_0_trt_config.json"
    name_aifile = path1.split("/")[-2]
    print("加载的模型文件为：{}".format(name_aifile))
    print("原来的路径为：{}".format(path1))


def test_get_list1():
    claw_section = False  # True：抓手分段  || False：抓手一致
    num_claw_state = 4
    list_claw_state = [0, 1, 0, 1, 0, 1, 0, 0,]
    Claw_ch_q = [[[0], [0, 1], [0, 1, 2], [0, 1, 2]],
                 [[0], [1], [0, 2], [1, 3]]]
    zhua_a = 0
    for ic in range(num_claw_state):
        claw_sta1 = sum(list_claw_state[2*ic: 2*ic + 2])
        tidui_l = Claw_ch_q[1][ic] if claw_section else Claw_ch_q[0][ic]
        print("抓手状态：{}， 梯队选取：{}".format(claw_sta1, tidui_l))
        if claw_sta1 == 0:
            zhua_a = ic + 1
            break
    print("@@@@@@@---{}".format(zhua_a))


def test_cut_list1():
    lista1 = [1,2,3,4,5,6,7,8]
    print("截取列表：{}".format(lista1[0:2]))


def list_test_8():
    listt1 = [None] * 4
    print(listt1)
    listt1[0] = 2344
    listt1[1] = "sd23"
    print(listt1)

def path_jion_test():
    path1 = "/mnt/data/data/image/havebox/"
    path2 = "_2012_34342_inter"
    path3 = "_W"
    path_all = os.path.join(path1, path2 + path3)
    print(path_all)


def test_name1():
    result_takepic_sort = []
    deal_light_record1 = 1
    result_takepic = ["cam_c88_2325.jpg", "cam_a88_2325.jpg", "cam_b88_2325.jpg"]
    Camera_id = [["a88", "A", "1"],
             ["b88", "C", "2"],
             ["c88", "B", "3"]]  # 仁杰羊毛-ARM1 对应相机号
    if len(result_takepic) == len(Camera_id):
        # bool_take_pic = False
        for list_cam in Camera_id:
            for name_pic in result_takepic:
                if list_cam[0] in name_pic:
                    if deal_light_record1 >= 10:  # 标记位：大于等于10：为非白光时段
                        name_pic = "UV_" + name_pic
                    result_takepic_sort.append(name_pic)  # 按配置文件中的相机号排序
                    continue
    print(result_takepic_sort)


def test_none():
    sign1 = "sdsa"
    if sign1 is not None:
        print("a")
    else:
        print("b")
    return sign1

def rec_str():
    test_none()
    print("完成")

def jisuan1():
    res = 1 // 2
    print(res)

    lis1 = [0,1,2,3,4,5]
    print(lis1[1:])

def test_if_1():
    dsa_list = [0, 0, 0]
    num1 = 3
    # if num1 > 5:
    #     dsa_list[0] += 1
    # else:
    #     dsa_list[1] += 1
    ipn = 0 if num1 > 5 else 1
    dsa_list[ipn] += 1
    print("结果：{}".format(dsa_list))

def test_list1():
    pic_queue1 = [[False, False, []], []]
    pic_queue1[0][0] = True
    print("1:{}".format(pic_queue1))
    if pic_queue1[0][0]:
        pic_queue1[0][:2] = [False, True]
    print("2:{}".format(pic_queue1))

if __name__ == "__main__":
    test_list1()
    # test_print()
    # test_path_comb1()
    # test_deal_path()
    # test_use_one_line()
    # create_2dimension_list()
    # os_path_test()
    # test_if()
    # write_record_num_label()
    # test_dict_get()
    # test_and_judge()
    # choose_point2()
    # print_str_cut1()
    # test_get_list1()
    # test_cut_list1()
    # test_name1()
    # rec_str()
    # jisuan1()