from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
from tensorflow.python.platform import gfile
import tensorflow.contrib.tensorrt
import os
import time
import cv2
import copy
import numpy as np

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



# img = cv2.imread("/mnt/AIdata/images4code2/images/sjht/sjht-20191028103806228291/1/sjht-20191028103806228291_1572230303922606.2_1800389779584.png")
# img = cv2.resize(img, (5440, 3648))



detection_model_forward = DetectionModelForward("./trt_model/yolov3_sjht_fp16_detection.pb")
clssify_model_forward = ClasifyModelForward("./trt_model/yolov3_sjht_fp16_classfipy.pb")
# model_forward = ModelForward("/media/lantaincug/DATADRIVE1/lantiancug/projects/work/YOLOv3_TensorFlow/tensorflow_trt/checkpoints/yolov3.pb")
id = 0
time_list = []
time_max = 0
time_min = 0
classes = []
for line in  open("./data/my_data/class.txt").readlines():
    classes.append(line.split("\n")[0])
# test_path = "/mnt/AIdata/images4code2/images/sjht/ai-product-injection-mold-inserts/pic/examine/20191130102949-31"
# img_list = os.listdir(test_path)
# for img_name in img_list:
    # img_path = test_path + "/" + img_name
def fill(image):
    ori_w, ori_h = image.shape[1], image.shape[0]
    if ori_w >= ori_h:
        tmp = int((ori_w - ori_h) / 2)
        image = cv2.copyMakeBorder(image, 0, tmp, 0, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        image = cv2.copyMakeBorder(image, tmp, 0, 0, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])

    else:
        tmp = int((ori_h - ori_w) / 2)
        image = cv2.copyMakeBorder(image, 0, 0, 0, tmp, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        image = cv2.copyMakeBorder(image, 0, 0, tmp, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])

    return image

def fill_new(image):
    ori_w, ori_h = image.shape[1], image.shape[0]
    new_size = max(ori_h, ori_w)
    new_img = np.zeros([new_size, new_size, 3], dtype=np.float32) #np.float32 np.uint8
    x0 = int((new_size - ori_w)/2)
    y0 = int((new_size - ori_h)/2)
    new_img[y0: y0+ori_h, x0:x0+ori_w, :] = image
    return new_img


while True:
    img_path = "./camera0_2019_12_19_17_15_48.jpg"
    img = cv2.imread(img_path)
    #height_ori, width_ori, _ = img.shape
    img_org = copy.deepcopy(img)
    img_ori = copy.deepcopy(img)
    start = time.time()
    img_org = cv2.cvtColor(img_org, cv2.COLOR_BGR2RGB)
    start_1 = time.time()
    print("cvt_time:%f"%(start_1 - start))
    #img_detection = cv2.resize(img_org, tuple([2368, 1568]))
    #img_org = np.asarray(img_org, np.float32)/255.
    #img_org = img_org/255.
    start_2 = time.time()
    print("as_time:%f"%(start_2 - start_1))
    img_detection = cv2.resize(img_org, tuple([3008, 2016]))
    start_3 = time.time()
    print("resize_time:%f"%(start_3 - start_2))

    img_detection = img_detection[np.newaxis, :]
    #_, width_det, height_det, _ = img_detection.shape
    d_start = time.time()
    print("pretreat_time:%f"%(d_start - start))
    boxes_, scores_, labels_ = detection_model_forward.forward(img_detection)
    d_end = time.time()
    print("d_time:%f"%(d_end - d_start))
    boxes_[:, 0] *= (3648. / 2016.)
    boxes_[:, 2] *= (3648. / 2016.)
    boxes_[:, 1] *= (5472. / 3008.)
    boxes_[:, 3] *= (5472. / 3008.)
    labels_cut = []
    end_1 = time.time()
    print("boxes_time:%f"%(end_1 - d_end))
    for box in boxes_:
        x0, y0, x1, y1 = box
        if y1 - y0 > 5 and x1 - x0 > 5:
            img_cut = img_org[int(y0): int(y1), int(x0): int(x1), :]
            img_cut = fill_new(img_cut)
            img_cut = cv2.resize(img_cut, tuple([192,192]))
            img_classify = img_cut[np.newaxis, :]
            c_start = time.time()
            label_cut = clssify_model_forward.forward(img_classify)
            c_end = time.time()
            #print("c_time:%f"%(c_end - c_start))
            labels_cut.append(label_cut[0])
    end_2 = time.time()
    print("c_time:%f"%(end_2 - end_1))
    print("all_time:%f"%(end_2 - start))
    id = id + 1
    if id == 1:
        print("+++++++++++++++++++++++start++++++++++++++++++")
    if id > 10:
        time_list.append(end_2-start)
        print(id, max(time_list), min(time_list), sum(time_list)/len(time_list))


    for i in range(len(boxes_)):
        x0, y0, x1, y1 = boxes_[i]
        s = (x1 - x0) * (y1 - y0)
        if s > 0:
                    # logits_softmax_show = logits_softmax_[i].argsort()[-3:][::-1]
            cv2.rectangle(img_ori, (int(x0), int(y0)), (int(x1), int(y1)), [255, 255, 0], 4)
            #cv2.putText(img_ori, "%s_%.2f" % (classes[labels_cut[i]], scores_[i]),
             #                   (int(x0), int(y0) - 16), 0, 2, [0, 0, 255], 5, lineType=cv2.LINE_AA)
                    # cv2.putText(img_ori, "%s_%s_%s_%.2f" % (classes[logits_softmax_show[0]], classes[logits_softmax_show[1]], classes[logits_softmax_show[2]], scores_[i]),
                    #             (int(x0), int(y0) - 16), 0, 2, [0, 0, 255], 5, lineType=cv2.LINE_AA)

    cv2.imwrite('./find.jpg', img_ori)
        #print(end_2 - end_1)
    # for i in range(len(boxes_)):
    #     x0, y0, x1, y1 = boxes_[i]
    #     cv2.rectangle(img, (int(x0), int(y0)), (int(x1), int(y1)), [255, 255, 0], 4)
    #     cv2.putText(img, "%s_%.2f" % (classes[labels_[i]], scores_[i]),
    #                 (int(x0), int(y0) - 16), 0, 2, [255, 0, 255], 5, lineType=cv2.LINE_AA)
    # # img_org = np.asarray(img_org, np.uint8)
    # # cv2.imwrite("find.jpg", img_org)
    # # img_org = cv2.resize(img_org, (900, 900))
    # cv2.namedWindow('Detection result', cv2.WND_PROP_FULLSCREEN)
    # cv2.imshow('Detection result', img)
    # print(end - start)
    # cv2.waitKey(0)
    #

