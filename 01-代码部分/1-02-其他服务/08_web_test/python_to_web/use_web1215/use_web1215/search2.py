# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.views.decorators import csrf
import os, json, copy

'''读取txt input:完整路径  output: 是否异常结果'''
def read_txt1(path_txt1):
    bool_read_ok = False  # 读取是否异常
    res_dict1 = {}
    name_l_claw = [[["x1a", "x1b", "x1c"], ["y1a", "y1b", "y1c"], ["t1a", "t1b", "t1c"]],
                   [["x2a", "x2b", "x2c"], ["y2a", "y2b", "y2c"], ["t2a", "t2b", "t2c"]],
                   [["x3a", "x3b", "x3c"], ["y3a", "y3b", "y3c"], ["t3a", "t3b", "t3c"]],
                   [["x4a", "x4b", "x4c"], ["y4a", "y4b", "y4c"], ["t4a", "t4b", "t4c"]],]
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
                for km, vm in message1.items():
                    if "1" in km:
                        res_dict1 = vm
                # for km, vm in message1.items():
                #     ctrl_print("key:{}  对应的值 ：{}，值的类型为：{}".format(km, vm, type(vm)))
                #     if isinstance(vm, list):
                #         ctrl_print("数据组数：{}".format(len(vm)))
                #         for num_a in vm:
                #             ctrl_print("数据：{} 的类型为：{}".format(num_a, type(num_a)))
            print("读取txt配置文件，完成")
            bool_read_ok = True
        else:
            print("{} 该文件不存在".format(path_txt1))
    except Exception as e:
        print(f"read_txt1  err: {e}")
    return bool_read_ok, res_dict1


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


# 接收post请求数据
def search_post(request):
    data_list = {"showmes": {
        "x1a": 230, "x1b": 231, "x1c": 232,
        "y1a": 530, "y1b": 531, "y1c": 532,
        "t1a": 2.30, "t1b": 2.31, "t1c": 2.32,
    }}
    ctx = {}
    if request.POST:
        ctx['rlt'] = request.POST['x1a']
        print("收到数据：{}".format(ctx))
    return render(request, "post.html", {'data_list':data_list})

def show_mes1(request):
    # get_my_path()
    path_cfg1 = r"C:\001chengxu\04\2020twelve_1207\08_web_test\test_base_func1\af-config.txt"
    boll_res, res_data1 = read_txt1(path_cfg1)
    if boll_res:
        pass
        # print(res_data1)
    else:
        print("读取配置文件失败")
    bool_record1 = False
    ctx = copy.deepcopy(res_data1)
    # ctx = {"showmes": res_data1}
    # print(request.POST)
    if len(request.body) > 0:
        list_claw = ['hx1a', 'hx1b', 'hx1c', 'hy1a', 'hy1b', 'hy1c', 'ht1a', 'ht1b', 'ht1c', ]
        # print(request.POST)
        if request.POST:
            for name_l in list_claw:
                if request.POST[name_l] != "":
                    pname = name_l.replace("h", "")
                    if "t" in pname:
                        ctx[pname] = round(float(request.POST[name_l]), 3)
                        if (ctx[pname] < -5) or (ctx[pname] > 5):
                            ctx[pname] = 0; bool_record1 = True
                    else:
                        ctx[pname] = int(float(request.POST[name_l]))
                        if "x" in pname:
                            if (ctx[pname] < -1000) or (ctx[pname] > 500):
                                ctx[pname] = 0; bool_record1 = True
                        else:
                            if (ctx[pname] < 100) or (ctx[pname] > 9900):
                                ctx[pname] = 0; bool_record1 = True
            if bool_record1:
                bool_record1 = False
                print("数据输出错误")
            else:
                print("收到数据：{}".format(ctx))
                if ctx != res_data1:
                    write_change_mes(path_cfg1, ctx)
                    print("数据写入txt文档")
                else:
                    print("修改内容一致，无需写入")
        return render(request, "show-mes1.html", ctx)
    else:
        return render(request, "show-mes1.html", ctx)

def show_mes2(request):
    # get_my_path()
    path_cfg1 = r"C:\001chengxu\04\2020twelve_1207\08_web_test\test_base_func1\af-config.txt"
    boll_res, res_data1 = read_txt1(path_cfg1)
    if boll_res:
        pass
        # print(res_data1)
    else:
        print("读取配置文件失败")
    bool_record1 = False
    res_post = {"data": {}, "tip": {}}
    tips = {"tips1": "500以内整数", "tips2": "9900以内整数", "tips3": "2以内小数"}
    res_post["tip"] = tips
    ctx = copy.deepcopy(res_data1)
    res_post["data"] = ctx
    # print(request.POST)
    if len(request.body) > 0:
        list_claw = ['hx1a', 'hx1b', 'hx1c', 'hy1a', 'hy1b', 'hy1c', 'ht1a', 'ht1b', 'ht1c', ]
        # print(request.POST)
        if request.POST:
            for name_l in list_claw:
                if request.POST[name_l] != "":
                    pname = name_l.replace("h", "")
                    if "t" in pname:
                        ctx[pname] = round(float(request.POST[name_l]), 3)
                        if (ctx[pname] < -5) or (ctx[pname] > 5):
                            ctx[pname] = ""; bool_record1 = True
                    else:
                        ctx[pname] = int(float(request.POST[name_l]))
                        if "x" in pname:
                            if (ctx[pname] < -1000) or (ctx[pname] > 500):
                                ctx[pname] = ""; bool_record1 = True
                        else:
                            if (ctx[pname] < 100) or (ctx[pname] > 9900):
                                ctx[pname] = ""; bool_record1 = True
            if bool_record1:
                bool_record1 = False
                print("数据输出错误")
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