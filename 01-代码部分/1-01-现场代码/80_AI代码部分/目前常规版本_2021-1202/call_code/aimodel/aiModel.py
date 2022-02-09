import os
from tritonserver_utils import TritonClient
from aimodel.modelInfer import *
import numpy as np
from aimodel.anchor import *
from tritonclient_new import TritonClientNew
from tritonclient_new import inputDataProcess
from fluorescence.fluorescence_detection import fluorescence_detection


class model_detection_core:
    def __init__(self, model_config):
        self.model_config = model_config
        url = 'localhost:%d' % self.model_config["trtServerModelParam"]["grpc_port"]
        model_name = model_config["model_detection_core"]["model_name"]
        if model_config["model_detection_core"]["shared_memory"]:
            self.model_detection_core = TritonClient(model_name, url=url, shared_memory=False)
        else:
            self.model_detection_core = TritonClient(model_name, url=url, shared_memory=False)

        img_gj_ori = np.zeros((1, model_config["model_detection_core"]["image_input_size"][1],
                               model_config["model_detection_core"]["image_input_size"][0], 3),
                              dtype=np.float32)
        _ = self.model_detection_core.inference(img_gj_ori)

    def aiInfer(self, oriimg, img, img_name):
        image_h, image_w, c = oriimg.shape
        # 棉花项目：需要将yixian阈值乘以10, 然后做成一类的nms, 羊毛则不需要
        if self.model_config["project_name"] == "cotton":
            # boxes_core, scores_core, labels_core = do_detection_common_(model_detection_core, img,
            #                                                            len(model_config["class_names"]),
            #                                                            model_config["model_detection_core"][
            #                                                                "image_input_size"],
            #                                                            model_config["model_detection_core"][
            #                                                                "iou_thresh"],
            #                                                            model_config["model_detection_core"][
            #                                                                "score_thresh"])
            boxes_core, scores_core, labels_core = do_detection_common_nodata_process(self.model_detection_core, oriimg,
                                                                                      img,
                                                                                      len(self.model_config[
                                                                                              "class_names"]),
                                                                                      self.model_config[
                                                                                          "model_detection_core"][
                                                                                          "image_input_size"],
                                                                                      self.model_config[
                                                                                          "model_detection_core"][
                                                                                          "iou_thresh"],
                                                                                      self.model_config[
                                                                                          "model_detection_core"][
                                                                                          "score_thresh"])
        else:
            boxes_core, scores_core, labels_core = do_detection_common(self.model_detection_core, img,
                                                                       len(self.model_config["class_names"]),
                                                                       self.model_config["model_detection_core"][
                                                                           "image_input_size"],
                                                                       self.model_config["model_detection_core"][
                                                                           "iou_thresh"],
                                                                       self.model_config["model_detection_core"][
                                                                           "score_thresh"])

        # 如果识别出来目标，把目标裁剪到合理范围
        s = []
        if len(boxes_core) > 0:
            boxes_core = clamp_bboxs(boxes_core, [image_w, image_h], to_remove=1)
            w = boxes_core[:, 2] - boxes_core[:, 0]
            h = boxes_core[:, 3] - boxes_core[:, 1]
            s = w * h

        boxes_core_temp = []
        scores_core_temp = []
        labels_core_temp = []
        for n, score in enumerate(scores_core.tolist()):
            if score >= self.model_config["class_name_score_factors"][
                self.model_config["class_names"][int(labels_core[n])]] and s[n] >= self.model_config["area_factor"]:
                boxes_core_temp.append(boxes_core[n])
                scores_core_temp.append(scores_core[n])
                labels_core_temp.append(labels_core[n])
        boxes_core = np.array(boxes_core_temp)
        scores_core = np.array(scores_core_temp)
        labels_core = np.array(labels_core_temp)

        boxes_core = np.asarray(boxes_core, np.int32)
        boxes_return = boxes_core.tolist()
        scores_return = scores_core.tolist()
        labels_return = labels_core.tolist()
        labels_return = [self.model_config["class_names"][int(class_id)] for class_id in labels_return]

        # #进行过滤
        # for n, score in enumerate(scores_list):
        #     if score >= model_config["class_name_score_factors"][model_config["class_names"][int(labels_list[n])]] and s[n] >= model_config["area_factor"]:
        #         boxes_return.append(boxes_list[n])
        #         scores_return.append(scores_list[n])
        #         labels_return.append(model_config["class_names"][int(labels_list[n])])

        if self.model_config["zangmian_score_factor"] > 0:
            labels_temp = []
            for label_id in range(len(labels_return)):
                if labels_return[label_id] == "zangmian" and scores_return[label_id] >= self.model_config[
                    "zangmian_score_factor"]:
                    labels_temp.append("zangmian")
                else:
                    labels_temp.append("yixian")
            labels_return = labels_temp

        returnObj = {}
        returnObj['boxes'] = boxes_return
        returnObj['scores'] = scores_return
        returnObj['labels'] = labels_return
        returnObj['img_name'] = img_name

        return returnObj

