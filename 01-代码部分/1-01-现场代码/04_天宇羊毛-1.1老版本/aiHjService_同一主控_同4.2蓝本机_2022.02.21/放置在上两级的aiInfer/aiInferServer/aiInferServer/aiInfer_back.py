from django.http import HttpResponse
import os
import json
import tensorflow as tf
from datetime import datetime
from tensorflow.python.platform import gfile
import tensorflow.contrib.tensorrt
import cv2
import numpy as np
# import args
import copy
import time
# from logging_util import Logger

model_detection = None
# model_classify = None
isModelForward = False #模型是否正在初始化
model_config = None #配置文件
# classFilePath = ""
# detectionModelPath = ""
# clasifyModelPath = ""

labels = []
labels_num = len(labels)



def infer(request):
    print("start infer", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    request.encoding = 'utf-8'

    imagePath = ""
    # labels_name = ""
    if request.POST:
        imagePath = request.POST['imagePath']
        # try:
        #     labels_name = request.POST['labels_name']
        # except:
        #     labels_name = ""
    elif request.GET:
        imagePath = request.GET['imagePath']
        # try:
        #     labels_name = request.GET['labels_name']
        # except:
        #     labels_name = ""
    # print("+++++++++++++++++")
    # print(imagePath)
    # print(labels_name)
    # print("+++++++++++++++++")
    if len(imagePath) <= 0:
        retObj = {"return_code": -80001000, "return_message": "缺少参数: imagePath"}
        return HttpResponse(json.dumps(retObj))
    retObj = {"return_code": 0, "return_message": "success"}
    try:
        # poitList = doInfer(imagePath, labels_name)
        poitList = doInfer(imagePath)
        retObj['data'] = poitList
    except Exception as e:
        print(e)
        retObj = {"return_code": 1, "return_message": str(e)}
    print("end infer", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    return HttpResponse(json.dumps(retObj))


# end infer()

# '''
# 发送当前ai模型地址
# '''
# def sendCurrentAiModel(request):
#     data = {}
#
#     # data['classFilePath'] = classFilePath
#     data['detectionModelPath'] = detectionModelPath
#     # data['clasifyModelPath'] = clasifyModelPath
#
#     retObj = {}
#     retObj = {"return_code": 0, "return_message": "success","data":data}
#
#     return HttpResponse(json.dumps(retObj))
#
# '''
# 接受需要的ai模型地址
# '''
# def reciveModelPath(request):
#     # global classFilePath
#     global detectionModelPath
#     # global clasifyModelPath
#     if request.POST:
#         # classFilePath = request.POST['classFilePath']
#         detectionModelPath = request.POST['detectionModelPath']
#         # clasifyModelPath = request.POST['clasifyModelPath']
#     elif request.GET:
#         # classFilePath = request.GET['classFilePath']
#         detectionModelPath = request.GET['detectionModelPath']
#         # clasifyModelPath = request.GET['clasifyModelPath']
#
#     retObj = {"return_code": 0, "return_message": "success"}
#
#     return HttpResponse(json.dumps(retObj))


# class DetectionModelForward():
#     def __init__(self, model_path):
#         self.gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.40)
#         with gfile.FastGFile(model_path, 'rb') as f:
#             graph_def = tf.GraphDef()
#             graph_def.ParseFromString(f.read())
#         self.g = tf.Graph()
#         with self.g.as_default():
#             tf.import_graph_def(graph_def, name="")
#         self.sess = tf.Session(graph=self.g, config=tf.ConfigProto(gpu_options=self.gpu_options))
#         self.input_data = self.sess.graph.get_tensor_by_name("input_data:0")
#         self.boxes = self.sess.graph.get_tensor_by_name("boxes_result:0")
#         self.scores = self.sess.graph.get_tensor_by_name("scores_result:0")
#         self.labels = self.sess.graph.get_tensor_by_name("class_result:0")
#     def forward(self, data):
#         boxes_, scores_, labels_ = self.sess.run([self.boxes, self.scores, self.labels], feed_dict={self.input_data: data})
#         return boxes_, scores_, labels_



#加载模型json字符串
def load_json(json_str):
    global model_config
    with open(json_str, 'rb') as f:
        model_config = json.load(f)
    # model_config = json.loads(json_str)
    # logger.info_ai(meg="load json", api_name="load json", get_ins={"model_config": model_config})

class DetectionModelForward():
    def __init__(self, model_path):
        self.gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.40)
        with gfile.FastGFile(model_path, 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
        self.g = tf.Graph()
        with self.g.as_default():
            tf.import_graph_def(graph_def, name="")
        self.sess = tf.Session(graph=self.g, config=tf.ConfigProto(gpu_options=self.gpu_options))
        self.input_data = self.sess.graph.get_tensor_by_name("input_data:0")
        self.iou_thresh = self.sess.graph.get_tensor_by_name("iou_thresh:0")
        self.score_thresh = self.sess.graph.get_tensor_by_name("score_thresh:0")

        self.boxes = self.sess.graph.get_tensor_by_name("boxes_result:0")
        self.scores = self.sess.graph.get_tensor_by_name("scores_result:0")
        self.labels = self.sess.graph.get_tensor_by_name("class_result:0")
    def forward(self, data, iou_thresh=0.1, score_thresh=0.1):
        boxes_, scores_, labels_ = self.sess.run([self.boxes, self.scores, self.labels], feed_dict={self.input_data: data, self.iou_thresh: iou_thresh, self.score_thresh: score_thresh})
        return boxes_, scores_, labels_

class ClasifyModelForward():
    def __init__(self, model_path):

        self.gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.40)
        with gfile.FastGFile(model_path, 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
        self.g = tf.Graph()
        with self.g.as_default():
            tf.import_graph_def(graph_def, name="")
        self.sess = tf.Session(graph=self.g, config=tf.ConfigProto(gpu_options=self.gpu_options))
        self.input_data = self.sess.graph.get_tensor_by_name("input_data:0")
        self.labels = self.sess.graph.get_tensor_by_name("class_result:0")
    def forward(self, data):
        labels_ = self.sess.run([self.labels], feed_dict={self.input_data: data})
        return labels_





# start1 = 0
def doInfer(imagePath):
    # print(imagePath)
    # print(labels_name)
    # 改成：加载AI模型的变量
    # start1 = time.time()
    global model_detection
    # global model_classify
    global isModelForward
    global model_config
    # print("classFilePath = ", classFilePath)
    # print("detectionModelPath = ", detectionModelPath)
    # print("clasifyModelPath = ",clasifyModelPath)
    # if classFilePath is not None and labels_num == 0:
    #     load_labels(classFilePath)
    #配置文件路径修改
    if model_config is None:
        load_json("/mnt/data/data/aimodel/cotton_config.txt")

    if isModelForward == False:
        isModelForward = True
        # 改成：初始化AI模型的变量
        # model_detection = DetectionModelForward("/media/data/Data/model/zangmian/tf-rt/wxmfc_detection_yolov3/20200326/yolov3_zangmian_fp16_detection.pb")#/opt/model/yolov3_sjht.pb
        # model_detection = DetectionModelForward("/media/data/Data/model/wool/model_build/yolov3_wool_fp16_detection.pb")#/opt/model/yolov3_sjht.pb
        model_detection = DetectionModelForward("/mnt/data/data/aimodel/cotton_model.pb")  # /opt/model/yolov3_sjht.pb

    # 改成：调用模型进行推断
    return callAiModel(model_detection, imagePath)



def load_labels(path):
    global labels
    labels = []
    for line in open(path).readlines():
        labels.append(line.split("\n")[0])
    print("labels_num = ",len(labels))
    global labels_num
    labels_num = len(labels)

def fill_new(image):
    ori_w, ori_h = image.shape[1], image.shape[0]
    new_size = max(ori_h, ori_w)
    new_img = np.zeros([new_size, new_size, 3], dtype=np.float32) #np.float32 np.uint8
    x0 = int((new_size - ori_w)/2)
    y0 = int((new_size - ori_h)/2)
    new_img[y0: y0+ori_h, x0:x0+ori_w, :] = image
    return new_img


def clamp_bboxs(boxs, img_size, to_remove=1):

    boxs[:, 0].clip(min=0, max=img_size[0] - to_remove)
    boxs[:, 1].clip(min=0, max=img_size[1] - to_remove)
    boxs[:, 2].clip(min=0, max=img_size[0] - to_remove)
    boxs[:, 3].clip(min=0, max=img_size[1] - to_remove)

    return boxs

def delete_background(image):
    kernel = np.ones((40, 40), np.uint8)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image_channel = gray
    background_region = np.asarray(np.where(image_channel < 40, 0, 1) * 255, np.uint8)
    background_region = cv2.erode(background_region, kernel=kernel, iterations=1)
    background_region = cv2.dilate(background_region, kernel=kernel, iterations=1)
    # cv2.imshow("background_region_1", cv2.resize(background_region, (800, 800)))
    background_region = background_region[..., np.newaxis]
    background_region = np.concatenate([background_region, background_region, background_region], axis=-1)
    cv2.imshow("background_region", cv2.resize(background_region, (800, 800)))
    background_region = background_region / 255
    image = image * background_region
    image = np.asarray(image, np.uint8)
    return image

def plot_one_box(img, coord, label=None, color=None, line_thickness=None):
    '''
    coord: [x_min, y_min, x_max, y_max] format coordinates.
    img: img to plot on.
    label: str. The label name.
    color: int. color index.
    line_thickness: int. rectangle line thickness.
    '''
    tl = line_thickness or int(round(0.002 * max(img.shape[0:2])))  # line thickness
    # color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(coord[0]), int(coord[1])), (int(coord[2]), int(coord[3]))
    cv2.rectangle(img, c1, c2, color, thickness=3)#thickness=tl
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=float(tl) / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        # cv2.rectangle(img, c1, c2, color, -1)  # filled
        # cv2.rectangle(img, c1, c2, color ,thickness=0)  # filled#label的框
        # cv2.putText(img, label, (c1[0], c1[1] - 2), 0, float(tl) / 3, color, thickness=tf, lineType=cv2.LINE_AA)
        cv2.putText(img, label, (c1[0], c1[1] - 2), cv2.FONT_HERSHEY_COMPLEX, float(tl) / 3, color, thickness=3, lineType=cv2.LINE_AA)




def callAiModel(model_detection, imagePath, model_classify=None, labels_name=None):
    Score = 0.1
    start_time = time.time()
    img_paths = imagePath.split(",")


    # if labels_name != "":
    #     labels_name = labels_name.split(",")
    # else:
    #     labels_name = []
    # labels_id = []
    # if len(labels_name) > 0:
    #     #labels_id = []
    #     print(labels_name)
    #     for name in labels_name:
    #         print(name)
    #         labels_id.append(labels.index(name.split(" ")[0]))
    #         name_suffix = name.split("-")[-1]
    #         # if name_suffix == "fm" and name not in ["b-hslqj02h-fm", "hssjqj01h-fm", "hssjqj03h-fm"]:
    #         if name_suffix == "fm":
    #             name_change = name.replace("fm", "zm")
    #             if name_change in labels:
    #                 labels_id.append(labels.index(name_change))
    #             else:
    #                 print("not find class:%s"%name_change)
    #         elif name_suffix == "zm":
    #             name_change = name.replace("zm", "fm")
    #             if name_change in labels:
    #                 labels_id.append(labels.index(name_change))
    #             else:
    #                 print("not find class:%s" % name_change)
    #         else:
    #             pass
    #     labels_id.append(0)
    # else:
    #     labels_id = [id for id in range(labels_num)]
    returnObjs = {}
    for img_path_id in range(len(img_paths)):
        img = []
        start_read_img = time.time()
        try:
            img = cv2.imread(img_paths[img_path_id])
            # img = cv2.resize(img, (5440, 3648))
            img_org = copy.deepcopy(img)
            # img = delete_background(img)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except:
            returnObj = {}
            returnObj['boxes'] = []
            returnObj['scores'] = []
            returnObj['labels'] = []
            returnObj['class_scores'] = []
            returnObj['img_exist'] = 0
            return returnObj
        end_read_img = time.time()
        print("read time:%f"%(end_read_img - start_read_img))
        start_detection_time = time.time()
        # img = np.asarray(img, np.float32)
        # data = img[np.newaxis, :] / 255.
        # img_detection = cv2.resize(img, tuple([3008, 2016]))#
        # img_detection = cv2.resize(img, tuple([2048, 2048]))
        image_size = model_config["image_size"]
        img_detection = cv2.resize(img, tuple([image_size, image_size]))
        img_detection = img_detection[np.newaxis, :]
        boxes_, scores_, labels_ = model_detection.forward(img_detection, iou_thresh=0.1, score_thresh=0.1)
        end_detection_time = time.time()
        print("detection time:%f" % (end_detection_time - start_detection_time))

        # boxes_[:, 0] *= (5472. / 3008.)
        # boxes_[:, 2] *= (5472. / 3008.)
        # boxes_[:, 1] *= (3648. / 2016.)
        # boxes_[:, 3] *= (3648. / 2016.)
        boxes_[:, 0] *= (2448. / image_size)
        boxes_[:, 2] *= (2448. / image_size)
        boxes_[:, 1] *= (2048. / image_size)
        boxes_[:, 3] *= (2048. / image_size)
        #boxes clip
        if len(boxes_) > 0:
            # boxes_ = clamp_bboxs(boxes_, [5472, 3648], to_remove=1)
            boxes_ = clamp_bboxs(boxes_, [2448, 2048], to_remove=1)

        # labels_cut = []
        # for box in boxes_:
        #     x0, y0, x1, y1 = box
        #     img_cut = img[int(y0): int(y1), int(x0): int(x1), :]
        #     img_cut = fill_new(img_cut)
        #     img_cut = cv2.resize(img_cut, tuple([192, 192]))
        #     img_classify = img_cut[np.newaxis, :]
        #     label_cut = model_classify.forward(img_classify)
        #     labels_cut.append(label_cut[0][0])
        # labels_ = np.array(labels_cut)
        # labels_return = []
        # if len(boxes_) > 0:
        #     #print(labels_id)
        #     labels_select = labels_[:, labels_id]
        #     labels_max = np.argmax(labels_select, axis=1)
        #     labels_result = []
        #     for i in range(len(boxes_)):
        #         labels_result.append(labels_id[labels_max[i]])
        #     for id in labels_result:
        #         labels_return.append(labels[id])
        #     labels_mask = np.array(labels_result) > 0
        #     labels_return = np.array(labels_return)[labels_mask > 0]
        #     boxes_ = boxes_[labels_mask > 0]
        #     scores_ = scores_[labels_mask > 0]
        # else:
        #     labels_return = np.array(labels_return)
        #     pass
        w = boxes_[:, 2] - boxes_[:, 0]
        h = boxes_[:, 3] - boxes_[:, 1]
        s = w * h
        boxes_list = boxes_.tolist()
        scores_list = scores_.tolist()
        labels_list = labels_.tolist()

        boxes_return = list()
        scores_return = list()
        labels_return = list()
        # class_names = ["qianhuangmao", "yixian", "kongqiangmao", "shenhuangmao"]
        for n, score in enumerate(scores_list):
            if score >= Score and s[n] > model_config["area_factor"]:
                boxes_return.append(boxes_list[n])
                scores_return.append(scores_list[n])
                labels_return.append(model_config["class_names"][int(labels_list[n])])
        if model_config["zangmian_score_factor"] > 0:
            labels_temp = []
            for label_id in range(len(labels_return)):
                if labels_return[label_id] == "zangmian" and scores_return[label_id] >= model_config["zangmian_score_factor"]:
                    labels_temp.append("zangmian")
                else:
                    labels_temp.append("yixian")
            labels_return = labels_temp

        #drow box
        # for j in range(len(boxes_return)):
        #     # print(j)
        #     label_, score_, x_min, y_min, x_max, y_max = labels_return[j], scores_return[j], boxes_return[j][0], boxes_return[j][1], boxes_return[j][2], boxes_return[j][3]
        #     # class_names为所有类别名列表或元组，label为类别索引
        #     """color for diferent classes."""
        #     # hsv_tuples = [(x / len(class_names), 1., 1.) for x in range(
        #     #     len(class_names))]  # 构建80个倒数   shape = [(0/80, 1.0, 1.0), (1/80, 1.0, 1.0), (2/80, 1.0, 1.0), ....]
        #     # """hsv_tuples中 hue（色相）、saturation（饱和度）、value(色调)"""
        #     # for ii, oncee in enumerate(class_names):
        #     #     if oncee == label:
        #     #         label_num = ii
        #     # colors = list(map(lambda x: hsv_to_rgb(*x), hsv_tuples))
        #     # colors = list(
        #     #     map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)), colors))  # 为了区分不同的类画检测框而用
        #
        #     # plot_one_box(img, [x_min, y_min, x_max, y_max], label=str(label_) + "|" + str(score_), color=colors[label_num])
        #     plot_one_box(img_org, [x_min, y_min, x_max, y_max], label=str(label_) + "|" + str(score_))
        # path_ = imagePath.split("/")[-1]
        # subdir = datetime.strftime(datetime.now(), '%Y%m%d-%H_%M_%S')
        # date_path1 = time.strftime("%Y_%m%d", time.localtime())
        # if not os.path.exists("/media/data/Data/image/"):
        #     os.makedirs("/media/data/Data/image/")
        # if not os.path.exists("/media/data/Data/image/havebox/"):
        #     os.makedirs("/media/data/Data/image/havebox/")
        # if not os.path.exists("/media/data/Data/image/nobox/"):
        #     os.makedirs("/media/data/Data/image/nobox/")
        #
        # havebox_path = "/media/data/Data/image/havebox/" + date_path1
        # nobox_path = "/media/data/Data/image/nobox/" + date_path1
        # path = subdir + ".jpg"
        # if not os.path.exists(nobox_path):
        #     os.makedirs(nobox_path)
        # if not os.path.exists(havebox_path):
        #     os.makedirs(havebox_path)
        # if len(boxes_return):
        #     cv2.imwrite(os.path.join(havebox_path, path_), img_org)
        # else:
        #     cv2.imwrite(os.path.join(nobox_path, path_), img_org)



        returnObj = {}
        # returnObj['boxes'] = boxes_.tolist()
        # returnObj['scores'] = scores_.tolist()
        # # returnObj['labels'] = labels_return.tolist()
        # returnObj['labels'] = labels_.tolist()
        returnObj['boxes'] = boxes_return
        returnObj['scores'] = scores_return
        # returnObj['labels'] = labels_return.tolist()
        returnObj['labels'] = labels_return
        returnObj['class_scores'] = []
        returnObj['img_exist'] = 1
        returnObjs[str(img_path_id)] = returnObj
    end_time = time.time()
    print("all time:%f" % (end_time - start_time))
    # print(time.time() - start1)
    return returnObjs
# end callAiModel()
