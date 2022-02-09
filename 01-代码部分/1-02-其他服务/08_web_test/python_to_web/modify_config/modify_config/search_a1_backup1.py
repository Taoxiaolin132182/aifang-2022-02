# -*- coding: utf-8 -*-
from django.shortcuts import render
import os, json, copy

'''读取txt input:完整路径  output: 是否异常结果'''
def read_txt1(path_txt1):
    bool_read_ok = False  # 读取是否异常
    message1 = None
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

'''把信息写入 txt'''
def write_change_mes(path_w, data1):
    if data1 is None:
        data1 = {
            "claw1": {"x": [100, 100, 100], "y": [500, 500, 500], "t": [0.4, 0.4, 0.4]},
            "claw2": {"x": [100, 100, 100], "y": [500, 500, 500], "t": [0.4, 0.4, 0.4]},
            "claw3": {"x": [100, 100, 100], "y": [500, 500, 500], "t": [0.4, 0.4, 0.4]},
            "claw4": {"x": [100, 100, 100], "y": [500, 500, 500], "t": [0.4, 0.4, 0.4]}}
    with open(path_w, "w") as f_dict:
        f_dict.write(json.dumps(data1))  # 开始存信息，写入txt文件
    return data1

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


def show_mes2(request):
    # get_my_path()
    path_cfg1 = r"C:\001chengxu\04\2020twelve_1207\08_web_test\test_base_func1\af-config.txt"
    boll_res, res_data1 = read_txt1(path_cfg1)  # 读取 txt 文件，失败返回 False, None
    if not boll_res:
        print("读取配置文件失败, 开始赋予初始值")
        res_data1 = write_change_mes(path_cfg1, res_data1)  # 写入初始值，并返回来
    ctx = copy.deepcopy(res_data1)  # 拷贝给ctx 参数，后面会和post后的值作比较
    tips = {"tips1": "<500整数", "tips2": "<9900内整数", "tips3": "<2小数"}
    res_post = {"data": ctx, "tip": tips}
    if len(request.body) > 0:
        if request.POST:  # 当post 有返回时
            str_list1 = [["1", "2", "3", "4"], ["x", "y", "t"], ["a", "b", "c"]]
            bool_err = 0
            if len(str_list1) == 3:
                for num1 in str_list1[0]:
                    claw_name1 = "claw" + num1
                    for value1 in str_list1[1]:
                        for cid in range(len(str_list1[2])):
                            c_name1 = value1 + num1 + str_list1[2][cid]
                            h_name1 = "h" + c_name1
                            res_xyt = request.POST[h_name1]
                            if len(res_xyt) == 0:
                                continue
                            bool_res1, d_res1 = deal_input_data1(c_name1, res_xyt)
                            bool_err += bool_res1
                            if bool_err > 0:
                                break
                            ctx[claw_name1][value1][cid] = d_res1
                if bool_err > 0:
                    print("数据输出错误, 不进行写入")
                else:
                    print("收到数据：{}".format(ctx))
                    if ctx != res_data1:
                        write_change_mes(path_cfg1, ctx)
                        print("数据写入txt文档")
                    else:
                        print("修改内容一致，无需写入")

        return render(request, "show-mes2.html", res_post)
    else:
        return render(request, "show-mes2.html", res_post)