# 棉花、羊绒单模型
class model_atss_detection:
    def __init__(self, model_config):
        self.model_config = model_config
        url = 'localhost:%d' % self.model_config["trtServerModelParam"]["grpc_port"]
        model_name = model_config["model_atss_detection"]["model_name"]
        # old tritonserver init
        # if model_config["model_atss_detection"]["shared_memory"]:
        #     self.model_atss_detection = TritonClient(model_name, url=url, shared_memory=False)
        # else:
        #     self.model_atss_detection = TritonClient(model_name, url=url, shared_memory=False)

        # new tritonserver init
        input_names = 'input_data'
        output_names = ['logits', 'bbox_reg', 'centerness']
        self.model_atss_detection = TritonClientNew(model_name, input_names, output_names, url=url)
        img_gj_ori = np.zeros((1, 3, model_config["model_atss_detection"]["image_input_size"][1],
                               model_config["model_atss_detection"]["image_input_size"][0]),
                              dtype=np.float32)
        # old infer
        # _ = self.model_atss_detection.inference(img_gj_ori)
        # new infer
        inputs = inputDataProcess(img_gj_ori, input_names)
        _ = self.model_atss_detection.inferenceNew(inputs)

        # 预anchor的尺寸
        anchor_strides = [8, 16, 32, 64, 128]
        # anchor_scale = [8]
        anchor_scale = [2]
        # 根据模型尺寸来的, 1280/32 = 40  1024/32 = 32
        neck_shapes = [[160, 160], [80, 80], [40, 40], [20, 20], [10, 10]]
        self.anchors = prepare_anchors(neck_shapes, anchor_strides, anchor_scale)
        self.anchors = torch.cat(self.anchors, dim=0)

    def aiInfer(self, oriimg, img, img_name):
        image_h, image_w, c = oriimg.shape
        boxes_core, scores_core, labels_core = atssDetectionInferCommonNoDataProcess(self.model_atss_detection, oriimg,
                                                                                     img, self.anchors,
                                                                                     len(self.model_config[
                                                                                             "class_names"]),
                                                                                     self.model_config[
                                                                                         "model_detection_core"][
                                                                                         "image_input_size"],
                                                                                     self.model_config[
                                                                                         "model_detection_core"][
                                                                                         "iou_thresh"],
                                                                                     self.model_config[
                                                                                         "model_detection_core"][
                                                                                         "score_thresh"])

        # 如果识别出来目标，把目标裁剪到合理范围
        s = []
        if len(boxes_core) > 0:
            boxes_core = clamp_bboxs(boxes_core, [image_w, image_h], to_remove=1)
            w = boxes_core[:, 2] - boxes_core[:, 0]
            h = boxes_core[:, 3] - boxes_core[:, 1]
            s = w * h

        boxes_core_temp = []
        scores_core_temp = []
        labels_core_temp = []
        for n, score in enumerate(scores_core.tolist()):
            if score >= self.model_config["class_name_score_factors"][
                self.model_config["class_names"][int(labels_core[n])]] and s[n] >= self.model_config["area_factor"]:
                boxes_core_temp.append(boxes_core[n])
                scores_core_temp.append(scores_core[n])
                labels_core_temp.append(labels_core[n])
        boxes_core = np.array(boxes_core_temp)
        scores_core = np.array(scores_core_temp)
        labels_core = np.array(labels_core_temp)

        boxes_core = np.asarray(boxes_core, np.int32)
        boxes_return = boxes_core.tolist()
        scores_return = scores_core.tolist()
        labels_return = labels_core.tolist()
        labels_return = [self.model_config["class_names"][int(class_id)] for class_id in labels_return]

        # #进行过滤
        # for n, score in enumerate(scores_list):
        #     if score >= model_config["class_name_score_factors"][model_config["class_names"][int(labels_list[n])]] and s[n] >= model_config["area_factor"]:
        #         boxes_return.append(boxes_list[n])
        #         scores_return.append(scores_list[n])
        #         labels_return.append(model_config["class_names"][int(labels_list[n])])

        if self.model_config["zangmian_score_factor"] > 0:
            labels_temp = []
            for label_id in range(len(labels_return)):
                if labels_return[label_id] == "zangmian" and scores_return[label_id] >= self.model_config[
                    "zangmian_score_factor"]:
                    labels_temp.append("zangmian")
                else:
                    labels_temp.append("yixian")
            labels_return = labels_temp

        returnObj = {}
        returnObj['boxes'] = boxes_return
        returnObj['scores'] = scores_return
        returnObj['labels'] = labels_return
        returnObj['img_name'] = img_name

        return returnObj


