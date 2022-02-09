import urllib.request
import os
import json
import cv2

import requests
import time
import hashlib
import random
from utils.areas_count import areas_count
import json
import numpy as np

def requestWithSign(path, params, host="http://openapi.gmmsj.com/"):
    fixed_params = {
        "merchant_name": "AI_ADMIN",
        "timestamp": str(int(time.time())),
        "signature_method": "MD5"
    }

    params.update(fixed_params)

    url = host + path
    params["signature"] = sign(params)

    print("{}?{}".format(url, params))
    response = requests.get(url=url, params=params)
    response.raise_for_status()
    result = response.json()
    #     if result['return_code'] != 0:
    #         raise RequestInteralError(**result)
    print(result)
    if 'data' in result:
        result = result['data']
    else:
        result = None
    return result


def sign(params):
    sigKey = "8HM2NiElGzSIq9nNPtTW0ZH8Vk7YLWRB"
    sigValue = ""
    paraSign = ""
    sortData = {}

    sortData = sorted(params.items(), key=lambda asd: asd[0], reverse=False)

    for item in sortData:
        paraSign = paraSign + item[0] + "=" + str(item[1])

    paraSign = paraSign + sigKey
    paraSign = paraSign.encode()
    print(paraSign)
    sigValue = hashlib.md5(paraSign).hexdigest()

    return sigValue


def getHttp(url):
    page = urllib.request.urlopen(url)
    str = page.read()
    return str


project_name = "wool"

data_save_path_train = "./data/my_data/20201123_wool_test_3.txt"
data_save_path_test = "./data/my_data/202011160_wool_val.txt"

data_save_train = open(data_save_path_train, "w")
data_save_test = open(data_save_path_test, "w")
train_num_rate = 1.
id = 0

batch_list = []
for batch in open("./data/my_data/20201116_wool_data_batch_test.txt").readlines():
    batch_list.append(batch.split("\n")[0])

batch_list = ["ljpc-wool-2020111201-3"]

#
# batch_list = ["ss072401", "ss072402"]
# batch_list_1 = open("./data/my_data/train_batch_20200709.txt").readlines()
# batch_list_2 = open("./data/my_data/train_batch_20200714.txt").readlines()
# batch_list = set(batch_list_2) - set(batch_list_1)
# batch_list = open("./data/my_data/20200720_train_batch.txt").readlines()
# batch_list = ["20200401154524-3", "20200617132533-169"]
delete_labels = ["background", "R", "L", "L1", "R1", "QL", "QR",  "dcf", "gj"]
# batch_list = ["20200825140003-222","20200825141638-2"]
# for line in open("./data/my_data/train_batch_20200820_yths.txt"):
#     batch = line.split("\n")[0]
#     if batch not in batch_list:
#         batch_list.append(batch)

not_data_batch = []
deleted_labels = []
import random
little_cow = 0
for batch in batch_list:
    batch = batch.split("\n")[0]
    # print(batch)
    data = requestWithSign("aiadminapi/GetImageRecord/listByWhere", {"assignBatchNo":batch, "pageSize":10000, "belongBusiness":project_name, "handlerStatus":2, "status": 1})#"handler_status":2  "handlerStatus":2, 2是审核通过， 1是标注完成 "status": 1 #（审核）
    # str = json.loads(html)
    # list_key = []
    # print(data)
    if data is None:
        print(batch)
        not_data_batch.append(batch)
        continue
    batch_data = []
    # len_data = len(data)
    # random.shuffle(data)
    # data = data[:int(len_data * 0.2)]
    for children in data:
        # img_path = "Q:/images/" + children["path"]
        img_path = children["path"]
        # img_path = img_path.replace("images/sjht", "sjht")
        boxes_list = children["imageLabelPolygonExt"]
        boxes = []
        labels = []
        points = []
        for box in boxes_list:
            points_json = json.loads(box["polygonJson"])
            points_temp = []
            for point in points_json:
                points_temp.append([point["x"], point["y"]])
            points_temp = np.array(points_temp)
            x0 = np.min(points_temp[:, 0])
            x1 = np.max(points_temp[:, 0])
            y0 = np.min(points_temp[:, 1])
            y1 = np.max(points_temp[:, 1])
            # points.append(points_temp)
            boxes.append([x0, y0, x1, y1])
            # if box["labelType"] != "waz072714hsslqj":
            labels.append(box["labelType"])

            points.append(points_temp)

        right = True
        # for label in labels:
        #     if label not in jswq:
        #         right = False
        # if not right:
        #     print("find not right one")
        # if len(boxes) == 4 and right:
        line = img_path
        for i in range(len(points)):
            # if labels[i] != "waz072714hsslqj":
            if labels[i] not in delete_labels:
                line = line + "%" + labels[i]
                for point_temp in points[i]:
                    line = line + " %d %d" % (point_temp[0], point_temp[1])
            # if labels[i] in ["gj", "wxqy"]:
            #     if areas_count(boxes[i][2:]) > 1:
            #         line = line + " %s %d %d %d %d" % (labels[i], boxes[i][0], boxes[i][1], boxes[i][2], boxes[i][3])
            #     else:
            #         little_cow = little_cow + 1
            else:
                print("delete label:", labels[i])
                if labels[i] not in deleted_labels:
                    deleted_labels.append(labels[i])
        if len(boxes_list) > 0 and (len(line.split(" ")) > 2):
            batch_data.append(line)
            # pass

            id = id + 1
        else:
            # batch_data.append(line)
            pass
            # data_save.write(line)
            # data_save.write("\n")
            # id = id + 1
    train_num = int(len(batch_data) * train_num_rate)
    random.shuffle(batch_data)
    train_data = batch_data[:train_num]
    test_data = batch_data[train_num:]
    for line in train_data:
        data_save_train.write(line)
        data_save_train.write("\n")
    for line in test_data:
        data_save_test.write(line)
        data_save_test.write("\n")
print("not have data batch:", not_data_batch)
data_save_train.close()
data_save_test.close()
print("delete label:", deleted_labels)
print("little cow:", little_cow)
