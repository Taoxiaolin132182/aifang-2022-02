# # coding=utf-8
import time, socket, json, threading, copy
from record_cfg import get_file_time, load_config, change_to_strtime

list_data_g1 = [False, {}]

def client_a1(ip_list_c, pc_name):
    print("启动客户端")
    global list_data_g1
    bool_run_c = True
    while bool_run_c:
        time.sleep(0.1)
        try:
            c_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            c_send.connect((ip_list_c[0], ip_list_c[1]))
            print("已连接上服务端")
            bool_client1 = True
            dict_data = {"pc_name": pc_name, "times": 0}
            while bool_client1:
                if list_data_g1[0]:
                    dict_data["times"] += 1
                    dict_data_send = {}
                    list_data_g1[0] = False
                    dict_data_send.update(dict_data)
                    dict_data_send.update(list_data_g1[1])
                    data_s = bytes(json.dumps(dict_data_send), encoding="utf-8")
                    c_send.send(data_s)
                    rec_data1 = str(c_send.recv(1024), encoding="utf-8")  # 先转成string
                    rec_d2 = json.loads(rec_data1)
                    ret_t1 = rec_d2["times"]
                    print("第{}次发送数据后的返回：{}".format(ret_t1, rec_d2))
                else:
                    print("客户端 未检测出 配置文件的更新，循环等待")
                    time.sleep(5)
            c_send.close()
        except Exception as e:
            print(f"error! --client_a1:{e}")
            # c_send.close()
            print("由于异常，停顿5秒")
            time.sleep(5)

'''服务端 调用的应答函数'''
def reply_client(server_sck, ip_port):  # 客户端的套接字对象，IP信息
    str_check1 = {"msg": "success"}  # 接收成功的返回值
    client_name = None
    while True:
        time.sleep(0.1)
        rec_d1 = server_sck.recv(1024)  # 等待接收
        if rec_d1:
            res_data2 = str(rec_d1, encoding="utf-8")  # byte --> 字符串
            res_d3 = json.loads(res_data2)  # 字符串 --> 字典
            if res_d3["times"] == 1:
                if client_name is None:
                    client_name = res_d3["pc_name"]
                print("====  客户端名称：{}---->> 信息：{}".format(client_name, ip_port))
            print("客户端传来的数据：{}".format(res_d3))
            str_check1["times"] = res_d3["times"]  # 计数次数
            server_sck.send(bytes(json.dumps(str_check1), encoding="utf-8"))  # 字典 --> 字符串 --> byte
        else:
            print("客户端：{}, 已下线".format(client_name))
            break
    server_sck.close()

def server_a1(ip_list_s):
    print("启动服务端")
    r_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    r_server.bind((ip_list_s[0], ip_list_s[1]))
    r_server.listen(5)
    bool_server1 = True
    keep_time_length = 60 * 10
    t_start1 = time.time()
    while bool_server1:
        time.sleep(0.1)
        try:
            conn, addr = r_server.accept()
            th_reply1 = threading.Thread(target=reply_client, args=(conn, addr,))
            th_reply1.start()

        except Exception as e:
            print(f"error! --server_a1:{e}")
        if (time.time() - t_start1) > keep_time_length:
            print("服务端 到达时限，退出程序")
            break
    r_server.close()

def read_json_cfg():
    global list_data_g1
    f_time1 = []
    bool_start_run = True
    path_cfg = "./arm_cfg.json"
    print("进入读取json文件进程")
    name_time = ["修改", "创建", ]
    while bool_start_run:
        time.sleep(0.1)
        now_time = get_file_time(path_cfg)
        if f_time1 == now_time:
            # print("从文件的时间属性上看，文件未更新，循环等待")
            time.sleep(5)
            continue
        else:
            f_time1 = copy.deepcopy(now_time)
            for i in range(len(f_time1)):
                t_format = change_to_strtime(f_time1[i])
                print("{}时间：{}".format(name_time[i], t_format))
        data_cfg = load_config(path_cfg)
        # print("返回的数据 类型：{}".format(type(data_cfg)))
        # print("返回的数据 内容：{}".format(data_cfg))
        list_data_g1 = [True, data_cfg]
        # for k1, v1 in data_cfg.items():
        #     print("键:{} 对应的值类型是:{},内容是:{}".format(k1, type(v1), v1))
        time.sleep(5)


def main_func1():
    ctrl_num = 11   # 个位数是服务端
    ip_list = ["10.246.104.110", 8030]
    p_name = ["A", "B", "C", "D"]
    num_name = 0
    if ctrl_num < 10:
        server_a1(ip_list)
    else:
        th_reply1 = threading.Thread(target=read_json_cfg)
        th_reply1.start()
        time.sleep(3)
        client_a1(ip_list, p_name[num_name])





if __name__ == "__main__":
    main_func1()