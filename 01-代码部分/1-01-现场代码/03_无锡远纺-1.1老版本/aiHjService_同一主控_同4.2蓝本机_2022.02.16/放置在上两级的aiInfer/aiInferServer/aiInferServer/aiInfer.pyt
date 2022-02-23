from django.http import HttpResponse
import json
import tensorflow as tf
from tensorflow.python.platform import gfile
import tensorflow.contrib.tensorrt
import cv2
import numpy as np
import copy
import time

model_detection = None
model_classify = None
isModelForward = False #模型是否正在初始化


def infer(request):
    request.encoding = 'utf-8'

    imagePath = ""
    labels_name = ""
    if request.POST:
        imagePath = request.POST['imagePath']
        try:
            labels_name = request.POST['labels_name']
        except:
            labels_name = ""
    elif request.GET:
        imagePath = request.GET['imagePath']
        try:
            labels_name = request.GET['labels_name']
        except:
            labels_name = ""
    # print("+++++++++++++++++")
    # print(imagePath)
    # print(labels_name)
    # print("+++++++++++++++++")
    if len(imagePath) <= 0:
        retObj = {"return_code": -80001000, "return_message": "缺少参数: imagePath"}
        return HttpResponse(json.dumps(retObj))

    poitList = doInfer(imagePath, labels_name)

    retObj = {"return_code": 0, "return_message": "success"}
    retObj['data'] = poitList
    return HttpResponse(json.dumps(retObj))


# end infer()


class DetectionModelForward():
    def __init__(self, model_path):
        self.gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.50)
        with gfile.FastGFile(model_path, 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
        self.g = tf.Graph()
        with self.g.as_default():
            tf.import_graph_def(graph_def, name="")
        self.sess = tf.Session(graph=self.g, config=tf.ConfigProto(gpu_options=self.gpu_options))
        self.input_data = self.sess.graph.get_tensor_by_name("input_data:0")
        self.boxes = self.sess.graph.get_tensor_by_name("boxes_result:0")
        self.scores = self.sess.graph.get_tensor_by_name("scores_result:0")
        self.labels = self.sess.graph.get_tensor_by_name("class_result:0")
    def forward(self, data):
        boxes_, scores_, labels_ = self.sess.run([self.boxes, self.scores, self.labels], feed_dict={self.input_data: data})
        return boxes_, scores_, labels_

class ClasifyModelForward():
    def __init__(self, model_path):
        self.gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.50)
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
def doInfer(imagePath, labels_name):
    # print(imagePath)
    # print(labels_name)
    # 改成：加载AI模型的变量
    # start1 = time.time()
    global model_detection
    global model_classify
    global isModelForward

    if model_classify is None:
        if isModelForward == False:
            isModelForward = True
            # 改成：初始化AI模型的变量
            model_detection = DetectionModelForward("/media/data/trt_model/YOLOv3_TensorFlow/trt_model/yolov3_sjht_fp16_detection.pb")#/opt/model/yolov3_sjht.pb
            model_classify = ClasifyModelForward("/media/data/trt_model/YOLOv3_TensorFlow/trt_model/yolov3_sjht_fp16_classfipy.pb")
    # 改成：调用模型进行推断
    return callAiModel(model_detection, model_classify, imagePath, labels_name)


# end doInfer()
# labels = ["hsslqj01", "hsslqj02", "hzjsqj01", "thjsqj01", "bsslqj01", "yhuijsqj01", "yhjsqj02h-fm", "yhjsqj02h-zm", "yhjsqj03h-fm", "yhjsqj03h-zm",
#               "yhjsqj04h-fm", "yhjsqj04h-zm", "yhjsqj05h-fm", "yhjsqj05h-zm", "yhjsqj06h-fm", "yhjsqj06h-zm", "zsjsqj01h-fm", "zsjsqj01h-zm", "yhjsqj08h-zm",
#               "yhjsqj08h-fm", "yhjsqj09m-fm", "yhjsqj09m-zm", "ysjsqj01h-zm", "ysjsqj01h-fm", "ysjsqj02h-zm", "ysjsqj02h-fm", "yhjsqj01", "b+hslqj02h-fm",
#           "heisejsqj01", "heisejsqj03", "hsjsqj04h-fm", "hsjsqj04h-zm", "hsjsqj05-fm", "hsjsqj05-zm", "lsslqj01h"]
labels = ["hsslqj01", "hsslqj02", "hzjsqj01", "thjsqj01", "bsslqj01", "yhuijsqj01", "yhjsqj02h-fm", "yhjsqj02h-zm",
          "yhjsqj03h-fm", "yhjsqj03h-zm",
          "yhjsqj04h-fm", "yhjsqj04h-zm", "yhjsqj05h-fm", "yhjsqj05h-zm", "yhjsqj06h-fm", "yhjsqj06h-zm",
          "zsjsqj01h-fm", "zsjsqj01h-zm", "yhjsqj08h-zm",
          "yhjsqj08h-fm", "yhjsqj09m-fm", "yhjsqj09m-zm", "ysjsqj01h-zm", "ysjsqj01h-fm", "ysjsqj02h-zm",
          "ysjsqj02h-fm", "yhjsqj01", "b-hslqj02h-fm",
          "heisejsqj01", "heisejsqj03", "hsjsqj04h-fm", "hsjsqj04h-zm", "hsjsqj05-fm", "hsjsqj05-zm", "lsslqj01h", "dhsjsqj-zm", "dhsjsqj-fm", "background"]

