# coding:utf-8
import uuid

mac_id_list = [
    [1, "48b02d4d3ed8"],
    [2, "00044be59dfe"]
]


'''可行，获取本机的mac地址'''
def get_mac_address():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return "".join([mac[e:e + 2] for e in range(0, 11, 2)])

def back_to_arm_num():
    parm_num = 0
    str_mac = get_mac_address()
    print("本机mac:{}".format(str_mac))
    for mac_id in mac_id_list:
        if str_mac == mac_id[1]:
            parm_num = mac_id[0]
            break
    return parm_num

if __name__ == '__main__':
    str_mac = back_to_arm_num()
    print(str_mac)