# 陈红的羊毛双模型
class model_detection_wool_double:
    def __init__(self, model_config):
        self.model_config = model_config
        # one model (yixian shenhuangmao)
        url = 'localhost:%d' % self.model_config["trtServerModelParam"]["grpc_port"]
        model_name = model_config["model_detection_core"]["model_name"]
        if model_config["model_detection_core"]["shared_memory"]:
            self.model_detection_core = TritonClient(model_name, url=url, shared_memory=False)
        else:
            self.model_detection_core = TritonClient(model_name, url=url, shared_memory=False)

        img_gj_ori = np.zeros((1, model_config["model_detection_core"]["image_input_size"][1],
                               model_config["model_detection_core"]["image_input_size"][0], 3),
                              dtype=np.float32)
        _ = self.model_detection_core.inference(img_gj_ori)
        # two model (zhonghuangmao)
        url = 'localhost:%d' % self.model_config["trtServerModelParam"]["grpc_port"]
        model_name = model_config["model_detection_add"]["model_name"]
        if model_config["model_detection_add"]["shared_memory"]:
            self.model_detection_add = TritonClient(model_name, url=url, shared_memory=False)
        else:
            self.model_detection_add = TritonClient(model_name, url=url, shared_memory=False)

        img_gj_ori = np.zeros((1, model_config["model_detection_add"]["image_input_size"][1],
                               model_config["model_detection_add"]["image_input_size"][0], 3),
                              dtype=np.float32)
        _ = self.model_detection_add.inference(img_gj_ori)

    def aiInfer(self, oriimg, img, img_name):
        image_h, image_w, c = oriimg.shape
        inferImg = cv2.cvtColor(oriimg, cv2.COLOR_BGR2RGB)
        # 第一个模型
        # 传入原始图片进行infer
        boxes_core, scores_core, labels_core = do_detection_common(self.model_detection_core, inferImg,
                                                                   len(self.model_config["class_names"]),
                                                                   self.model_config["model_detection_core"][
                                                                       "image_input_size"],
                                                                   self.model_config["model_detection_core"][
                                                                       "iou_thresh"],
                                                                   self.model_config["model_detection_core"][
                                                                       "score_thresh"])

        # 如果识别出来目标，把目标裁剪到合理范围
        s = []
        if len(boxes_core) > 0:
            boxes_core = clamp_bboxs(boxes_core, [image_w, image_h], to_remove=1)
            w = boxes_core[:, 2] - boxes_core[:, 0]
            h = boxes_core[:, 3] - boxes_core[:, 1]
            s = w * h

        boxes_core_temp = []
        scores_core_temp = []
        labels_core_temp = []
        for n, score in enumerate(scores_core.tolist()):
            if score >= self.model_config["class_name_score_factors"][
                self.model_config["class_names"][int(labels_core[n])]] and s[n] >= self.model_config["area_factor"]:
                boxes_core_temp.append(boxes_core[n])
                scores_core_temp.append(scores_core[n])
                labels_core_temp.append(labels_core[n])
        boxes_core = np.array(boxes_core_temp)
        scores_core = np.array(scores_core_temp)
        labels_core = np.array(labels_core_temp)

        # 第二个模型
        boxes_add, scores_add, labels_add = do_detection_common(self.model_detection_add, inferImg,
                                                                len(self.model_config["class_names"]),
                                                                self.model_config["model_detection_add"][
                                                                    "image_input_size"],
                                                                self.model_config["model_detection_add"][
                                                                    "iou_thresh"],
                                                                self.model_config["model_detection_add"][
                                                                    "score_thresh"])
        # 如果识别出来目标，把目标裁剪到合理范围
        s = []
        if len(boxes_add) > 0:
            boxes_add = clamp_bboxs(boxes_add, [image_w, image_h], to_remove=1)
            w = boxes_add[:, 2] - boxes_add[:, 0]
            h = boxes_add[:, 3] - boxes_add[:, 1]
            s = w * h

        boxes_add_temp = []
        scores_add_temp = []
        labels_add_temp = []

        for n, score in enumerate(scores_add.tolist()):
            if score >= self.model_config["class_name_score_factors"][
                self.model_config["class_names"][int(labels_add[n])]] and s[n] >= self.model_config["area_factor"]:
                boxes_add_temp.append(boxes_add[n])
                scores_add_temp.append(scores_add[n])
                labels_add_temp.append(int(labels_add[n]))
        boxes_add = np.array(boxes_add_temp)
        scores_add = np.array(scores_add_temp)
        labels_add = np.array(labels_add_temp)

        # 过滤掉已经识别出来的框
        if len(boxes_core) > 0 and len(boxes_add) > 0:
            iou_matrix = calc_iou(boxes_add, boxes_core)
            max_iou_idx = np.argmax(iou_matrix, axis=-1)
            max_iou = np.array([iou_matrix[idx][max_iou_idx[idx]] for idx in range(len(max_iou_idx))])
            reserve_ids = np.where(max_iou < 0.1)[0]
            # 如果还有保留数据
            if len(reserve_ids) > 0:
                boxes_add = boxes_add[reserve_ids]
                scores_add = scores_add[reserve_ids]
                labels_add = labels_add[reserve_ids]
            else:
                boxes_add = np.array([])
                scores_add = np.array([])
                labels_add = np.array([])

        # 如果两个模型结果都有, 两个模型结果进行合并
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
        labels_return = [self.model_config["class_names"][int(class_id)] for class_id in labels_return]

        # #进行过滤
        # for n, score in enumerate(scores_list):
        #     if score >= model_config["class_name_score_factors"][model_config["class_names"][int(labels_list[n])]] and s[n] >= model_config["area_factor"]:
        #         boxes_return.append(boxes_list[n])
        #         scores_return.append(scores_list[n])
        #         labels_return.append(model_config["class_names"][int(labels_list[n])])

        if self.model_config["zangmian_score_factor"] > 0:
            labels_temp = []
            for label_id in range(len(labels_return)):
                if labels_return[label_id] == "zangmian" and scores_return[label_id] >= self.model_config[
                    "zangmian_score_factor"]:
                    labels_temp.append("zangmian")
                else:
                    labels_temp.append("yixian")
            labels_return = labels_temp

        returnObj = {}
        returnObj['boxes'] = boxes_return
        returnObj['scores'] = scores_return
        returnObj['labels'] = labels_return
        returnObj['img_name'] = img_name

        return returnObj