labels_num = len(labels)

def fill_new(image):
    ori_w, ori_h = image.shape[1], image.shape[0]
    new_size = max(ori_h, ori_w)
    new_img = np.zeros([new_size, new_size, 3], dtype=np.float32) #np.float32 np.uint8
    x0 = int((new_size - ori_w)/2)
    y0 = int((new_size - ori_h)/2)
    new_img[y0: y0+ori_h, x0:x0+ori_w, :] = image
    return new_img

def callAiModel(model_detection, model_classify, imagePath, labels_name):
    img_paths = imagePath.split(",")
    if labels_name != "":
        labels_name = labels_name.split(",")
    else:
        labels_name = []
    labels_id = []
    if len(labels_name) > 0:
        #labels_id = []
        for name in labels_name:
            labels_id.append(labels.index(name.split(" ")[0]))
            name_suffix = name.split("-")[-1]
            if name_suffix == "fm" and name != "b-hslqj02h-fm":
                name_change = name.replace("fm", "zm")
                labels_id.append(labels.index(name_change))
            elif name_suffix == "zm":
                name_change = name.replace("zm", "fm")
                labels_id.append(labels.index(name_change))
            else:
                pass
        labels_id.append(labels_num - 1)
    else:
        labels_id = [id for id in range(labels_num)]
    returnObjs = {}
    for img_path_id in range(len(img_paths)):
        img = []
        # start_read_img = time.time()
        try:
            img = cv2.imread(img_paths[img_path_id])
            # img = cv2.resize(img, (5440, 3648))
            # img_org = copy.deepcopy(img)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except:
            returnObj = {}
            returnObj['boxes'] = []
            returnObj['scores'] = []
            returnObj['labels'] = []
            returnObj['img_exist'] = 0
            return returnObj
        # end_read_img = time.time()
        # img = np.asarray(img, np.float32)
        # data = img[np.newaxis, :] / 255.
        img_detection = cv2.resize(img, tuple([3008, 2016]))
        img_detection = img_detection[np.newaxis, :]
        boxes_, scores_, labels_ = model_detection.forward(img_detection)
        #print(boxes_)
        boxes_[:, 0] *= (3648. / 2016.)
        boxes_[:, 2] *= (3648. / 2016.)
        boxes_[:, 1] *= (5472. / 3008.)
        boxes_[:, 3] *= (5472. / 3008.)
        labels_cut = []
        for box in boxes_:
            x0, y0, x1, y1 = box
            img_cut = img[int(y0): int(y1), int(x0): int(x1), :]
            cv2.imwrite("box.jpg", img_cut)
            img_cut = fill_new(img_cut)
            img_cut = cv2.resize(img_cut, tuple([192, 192]))
            img_classify = img_cut[np.newaxis, :]
            label_cut = model_classify.forward(img_classify)
            labels_cut.append(label_cut[0][0])
        labels_ = np.array(labels_cut)
        labels_return = []
        if len(boxes_) > 0:
            labels_select = labels_[:, labels_id]
            labels_max = np.argmax(labels_select, axis=1)
            labels_result = []
            for i in range(len(boxes_)):
                labels_result.append(labels_id[labels_max[i]])
            for id in labels_result:
                labels_return.append(labels[id])
            labels_mask = np.array(labels_result) < labels_num - 1
            labels_return = np.array(labels_return)[labels_mask > 0]
            boxes_ = boxes_[labels_mask > 0]
            scores_ = scores_[labels_mask > 0]
        else:
            pass

        returnObj = {}
        returnObj['boxes'] = boxes_.tolist()
        returnObj['scores'] = scores_.tolist()
        returnObj['labels'] = labels_return.tolist()
        returnObj['img_exist'] = 1
        returnObjs[str(img_path_id)] = returnObj
    # print(time.time() - start1)
    return returnObjs
# end callAiModel()
