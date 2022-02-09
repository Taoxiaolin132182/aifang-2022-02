from django.http import HttpResponse
import os
import json
import tensorflow as tf
from datetime import datetime
from tensorflow.python.platform import gfile
import tensorflow.contrib.tensorrt
from logging_util import Logger
import cv2
import numpy as np

import copy
import time

# trt model infer
from tensorrt_utils import TensorrtClientDetect

#核心模型
model_detection_core = None
#羊毛项目单独检测中黄毛模型
model_detection_add = None
# atss trt 模型
model_atss_trt = None
isModelForward = False #模型是否正在初始化
model_config = None #配置文件
logger = None
labels = []
# labels_num = len(labels)


def infer(request):
    print("start infer", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    request.encoding = 'utf-8'

    imagePath = ""
    if request.POST:
        imagePath = request.POST['imagePath']
    elif request.GET:
        imagePath = request.GET['imagePath']
    if len(imagePath) <= 0:
        retObj = {"return_code": -80001000, "return_message": "缺少参数: imagePath"}
        return HttpResponse(json.dumps(retObj))
    retObj = {"return_code": 0, "return_message": "success"}
    try:
        poitList = doInfer(imagePath)
        retObj['data'] = poitList
    except Exception as e:
        print(e)
        retObj = {"return_code": 1, "return_message": str(e)}
    print("end infer", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    return HttpResponse(json.dumps(retObj))


#加载模型配置文件
def load_json(json_str):
    global model_config
    with open(json_str, 'rb') as f:
        model_config = json.load(f)
    model_config["class_names"] = list(model_config["class_name_score_factors"].keys())


#检测模型封装
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
#分类模型封装
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

# 推断入口
def doInfer(imagePath):
    global model_detection_core
    global model_detection_add
    global isModelForward
    global model_config
    global logger
    global model_atss_trt

    #配置文件路径修改
    if model_config is None:
        load_json("/mnt/data/data/aimodel/config.txt")
        # load_json("/mnt/data/zzb_test/aimodel/config.txt")
        #初始化日志，如果日志路径不存在，新建路径
        if not os.path.exists(model_config["log_save_dir"]):
            os.makedirs(model_config["log_save_dir"])
        logger = Logger(model_config["log_save_dir"])
        logger.clean_log_dir()
        logger.info_ai(meg="model_config:%s"%str(model_config))

    if isModelForward == False:
        if model_config["use_atss_trt"]:
            logger.info_ai(meg="use_atss_trt model infer")
            # 替换老的类别和阈值限定
            model_config["class_names"] = list(model_config["model_atss_trt_param"]["class_name_score_factors"].keys())
            model_config["class_name_score_factors"] = model_config["model_atss_trt_param"]["class_name_score_factors"]
            if os.path.exists(model_config["model_atss_trt_param"]["model_path"]):
                model_path = model_config["model_atss_trt_param"]["model_path"]
                input_size = model_config["model_atss_trt_param"]["image_size"]
                batch_size = model_config["model_atss_trt_param"]["batch_size"]
                iou_thresh = model_config["model_atss_trt_param"]["iou_thresh"]
                score_thresh = model_config["model_atss_trt_param"]["score_thresh"]
                class_num = len(model_config["class_names"])
                model_atss_trt = TensorrtClientDetect(model_path, input_size, batch_size, class_num, iou_thresh, score_thresh)
            else:
                logger.info_ai(meg="atss trt model path is not exist:%s" % model_config["model_atss_trt_param"]["model_path"])
        else:
            #初始化主要模型，棉花中的异纤、脏棉，羊毛中的异纤、深黄毛、草干
            if len(model_config["model_core_path"]) > 0:
                if os.path.exists(model_config["model_core_path"]):
                    model_detection_core = DetectionModelForward(model_config["model_core_path"])
                else:
                    logger.info_ai(meg="core detection model path is not exist:%s" % model_config["model_core_path"])
            if len(model_config["model_add_path"]) > 0:
                if os.path.exists(model_config["model_add_path"]):
                    model_detection_add = DetectionModelForward(model_config["model_add_path"])
                else:
                    logger.info_ai(meg="add detection model path is not exist:%s" % model_config["model_add_path"])

        isModelForward = True
    if model_config["use_atss_trt"]:
        return atssTrtModelInfer(model_atss_trt, imagePath)
    else:
        #传入模型进行推断
        return callAiModel(model_detection_core, model_detection_add, imagePath)


#加载配置文件
def load_labels(path):
    global labels
    labels = []
    for line in open(path).readlines():
        labels.append(line.split("\n")[0])
    print("labels_num = ",len(labels))
    global labels_num
    labels_num = len(labels)

#填充图片到矩形
def fill_new(image):
    ori_w, ori_h = image.shape[1], image.shape[0]
    new_size = max(ori_h, ori_w)
    new_img = np.zeros([new_size, new_size, 3], dtype=np.float32) #np.float32 np.uint8
    x0 = int((new_size - ori_w)/2)
    y0 = int((new_size - ori_h)/2)
    new_img[y0: y0+ori_h, x0:x0+ori_w, :] = image
    return new_img

#裁剪目标框到正确范围
def clamp_bboxs(boxs, img_size, to_remove=1):

    boxs[:, 0].clip(min=0, max=img_size[0] - to_remove)
    boxs[:, 1].clip(min=0, max=img_size[1] - to_remove)
    boxs[:, 2].clip(min=0, max=img_size[0] - to_remove)
    boxs[:, 3].clip(min=0, max=img_size[1] - to_remove)

    return boxs
#去掉背景信息
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

#在图片上画识别结果
def plot_one_box(img, coord, label=None, color=None, line_thickness=None):
    tl = line_thickness or int(round(0.002 * max(img.shape[0:2])))  # line thickness
    c1, c2 = (int(coord[0]), int(coord[1])), (int(coord[2]), int(coord[3]))
    cv2.rectangle(img, c1, c2, color, thickness=3)#thickness=tl
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=float(tl) / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.putText(img, label, (c1[0], c1[1] - 2), cv2.FONT_HERSHEY_COMPLEX, float(tl) / 3, color, thickness=3, lineType=cv2.LINE_AA)


#计算iou
def calc_iou(pred_boxes, true_boxes):
    '''
    Maintain an efficient way to calculate the ios matrix using the numpy broadcast tricks.
    shape_info: pred_boxes: [N, 4]
                true_boxes: [V, 4]
    return: IoU matrix: shape: [N, V]
    '''

    # [N, 1, 4]
    pred_boxes = np.expand_dims(pred_boxes, -2)
    # [1, V, 4]
    true_boxes = np.expand_dims(true_boxes, 0)

    # [N, 1, 2] & [1, V, 2] ==> [N, V, 2]
    intersect_mins = np.maximum(pred_boxes[..., :2], true_boxes[..., :2])
    intersect_maxs = np.minimum(pred_boxes[..., 2:], true_boxes[..., 2:])
    intersect_wh = np.maximum(intersect_maxs - intersect_mins, 0.)

    # shape: [N, V]
    intersect_area = intersect_wh[..., 0] * intersect_wh[..., 1]
    # shape: [N, 1, 2]
    pred_box_wh = pred_boxes[..., 2:] - pred_boxes[..., :2]
    pred_box_wh = pred_box_wh.clip(min=0, max=2000)
    # shape: [N, 1]
    pred_box_area = pred_box_wh[..., 0] * pred_box_wh[..., 1]
    # [1, V, 2]
    true_boxes_wh = true_boxes[..., 2:] - true_boxes[..., :2]
    # [1, V]
    true_boxes_area = true_boxes_wh[..., 0] * true_boxes_wh[..., 1]

    # shape: [N, V]
    iou = intersect_area / (pred_box_area + true_boxes_area - intersect_area + 1e-10)

    return iou


#推断入口
def callAiModel(model_detection_core, model_detection_add, imagePath, model_classify=None, labels_name=None):
    logger.info_ai(meg="**************************************get into callAiModel API**************************************", api_name="callAiModel", get_ins={"imagePath": imagePath})
    start_time = time.time()
    img_paths = imagePath.split(",")

    returnObjs = {}
    for img_path_id in range(len(img_paths)):
        start_read_img = time.time()
        try:
            image_path = img_paths[img_path_id]
            result = os.path.exists(image_path)
            file_size = 0
            if result:
                file_size = os.path.getsize(image_path)
            msg = "file exists %s , file_size = %s" % (result, file_size)
            logger.info_ai(meg=msg)
            img = cv2.imread(image_path)
            img_org = copy.deepcopy(img)
            img_upload = copy.deepcopy(img)
            #是否过滤背景区域
            # img = delete_background(img)
            logger.info_ai(meg="read image", api_name="cv2.imread",
                           get_ins={"img_path": img_paths[img_path_id]}, get_outs={"img.shape": img.shape})
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
        logger.info_ai(meg="read time:%f" % (end_read_img - start_read_img))
        start_detection_time = time.time()
        image_h, image_w, c = img.shape
        boxes_core, scores_core, labels_core = np.array([]), np.array([]), np.array([])
        if model_detection_core is not None:
            image_size = model_config["image_size_core"]
            img_detection = cv2.resize(img, tuple([image_size, image_size]))
            img_detection = img_detection[np.newaxis, :]
            boxes_core, scores_core, labels_core = model_detection_core.forward(img_detection, iou_thresh=0.1, score_thresh=0.05)
            boxes_core[:, 0] *= (float(image_w) / image_size)
            boxes_core[:, 2] *= (float(image_w) / image_size)
            boxes_core[:, 1] *= (float(image_h) / image_size)
            boxes_core[:, 3] *= (float(image_h) / image_size)
            # 如果识别出来目标，把目标裁剪到合理范围
            s = []
            if len(boxes_core) > 0:
                boxes_core = clamp_bboxs(boxes_core, [image_w, image_h], to_remove=1)
                w = boxes_core[:, 2] - boxes_core[:, 0]
                h = boxes_core[:, 3] - boxes_core[:, 1]
                s = w * h
            logger.info_ai(meg="do model core detection", api_name="model_detection_core.forward",
                           get_ins={"img_detection.shape": img_detection.shape},
                           get_outs={"boxes_core": boxes_core, "scores_core": scores_core, "labels_core": labels_core})

            boxes_core_temp = []
            scores_core_temp = []
            labels_core_temp = []
            for n, score in enumerate(scores_core.tolist()):
                if score >= model_config["class_name_score_factors"][model_config["class_names"][int(labels_core[n])]] and s[n] >= model_config["area_factor"]:
                    boxes_core_temp.append(boxes_core[n])
                    scores_core_temp.append(scores_core[n])
                    labels_core_temp.append(labels_core[n])
            boxes_core = np.array(boxes_core_temp)
            scores_core = np.array(scores_core_temp)
            labels_core = np.array(labels_core_temp)


            logger.info_ai(meg="do core model score filter", api_name="not api",
                           get_outs={"boxes_core": boxes_core, "scores_core": scores_core, "labels_core": labels_core})

            end_core_detection_time = time.time()
            logger.info_ai(meg="do model core detection time:%f" % (end_core_detection_time - start_detection_time))
            start_detection_time = end_core_detection_time


        if model_detection_add is not None:
            image_size = model_config["image_size_add"]
            img_detection = cv2.resize(img, tuple([image_size, image_size]))
            img_detection = img_detection[np.newaxis, :]
            boxes_add, scores_add, labels_add = model_detection_add.forward(img_detection, iou_thresh=0.1, score_thresh=0.05)
            boxes_add[:, 0] *= (float(image_w) / image_size)
            boxes_add[:, 2] *= (float(image_w) / image_size)
            boxes_add[:, 1] *= (float(image_h) / image_size)
            boxes_add[:, 3] *= (float(image_h) / image_size)
            # 如果识别出来目标，把目标裁剪到合理范围
            s = []
            if len(boxes_add) > 0:
                boxes_add = clamp_bboxs(boxes_add, [image_w, image_h], to_remove=1)
                w = boxes_add[:, 2] - boxes_add[:, 0]
                h = boxes_add[:, 3] - boxes_add[:, 1]
                s = w * h
            logger.info_ai(meg="do model add detection", api_name="model_detection_add.forward",
                           get_ins={"img_detection.shape": img_detection.shape},
                           get_outs={"boxes_add": boxes_add, "scores_add": scores_add, "labels_add": labels_add})
            end_add_detection_time = time.time()
            logger.info_ai(meg="do model add detection time:%f" % (end_add_detection_time - start_detection_time))

            boxes_add_temp = []
            scores_add_temp = []
            labels_add_temp = []

            for n, score in enumerate(scores_add.tolist()):
                if score >= model_config["class_name_score_factors"][model_config["class_names"][int(labels_add[n])]] and s[n] >= model_config["area_factor"]:
                    boxes_add_temp.append(boxes_add[n])
                    scores_add_temp.append(scores_add[n])
                    labels_add_temp.append(int(labels_add[n]))
            boxes_add = np.array(boxes_add_temp)
            scores_add = np.array(scores_add_temp)
            labels_add = np.array(labels_add_temp)


            logger.info_ai(meg="do add model score filter", api_name="not api",
                           get_outs={"boxes_add": boxes_add, "scores_add": scores_add, "labels_add": labels_add})
            #过滤掉已经识别出来的框
            if len(boxes_core) > 0 and len(boxes_add) > 0:
                iou_matrix = calc_iou(boxes_add, boxes_core)
                max_iou_idx = np.argmax(iou_matrix, axis=-1)
                max_iou = np.array([iou_matrix[idx][max_iou_idx[idx]] for idx in range(len(max_iou_idx))])
                reserve_ids = np.where(max_iou < 0.1)[0]
                #如果还有保留数据
                if len(reserve_ids) > 0:
                    boxes_add = boxes_add[reserve_ids]
                    scores_add = scores_add[reserve_ids]
                    labels_add = labels_add[reserve_ids]
                else:
                    boxes_add = np.array([])
                    scores_add = np.array([])
                    labels_add = np.array([])

                #如果两个模型结果都有, 两个模型结果进行合并
            if len(boxes_core) > 0 and len(boxes_add) > 0:
                boxes_core = np.concatenate([boxes_core, boxes_add], axis=0)
                scores_core = np.concatenate([scores_core, scores_add], axis=0)
                labels_core = np.concatenate([labels_core, labels_add], axis=0)
            elif len(boxes_core) == 0 and len(boxes_add) > 0:
                boxes_core = boxes_add
                scores_core = scores_add
                labels_core = labels_add
            else:
                pass



        boxes_core = np.asarray(boxes_core, np.int32)
        boxes_return = boxes_core.tolist()
        scores_return = scores_core.tolist()
        labels_return = labels_core.tolist()
        labels_return = [model_config["class_names"][int(class_id)] for class_id in labels_return]


        #记录过滤前数据
        logger.info_ai(meg="result before score filter ", api_name="not api",
                       get_outs={"boxes_return": boxes_return, "scores_return": scores_return, "labels_return": labels_return})
        # #进行过滤
        # for n, score in enumerate(scores_list):
        #     if score >= model_config["class_name_score_factors"][model_config["class_names"][int(labels_list[n])]] and s[n] >= model_config["area_factor"]:
        #         boxes_return.append(boxes_list[n])
        #         scores_return.append(scores_list[n])
        #         labels_return.append(model_config["class_names"][int(labels_list[n])])

        if model_config["zangmian_score_factor"] > 0:
            labels_temp = []
            for label_id in range(len(labels_return)):
                if labels_return[label_id] == "zangmian" and scores_return[label_id] >= model_config["zangmian_score_factor"]:
                    labels_temp.append("zangmian")
                else:
                    labels_temp.append("yixian")
            labels_return = labels_temp

        #记录过滤后数据
        logger.info_ai(meg="result after score filter ", api_name="not api",
                       get_outs={"boxes_return": boxes_return, "scores_return": scores_return, "labels_return": labels_return})

        #根据配置文件决定是否要把结果画在图片上并保存
        if model_config["save_result"] > 0:
            save_result_start = time.time()
            for j in range(len(boxes_return)):
                label_, score_, x_min, y_min, x_max, y_max = labels_return[j], scores_return[j], boxes_return[j][0], boxes_return[j][1], boxes_return[j][2], boxes_return[j][3]
                plot_one_box(img_org, [x_min, y_min, x_max, y_max], label=str(label_) + "|" + str(score_))

            path_ = imagePath.split("/")[-1]
            subdir = datetime.strftime(datetime.now(), '%Y%m%d-%H_%M_%S')
            date_path1 = time.strftime("%Y_%m%d", time.localtime())
            date_path2 = "ty1_arm1_" + date_path1
            if not os.path.exists("/mnt/data/data/image/"):
                os.makedirs("/mnt/data/data/image/")
            if not os.path.exists("/mnt/data/data/image/havebox/"):
                os.makedirs("/mnt/data/data/image/havebox/")
            if not os.path.exists("/mnt/data/data/image/nobox/"):
                os.makedirs("/mnt/data/data/image/nobox/")
            if not os.path.exists("/mnt/data/data/upload_image/"):
                os.makedirs("/mnt/data/data/upload_image/")

            havebox_path = "/mnt/data/data/image/havebox/" + date_path1
            nobox_path = "/mnt/data/data/image/nobox/" + date_path1
            upload_path = "/mnt/data/data/upload_image/" + date_path2
            path = subdir + ".jpg"
            if not os.path.exists(nobox_path):
                os.makedirs(nobox_path)
            if not os.path.exists(havebox_path):
                os.makedirs(havebox_path)
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
            if len(boxes_return):
                cv2.imwrite(os.path.join(havebox_path, path_), img_org)
                cv2.imwrite(os.path.join(upload_path, path_), img_upload)
            else:
                cv2.imwrite(os.path.join(nobox_path, path_), img_org)

            save_result_end = time.time()
            logger.info_ai(meg="save result data time:%f" % (save_result_end - save_result_start))

        returnObj = {}
        returnObj['boxes'] = boxes_return
        returnObj['scores'] = scores_return
        returnObj['labels'] = labels_return
        returnObj['class_scores'] = []
        returnObj['img_exist'] = 1
        returnObjs[str(img_path_id)] = returnObj
    end_time = time.time()
    logger.info_ai(meg="all time:%f" % (end_time - start_time))
    logger.info_ai(meg="**************************************return end**************************************", api_name="not api", get_outs=returnObjs)
    return returnObjs
# end callAiModel()


# atss trt infer
def atssTrtModelInfer(model_atss_trt, imagePath):
    logger.info_ai(
        meg="**************************************atssTrtModelInfer API**************************************",
        api_name="atssTrtModelInfer", get_ins={"imagePath": imagePath})
    start_time = time.time()
    img_paths = imagePath.split(",")

    returnObjs = {}
    for img_path_id in range(len(img_paths)):
        start_read_img = time.time()
        try:
            image_path = img_paths[img_path_id]
            result = os.path.exists(image_path)
            file_size = 0
            if result:
                file_size = os.path.getsize(image_path)
            msg = "file exists %s , file_size = %s" % (result, file_size)
            logger.info_ai(meg=msg)
            img = cv2.imread(image_path)
            # img_org = copy.deepcopy(img)
            # img_upload = copy.deepcopy(img)
            # 是否过滤背景区域
            # img = delete_background(img)
            logger.info_ai(meg="read image", api_name="cv2.imread",
                           get_ins={"img_path": img_paths[img_path_id]}, get_outs={"img.shape": img.shape})
            # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except:
            returnObj = {}
            returnObj['boxes'] = []
            returnObj['scores'] = []
            returnObj['labels'] = []
            returnObj['class_scores'] = []
            returnObj['img_exist'] = 0
            return returnObj
        end_read_img = time.time()
        logger.info_ai(meg="read time:%f" % (end_read_img - start_read_img))
        start_detection_time = time.time()
        getData = model_atss_trt.inference(img)
        end_add_detection_time = time.time()
        logger.info_ai(meg="do model_atss_trt detection time:%f" % (end_add_detection_time - start_detection_time))
        boxes_r = getData['boxes']
        scores_r = getData['scores']
        labels_r = getData['labels']
        s = getData['s']

        boxes_add_temp = []
        scores_add_temp = []
        labels_add_temp = []
        # 过滤低于该类别限定阈值的box
        for n, score in enumerate(scores_r):
            if score >= model_config["class_name_score_factors"][model_config["class_names"][int(labels_r[n])]] and s[
                n] >= model_config["area_factor"]:
                boxes_add_temp.append(boxes_r[n])
                scores_add_temp.append(scores_r[n])
                labels_add_temp.append(int(labels_r[n]))

        boxes_return = boxes_add_temp
        scores_return = scores_add_temp
        labels_return = labels_add_temp
        labels_return = [model_config["class_names"][int(class_id)] for class_id in labels_return]

        returnObj = {}
        returnObj['boxes'] = boxes_return
        returnObj['scores'] = scores_return
        returnObj['labels'] = labels_return
        returnObj['class_scores'] = []
        returnObj['img_exist'] = 1
        returnObjs[str(img_path_id)] = returnObj

    end_time = time.time()
    logger.info_ai(meg="all time:%f" % (end_time - start_time))
    logger.info_ai(meg="**************************************return end**************************************",
                   api_name="not api", get_outs=returnObjs)
    return returnObjs