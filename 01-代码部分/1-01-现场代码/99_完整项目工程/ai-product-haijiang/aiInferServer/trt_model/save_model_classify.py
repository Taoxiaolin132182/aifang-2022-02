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

from model import yolov3

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
parser.add_argument("--anchor_path", type=str, default="/media/data/trt_model_back/YOLOv3_TensorFlow/data/my_data/sjht_anchors.txt",
                    help="The path of the anchor txt file.")
parser.add_argument("--new_size", nargs='*', type=int, default=[5472, 3648],  #[5440, 5440],5471, 3648
                    help="Resize the input image with `new_size`, size format: [width, height]")
parser.add_argument("--class_name_path", type=str, default="/media/data/trt_model_back/YOLOv3_TensorFlow/data/my_data/sjht_classnames_big_class.txt",
                    help="The path of the class names.")#black_model-step_4300_loss_1.946512_lr_1e-05
parser.add_argument("--restore_path_detection", type=str, default="/media/data/lantiancug/projects/work/trt_model/black_model-step_48800_loss_824.915527_lr_1e-06",#model-step_900_loss_0.890991_lr_3.125e-06,black_model-step_1100_loss_0.640153_lr_3.125e-06
                    help="The path of the weights to restore.")
parser.add_argument("--restore_path_classify", type=str, default="/media/data/trt_model_back/YOLOv3_TensorFlow/tf_model/0115_ResNeXt_10.ckpt",#27_ResNeXt_19.ckpt, 31_ResNeXt_80.ckpt
                    help="The path of the weights to restore.")

# args = parser.parse_args()

args, unknown = parser.parse_known_args()

#args.anchors = parse_anchors(args.anchor_path)*2.5
args.classes = read_class_names(args.class_name_path)
args.num_class = len(args.classes)


img_size = [192, 192]
class_num = 43

import os

gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
with tf.Session(config=tf.ConfigProto(gpu_options=gpu_options)) as sess:
#with tf.Session() as sess:
    input_data = tf.placeholder(tf.uint8, [1, 192, 192, 3], name='input_data')
    input_data_fp32 = tf.cast(input_data, tf.float32) / 255.
    yolo_model_classfy = yolov3_classfy(class_num)
    with tf.variable_scope('yolov3_classfication'):
        logits, center_feature = yolo_model_classfy.forward(input_data_fp32, is_training=False)
    # with tf.variable_scope('se_resnext'):
    #     logits, logits_softmax = SE_ResNet(images, num_classes=class_num, is_training=False)
    saver = tf.train.Saver(var_list=tf.contrib.framework.get_variables_to_restore(include=["yolov3_classfication"]))
    # class_lables = tf.argmax(logits, 1)
    # mask = tf.greater_equal(class_lables, tf.constant(score_thresh))
    class_result = tf.identity(logits, name='class_result')
    saver.restore(sess, args.restore_path_classify)

    saver = tf.train.Saver()
    # saver.save(sess, "./checkpoint/test_model")

    tf.saved_model.simple_save(sess,
                               "yolov3_model_sjht_classify",
                               inputs={"Input_img": input_data},
                               outputs={"Labels": class_result})

