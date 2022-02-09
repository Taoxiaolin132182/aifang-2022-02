# coding: utf-8

from __future__ import division, print_function

import tensorflow as tf
import numpy as np
import argparse
import cv2
import time
# import TIS


from utils.misc_utils import parse_anchors, read_class_names
from utils.nms_utils import gpu_nms, cpu_nms, gpu_nms_1, gpu_nms_2
from utils.plot_utils import get_color_table, plot_one_box

from model import yolov3, yolov3_trt, yolov3_trt_prun_new

import time
import ctypes
import numpy
import sys

sys.path.append(".")


from utils.misc_utils import parse_anchors, read_class_names
from utils.nms_utils import gpu_nms, cpu_nms, gpu_nms_combine, gpu_nms_new, gpu_nms_new_prun
from utils.plot_utils import get_color_table, plot_one_box

from model import yolov3, yolov3_trt
# from se_resnet import SE_ResNet
# from se_resnet_lekyrelu import SE_ResNet
from yolov3_classfition_model import yolov3_trt as yolov3_classfy



class StruMVSImageSize(ctypes.Structure):
    _fields_ = [("m_uWidth", ctypes.c_uint32),
                ("m_uHeight", ctypes.c_uint32)]
#end class StruMVSImageSize


parser = argparse.ArgumentParser(description="YOLO-V3 test single image test procedure.")
parser.add_argument("--input_image", type=str, default="./data/demo_data/WeChat Image_20190527134310.jpg",
                    help="The path of the input image.")
# parser.add_argument("--anchor_path", type=str, default="./data/my_data/cotton_anchors.txt",
#                     help="The path of the anchor txt file.")
parser.add_argument("--anchor_path", type=str, default="/media/data/trt_model/YOLOv3_TensorFlow/data/my_data/sjht_anchors.txt",
                    help="The path of the anchor txt file.")
parser.add_argument("--new_size", nargs='*', type=int, default=[5472, 3648],  #[5440, 5440],5471, 3648
                    help="Resize the input image with `new_size`, size format: [width, height]")
parser.add_argument("--class_name_path", type=str, default="/media/data/trt_model/YOLOv3_TensorFlow/data/my_data/sjht_classnames_big_class.txt",
                    help="The path of the class names.")#black_model-step_4300_loss_1.946512_lr_1e-05
parser.add_argument("--restore_path_detection", type=str, default="/media/data/trt_model_back/YOLOv3_TensorFlow/tf_model/black_model-step_181000_loss_0.131247_lr_1e-06",#model-step_900_loss_0.890991_lr_3.125e-06,black_model-step_1100_loss_0.640153_lr_3.125e-06
                    help="The path of the weights to restore.")
parser.add_argument("--restore_path_classify", type=str, default="/media/data/trt_model/YOLOv3_TensorFlow/tf_model/0103_ResNeXt_202.ckpt",#27_ResNeXt_19.ckpt, 31_ResNeXt_80.ckpt
                    help="The path of the weights to restore.")

# args = parser.parse_args()

args, unknown = parser.parse_known_args()

args.anchors = parse_anchors(args.anchor_path)*2.5
args.classes = read_class_names(args.class_name_path)
args.num_class = len(args.classes)


img_size = [192, 192]
class_num = 43

import os

gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
with tf.Session(config=tf.ConfigProto(gpu_options=gpu_options)) as sess:
    input_data = tf.placeholder(tf.uint8, [1, 2016, 3008, 3], name='input_data')
    #b, g, r = tf.split(axis=3, num_or_size_splits=3, value=input_data)
    #input_data_rgb = tf.concat(axis=3, values=[r, g, b])
    #input_data_rgb = tf.expand_dims(input_data_rgb, 0)
    input_data_fp32 = tf.cast(input_data, tf.float32) / 255.
    #input_data_1 = tf.image.resize_images(input_data_rgb_fp32, [1024, 1504], 3)
    # input_data_1 = tf.image.resize_images(input_data, [1824, 2736], 3)
    yolo_model = yolov3_trt(args.num_class, args.anchors)
    with tf.variable_scope('yolov3'):
        pred_feature_maps = yolo_model.forward(input_data_fp32, False)
    pred_boxes, pred_confs, pred_probs = yolo_model.predict(pred_feature_maps)
    pred_scores = pred_confs * pred_probs
    boxes_combine, scores_combine, labels_combine = gpu_nms_new_prun(pred_boxes, pred_scores, 1, max_boxes=50, score_thresh=0.01,
                                                                    iou_thresh=0.1, area_thresh=1.)


    scores_result = tf.identity(scores_combine, name='scores_result')
    boxes_result = tf.identity(boxes_combine, name='boxes_result')
    class_result = tf.identity(labels_combine, name='class_result')

    saver = tf.train.Saver()
    saver.restore(sess, args.restore_path_detection)


    tf.saved_model.simple_save(sess,
                               "./yolov3_model_sjht_detection",
                               inputs={"Input_img": input_data},
                               outputs={"Boxes": boxes_result, "Scores": scores_result, "Labels": class_result})

