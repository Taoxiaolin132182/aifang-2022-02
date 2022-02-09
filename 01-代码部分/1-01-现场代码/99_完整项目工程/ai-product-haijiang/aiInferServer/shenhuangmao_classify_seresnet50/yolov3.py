from __future__ import division, print_function
import tensorflow as tf
import numpy as np
import cv2
from shenhuangmao_classify_seresnet50.utils.nms_utils import gpu_nms_one_class
from shenhuangmao_classify_seresnet50.model import yolov3_trt
import os
from shenhuangmao_classify_seresnet50.yolov3_classfition_model import yolov3 as yolov3_classfy
# import tqdm


class wool_detection:
    def __init__(self, model_path_detection, class_name_path_detection, model_path_classify, class_name_path_classify,
                 do_classify):
        self.model_path_detection = model_path_detection
        self.model_path_classify = model_path_classify
        self.do_classify = do_classify
        self.score_thresh_detection = 0.05
        self.score_thresh_classify = 0.01
        self.class_name_detection, self.name2id_classify = self.get_class_name(class_name_path_detection)
        self.num_class_detection = len(self.class_name_detection)
        if do_classify:
            self.class_name_classify, self.name2id_classify = self.get_class_name(class_name_path_classify)
            self.num_class_classify = len(self.class_name_classify)
        self.new_size_detection = [1024, 1024]  # w,h #1440x1400==1560x1560<1280x1280
        self.new_size_classify = [320, 320]
        self.anchors_detection = np.reshape(
            np.array([15, 15, 35, 35, 55, 55, 80, 80, 110, 110, 140, 140, 180, 180, 230, 230, 300, 300],
                     dtype=np.float32), [-1, 2]) * 1.0
        # self.anchors_detection = np.reshape(np.array([13,13, 23,23, 36,36, 50,50, 70,70, 90, 90, 187, 103, 103, 187, 140, 140],
        #             dtype=np.float32), [-1, 2]) * 2.5

        self.sess_detection = None
        self.sess_classify = None

    def get_class_name(self, class_name_path):
        class_name = []
        for line in open(class_name_path, "r").readlines():
            class_name.append(line.split("\n")[0].split(",")[0].split(" ")[0])
        name2id = {}
        name2texture = {}
        textures = ["metal", "plastic01", "plastic02", "other"]
        name2color = {}
        color = ["black", "white", "silver", "other"]
        id = 0
        for line in open(class_name_path, "r").readlines():
            for name in line.split("\n")[0].split(",")[0].split(" "):
                name2id[name] = id
                if len(line.split("\n")[0].split(",")) > 2:
                    name2texture_id = textures.index(line.split("\n")[0].split(",")[1])
                    name2color_id = color.index(line.split("\n")[0].split(",")[2])
                    name2texture[name] = name2texture_id
                    name2color[name] = name2color_id
            id = id + 1
        return class_name, name2id

    def model_init_detection(self):
        self.gpu_options_detection = tf.GPUOptions(per_process_gpu_memory_fraction=0.50)
        self.graph_detection = tf.Graph()
        with self.graph_detection.as_default():
            self.input_data_detection = tf.placeholder(tf.float32,
                                                       [1, self.new_size_detection[1], self.new_size_detection[0],
                                                        3], name='input_data')
            self.input_data_detection_fp32 = tf.cast(self.input_data_detection, tf.float32) / 255.
            yolo_model = yolov3_trt(self.num_class_detection, self.anchors_detection)
            with tf.variable_scope('yolov3'):
                pred_feature_maps = yolo_model.forward(self.input_data_detection_fp32, False)
            pred_boxes, pred_confs, pred_probs = yolo_model.predict(pred_feature_maps)
            pred_scores = pred_confs * pred_probs
            # pred_scores = pred_confs
            self.boxes_combine_detection, self.scores_combine_detection, self.labels_combine_detection = gpu_nms_one_class(
                pred_boxes, pred_scores, self.num_class_detection,
                max_boxes=50, score_thresh=self.score_thresh_detection,
                nms_thresh=0.1)
            #
            # self.boxes_combine_detection, self.scores_combine_detection, self.labels_combine_detection = gpu_nms(
            #     pred_boxes, pred_scores, self.num_class_detection,
            #     max_boxes=50, score_thresh=self.score_thresh_detection,
            #     nms_thresh=0.1)

            saver_detection = tf.train.Saver(
                var_list=tf.contrib.framework.get_variables_to_restore(include=["yolov3"]))
        self.sess_detection = tf.Session(graph=self.graph_detection,
                                         config=tf.ConfigProto(gpu_options=self.gpu_options_detection))
        saver_detection.restore(self.sess_detection, self.model_path_detection)
        return True

    def model_init_classify(self):

        self.gpu_options_classify = tf.GPUOptions(per_process_gpu_memory_fraction=0.50)
        self.graph_classify = tf.Graph()
        with self.graph_classify.as_default():
            self.input_data_classify = tf.placeholder(tf.float32,
                                                      [1, self.new_size_classify[1], self.new_size_classify[0], 3],
                                                      name='input_data')
            self.input_data_classify_fp32 = tf.cast(self.input_data_classify, tf.float32) / 255.
            yolo_model_classfy = yolov3_classfy(self.num_class_classify)
            with tf.variable_scope('yolov3_classfication'):
                logits, center_feature = yolo_model_classfy.forward(self.input_data_classify_fp32,
                                                                    is_training=False)
            logits = tf.squeeze(logits)
            scores = tf.nn.softmax(logits)
            self.labels_classify = tf.squeeze(tf.argmax(scores, axis=0))
            self.score_classify = tf.gather(scores, self.labels_classify)
            saver_classify = tf.train.Saver(
                var_list=tf.contrib.framework.get_variables_to_restore(include=["yolov3_classfication"]))
        self.sess_classify = tf.Session(graph=self.graph_classify,
                                        config=tf.ConfigProto(gpu_options=self.gpu_options_classify))
        saver_classify.restore(self.sess_classify, self.model_path_classify)
        return True

    def clamp_bboxs(self, boxes, img_size, to_remove=1):
        boxes[:, 0] = boxes[:, 0].clip(min=0, max=img_size[0] - to_remove)
        boxes[:, 1] = boxes[:, 1].clip(min=0, max=img_size[1] - to_remove)
        boxes[:, 2] = boxes[:, 2].clip(min=0, max=img_size[0] - to_remove)
        boxes[:, 3] = boxes[:, 3].clip(min=0, max=img_size[1] - to_remove)

        return boxes

    def fill_new(self, image):
        ori_w, ori_h = image.shape[1], image.shape[0]
        new_size = max(ori_h, ori_w)
        new_img = np.zeros([new_size, new_size, 3], dtype=np.float32)  # np.float32 np.uint8
        x0 = int((new_size - ori_w) / 2)
        y0 = int((new_size - ori_h) / 2)
        new_img[y0: y0 + ori_h, x0:x0 + ori_w, :] = image
        return new_img

    def forward(self, img_ori, do_classify=False):
        height_ori, width_ori = img_ori.shape[:2]
        img_ori = cv2.cvtColor(img_ori, cv2.COLOR_BGR2RGB)
        img_detection = cv2.resize(img_ori, tuple(self.new_size_detection))
        img_detection = img_detection[np.newaxis, :]
        boxes_detection, scores_detection, labels_detection = self.sess_detection.run(
            [self.boxes_combine_detection, self.scores_combine_detection, self.labels_combine_detection],
            feed_dict={self.input_data_detection: img_detection})

        boxes_detection[:, 0] *= (width_ori / float(self.new_size_detection[0]))
        boxes_detection[:, 2] *= (width_ori / float(self.new_size_detection[0]))
        boxes_detection[:, 1] *= (height_ori / float(self.new_size_detection[1]))
        boxes_detection[:, 3] *= (height_ori / float(self.new_size_detection[1]))

        boxes_detection = self.clamp_bboxs(boxes_detection, [width_ori, height_ori])

        labels_detection_name = []
        for label in labels_detection:
            labels_detection_name.append(self.class_name_detection[label])
        labels_detection_name = np.array(labels_detection_name)

        if not do_classify:
            return boxes_detection, scores_detection, labels_detection_name, scores_detection, labels_detection_name

        labels_classify = []
        scores_classify = []

        for box in boxes_detection:
            x0, y0, x1, y1 = box
            img_cut = img_ori[int(y0): int(y1), int(x0): int(x1), :]
            img_cut = self.fill_new(img_cut)
            img_cut = cv2.resize(img_cut, tuple(self.new_size_classify))
            img_classify = img_cut[np.newaxis, :]
            score_classify, label_classify = self.sess_classify.run([self.score_classify, self.labels_classify],
                                                                    feed_dict={self.input_data_classify: img_classify})
            scores_classify.append(score_classify)
            labels_classify.append(label_classify)
        labels_nms_threshold = [0.5 for i in range(self.num_class_classify)]

        if len(boxes_detection) > 0:
            labels_classify = np.array(labels_classify)
            scores_classify = np.asarray(scores_classify)
            boxes_detection, scores_detection, labels_classify, scores_classify = nms_cpu(boxes_detection,
                                                                                          scores_detection,
                                                                                          labels_classify,
                                                                                          scores_classify,
                                                                                          labels_nms_threshold,
                                                                                          num_classes=self.num_class_classify)

            labels_classify = labels_classify.tolist()
            scores_classify = scores_classify.tolist()
        labels_classify_name = []
        for label in labels_classify:
            labels_classify_name.append(self.class_name_classify[label])

        scores_classify = np.array(scores_classify)

        labels_classify_name = np.array(labels_classify_name)

        return boxes_detection, scores_detection, labels_detection_name, scores_classify, labels_classify_name


