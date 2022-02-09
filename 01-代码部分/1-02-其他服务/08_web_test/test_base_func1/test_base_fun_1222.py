import os, json



def test_int_fushu():
    num = "1.3232"
    res_n = int(num)
    print("res_n:{}".format(res_n))

def test_round():
    num = "-11.3232"
    res_n = round(float(num), 3)
    print("res_n:{}".format(res_n))
    if (res_n > -5) and (res_n < 5):
        print("ok ")

'''读取txt input:完整路径  output: 是否异常结果'''
def read_txt1(path_txt1):
    bool_read_ok = False  # 读取是否异常
    try:
        if os.path.exists(path_txt1):
            print("\n==================\n开始读取txt信息\n")
            print("{} 此文件存在".format(path_txt1))
            # encoding=  gbk utf-8 ansi
            with open(path_txt1, "rb") as f_str:
                message1 = json.load(f_str)
                # print("读取内容为：\n{}".format(message1))
                print("信息个数：{}".format(len(message1)))
                print("信息类型：{}".format(type(message1)))

            print("读取txt配置文件，完成")
            bool_read_ok = True
        else:
            print("{} 该文件不存在".format(path_txt1))
    except Exception as e:
        print(f"read_txt1  err: {e}")
    return bool_read_ok, message1


def write_change_mes(path_w, data1):
    w_data1 = {"claw1": {}, "claw2": {}, "claw3": {}, "claw4": {}}
    w_data1["claw1"] = data1
    for kc, vc in w_data1.items():
        if len(vc) > 0:
            for k1, v1 in vc.items():
                if "t" in k1:
                    w_data1[kc][k1] = round(v1, 3)
                else:
                    w_data1[kc][k1] = int(v1)
    with open(path_w, "w") as f_dict:
        f_dict.write(json.dumps(w_data1))  # 开始存信息，写入txt文件

'''控制print 是否打印 函数'''
def ctrl_print(mess,bool_show=False):  # bool_show = True(显示)， = False(不显示)
    if bool_show:
        print(mess)

'''获取当前文件的所在路径'''
def get_my_path():
    now_path = os.path.abspath(__file__)  # 包含文件本身名称
    print("\n当前脚本所在完整路径为：{}".format(now_path))
    now_path_up = os.path.dirname(now_path)
    print("\n当前脚本所在路径为：{}".format(now_path_up))
    return now_path_up


def test_append_list1():
    config_choose_for_arm = 2
    index_mes1 = [
        "<a href='/index/'>   首页   </a>",
        "<a href='/show12/'>  2抓手配置  </a>",
        "<a href='/show14/'>  4抓手配置  </a>",
        "<a href='https://www.baidu.com/'>   百度   </a>",
        str(config_choose_for_arm)
    ]
    add_mes1 = "<a href='/instructions/'> 补偿参数说明 </a>"
    index_mes1.append(add_mes1)
    print(index_mes1)

def main_func1():
    test_append_list1()
    # test_int_fushu()
    # test_round()
    # get_my_path()


    # path_cfg1 = r"C:\001chengxu\04\2020twelve_1207\08_web_test\test_base_func1\af-config.txt"
    # boll_res, res_data1 = read_txt1(path_cfg1)
    # if boll_res:
    #     print(res_data1)
    # else:
    #     print("读取配置文件失败")

    # write_change_mes(path_cfg1, res_data1)



'''处理得到的每个元素(字符串)'''
def deal_input_data1(name, data):
    bool_res1 = 0
    if "x" in name:
        res_d1 = int(float(data))
        if (res_d1 < -1000) or (res_d1 > 500):
            res_d1 = ""
            bool_res1 = 1
    elif "y" in name:
        res_d1 = int(float(data))
        if (res_d1 < 100) or (res_d1 > 9900):
            res_d1 = ""
            bool_res1 = 1
    else:
        res_d1 = round(float(data), 3)
        if (res_d1 < -5) or (res_d1 > 5):
            res_d1 = ""
            bool_res1 = 1
    return bool_res1, res_d1


def test_str_comb():

    ctx = {
            "claw1": {
                "x": [0, 0, 0], "y": [0, 0, 0], "t": [0, 0, 0]},
            "claw2": {
                "x": [0, 0, 0], "y": [0, 0, 0], "t": [0, 0, 0]},
            "claw3": {
                "x": [0, 0, 0], "y": [0, 0, 0], "t": [0, 0, 0]},
            "claw4": {
                "x": [0, 0, 0], "y": [0, 0, 0], "t": [0, 0, 0]}}
    bool_err = 0
    str_list1 = [["1", "2", "3", "4"], ["x", "y", "t"], ["a", "b", "c"]]
    tips = {"tips1": "<500整数", "tips2": "<9900内整数", "tips3": "<2小数"}
    res_post = {"data": ctx, "tip": tips}

    if len(str_list1) == 3:
        for num1 in str_list1[0]:
            claw_name1 = "claw" + num1
            for value1 in str_list1[1]:
                for cid in range(len(str_list1[2])):
                    c_name1 = value1 + num1 + str_list1[2][cid]
                    h_name1 = "h" + c_name1
                    res_xyt = "100" if value1 == "x" else "200" if value1 == "y" else "1.6"
                    if len(res_xyt) == 0:
                        continue
                    bool_res1, d_res1 = deal_input_data1(c_name1, res_xyt)
                    bool_err += bool_res1
                    if bool_err > 0:
                        break
                    ctx[claw_name1][value1][cid] = d_res1
    print("接收整理后的数据为：{}".format(ctx))

def main_func2():
    test_str_comb()



if __name__ == "__main__":
    main_func1()
    # main_func2()