# 羊毛的单模型
class model_detection_wool_single:
    def __init__(self, model_config):
        self.model_config = model_config
        url = 'localhost:%d' % self.model_config["trtServerModelParam"]["grpc_port"]
        model_name = model_config["model_detection_core"]["model_name"]
        if model_config["model_detection_core"]["shared_memory"]:
            self.model_detection_core = TritonClient(model_name, url=url, shared_memory=True)
        else:
            self.model_detection_core = TritonClient(model_name, url=url, shared_memory=False)

        img_gj_ori = np.zeros((1, model_config["model_detection_core"]["image_input_size"][1],
                               model_config["model_detection_core"]["image_input_size"][0], 3),
                              dtype=np.float32)
        _ = self.model_detection_core.inference(img_gj_ori)

    def aiInfer(self, oriimg, img, img_name):
        image_h, image_w, c = oriimg.shape
        inferImg = cv2.cvtColor(oriimg, cv2.COLOR_BGR2RGB)
        boxes_core, scores_core, labels_core = do_detection_common(self.model_detection_core, inferImg,
                                                                   len(self.model_config["class_names"]),
                                                                   self.model_config["model_detection_core"][
                                                                       "image_input_size"],
                                                                   self.model_config["model_detection_core"][
                                                                       "iou_thresh"],
                                                                   self.model_config["model_detection_core"][
                                                                       "score_thresh"])

        # 如果识别出来目标，把目标裁剪到合理范围
        s = []
        if len(boxes_core) > 0:
            boxes_core = clamp_bboxs(boxes_core, [image_w, image_h], to_remove=1)
            w = boxes_core[:, 2] - boxes_core[:, 0]
            h = boxes_core[:, 3] - boxes_core[:, 1]
            s = w * h

        boxes_core_temp = []
        scores_core_temp = []
        labels_core_temp = []
        for n, score in enumerate(scores_core.tolist()):
            if score >= self.model_config["class_name_score_factors"][
                self.model_config["class_names"][int(labels_core[n])]] and s[n] >= self.model_config["area_factor"]:
                boxes_core_temp.append(boxes_core[n])
                scores_core_temp.append(scores_core[n])
                labels_core_temp.append(labels_core[n])
        boxes_core = np.array(boxes_core_temp)
        scores_core = np.array(scores_core_temp)
        labels_core = np.array(labels_core_temp)

        boxes_core = np.asarray(boxes_core, np.int32)
        boxes_return = boxes_core.tolist()
        scores_return = scores_core.tolist()
        labels_return = labels_core.tolist()
        labels_return = [self.model_config["class_names"][int(class_id)] for class_id in labels_return]
        returnObj = {}
        returnObj['boxes'] = boxes_return
        returnObj['scores'] = scores_return
        returnObj['labels'] = labels_return
        returnObj['img_name'] = img_name

        return returnObj


# 荧光检测模型
class fluorescence_model:
    def __init__(self):
        self.model = fluorescence_detection()

    def detect(self, img_ori, img_name, bin_thre):
        boxes_return = self.model.detect(img_ori, bin_thre)
        box_num = len(boxes_return)
        scores_return = [1.0 for i in range(box_num)]
        # 暂时荧光检测的全是yixian
        labels_return = ["yixian" for i in range(box_num)]
        returnObj = {}
        returnObj['boxes'] = boxes_return
        returnObj['scores'] = scores_return
        returnObj['labels'] = labels_return
        returnObj['img_name'] = img_name
        return returnObj