#
# if __name__ == '__main__':
#     imagessourse="V:/zzb_wool/ty1_arm1_2020_1229"
#
#     imagescode_path = "E:/"
#     model_path_detection = os.path.join(imagescode_path,
#                                         "ai_model_ckpt/wool/20201223_woo_v2.0/shenhuangmao/model-epoch_21_step_85100_loss_ 7.3168_lr_ 7.8125e-08")
#     model_path_classify = os.path.join(imagescode_path,
#                                        "ai_model_ckpt/wool/20201126_wool_v1.4/classify_model/20201201_cotton_darknet_plus_10.ckpt")
#     class_name_path_detection = os.path.join(imagescode_path,
#                                              "ai_model_ckpt/wool/20201126_wool_v1.4/20201107_wool_class.txt")
#     class_name_path_classify = os.path.join(imagescode_path,
#                                             "ai_model_ckpt/wool/20201126_wool_v1.4/classify_model/20201202_wool_classnames.txt")
#
#     do_classify = False
#
#     wool_detection1 = wool_detection(model_path_detection, class_name_path_detection, model_path_classify,
#                                     class_name_path_classify, do_classify)
#     result_detection_init = wool_detection1.model_init_detection()
#     print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
#     if result_detection_init is True:
#         score_thresh = 0.05
#         # test_data = test_data[:10]
#         boxes_temp_cal, labels_temp_cal = None, None
#         imglist = os.listdir(imagessourse)
#         for name in tqdm.tqdm(imglist):
#             print(name)
#             img_test_path = os.path.join(imagessourse, name)
#             if not os.path.exists(img_test_path):
#                 print("not exit:", img_test_path)
#                 continue
#             img_ori = cv2.imread(img_test_path)
#             boxes_detection, scores_detection, labels_detection_name, scores_classify, labels_classify_name = wool_detection1.forward(
#                 img_ori, do_classify=do_classify)
#             img = cv2.imread(img_test_path)
#             for i, boxe_detection in enumerate(boxes_detection):
#                 if scores_detection[i] >= score_thresh:
#                     cv2.rectangle(img, (int(boxe_detection[0]), int(boxe_detection[1])), (int(boxe_detection[2]), int(boxe_detection[3])), (0, 0, 255), 4)
#             cv2.imwrite(os.path.join('D:/gmm/wool_test/2',name),img)