# coding=utf-8
# for better understanding about yolov3 architecture, refer to this website (in Chinese):
# https://blog.csdn.net/leviopku/article/details/82660381

from __future__ import division, print_function

import tensorflow as tf

slim = tf.contrib.slim

from shenhuangmao_classify_seresnet50.utils.layer_utils import conv2d, darknet53_body, yolo_block, upsample_layer
from shenhuangmao_classify_seresnet50.utils.focal_loss import focal_loss


class yolov3(object):

    def __init__(self, class_num, batch_norm_decay=0.9):
        self.batch_norm_decay = batch_norm_decay
        self.class_num = class_num

    def forward(self, inputs, is_training=False, reuse=False):
        # the input img_size, form: [height, weight]
        # it will be used later
        self.img_size = tf.shape(inputs)[1:3]
        # set batch norm params
        batch_norm_params = {
            'decay': self.batch_norm_decay,
            'epsilon': 1e-05,
            'scale': True,
            'is_training': is_training,
            'fused': None,  # Use fused batch norm if possible.
        }

        with slim.arg_scope([slim.conv2d, slim.batch_norm], reuse=reuse):
            with slim.arg_scope([slim.conv2d], normalizer_fn=slim.batch_norm,
                                normalizer_params=batch_norm_params,
                                biases_initializer=None,
                                activation_fn=lambda x: tf.nn.relu6(x)):
                with tf.variable_scope('darknet53_body'):
                    route_1, route_2, route_3 = darknet53_body(inputs)

                with tf.variable_scope('yolov3_head'):
                    downsample_1 = conv2d(route_1, 128, 3, strides=2)
                    concat1 = tf.concat([downsample_1, route_2], axis=3)
                    downsample_2 = conv2d(concat1, 128, 3, strides=2)
                    concat2 = tf.concat([downsample_2, route_3], axis=3)
                    out_1 = conv2d(concat2, 128, 3, strides=2)
                    out_2 = conv2d(out_1, 128, 3, strides=1)
                    out_3 = conv2d(out_2, 128, 3, strides=1)
                    out_4 = tf.layers.flatten(out_3)
                    out_5 = tf.layers.dense(out_4, 128, activation=lambda x: tf.nn.relu6(x),
                                            kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                            bias_initializer=tf.zeros_initializer(), use_bias=True)

                    logits_output = tf.layers.dense(out_5, self.class_num,
                                                    kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                                    bias_initializer=tf.zeros_initializer(), use_bias=False)

                return logits_output, out_5


class yolov3_back(object):

    def __init__(self, class_num, batch_norm_decay=0.9):
        self.batch_norm_decay = batch_norm_decay
        self.class_num = class_num

    def forward(self, inputs, is_training=False, reuse=False):
        # the input img_size, form: [height, weight]
        # it will be used later
        self.img_size = tf.shape(inputs)[1:3]
        # set batch norm params
        batch_norm_params = {
            'decay': self.batch_norm_decay,
            'epsilon': 1e-05,
            'scale': True,
            'is_training': is_training,
            'fused': None,  # Use fused batch norm if possible.
        }

        with slim.arg_scope([slim.conv2d, slim.batch_norm], reuse=reuse):
            with slim.arg_scope([slim.conv2d], normalizer_fn=slim.batch_norm,
                                normalizer_params=batch_norm_params,
                                biases_initializer=None,
                                activation_fn=lambda x: tf.nn.leaky_relu(x, alpha=0.1)):
                with tf.variable_scope('darknet53_body'):
                    route_1, route_2, route_3 = darknet53_body(inputs)

                with tf.variable_scope('yolov3_head'):
                    downsample_1 = conv2d(route_1, 256, 3, strides=2)
                    concat1 = tf.concat([downsample_1, route_2], axis=3)
                    downsample_2 = conv2d(concat1, 256, 3, strides=2)
                    concat2 = tf.concat([downsample_2, route_3], axis=3)
                    out_1 = conv2d(concat2, 256, 3, strides=2)
                    out_2 = conv2d(out_1, 256, 3, strides=1)
                    out_3 = conv2d(out_2, 256, 3, strides=1)
                    out_4 = tf.layers.flatten(out_3)
                    out_5 = tf.layers.dense(out_4, 256, activation=lambda x: tf.nn.leaky_relu(x, alpha=0.1),
                                    kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                    bias_initializer=tf.zeros_initializer(), use_bias=True)

                    logits_output = tf.layers.dense(out_5, self.class_num,
                                                    kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                                    bias_initializer=tf.zeros_initializer(), use_bias=False)

            return logits_output, out_5

class yolov3_trt(object):

    def __init__(self, class_num, batch_norm_decay=0.9):
        self.batch_norm_decay = batch_norm_decay
        self.class_num = class_num

    def forward(self, inputs, is_training=False, reuse=False):
        # the input img_size, form: [height, weight]
        # it will be used later
        self.img_size = tf.shape(inputs)[1:3]
        # set batch norm params
        batch_norm_params = {
            'decay': self.batch_norm_decay,
            'epsilon': 1e-05,
            'scale': True,
            'is_training': is_training,
            'fused': None,  # Use fused batch norm if possible.
        }

        with slim.arg_scope([slim.conv2d, slim.batch_norm], reuse=reuse):
            with slim.arg_scope([slim.conv2d], normalizer_fn=slim.batch_norm,
                                normalizer_params=batch_norm_params,
                                biases_initializer=None,
                                activation_fn=lambda x: tf.nn.relu(x)):
                with tf.variable_scope('darknet53_body'):
                    route_1, route_2, route_3 = darknet53_body(inputs)

                with tf.variable_scope('yolov3_head'):
                    downsample_1 = conv2d(route_1, 256, 3, strides=2)
                    concat1 = tf.concat([downsample_1, route_2], axis=3)
                    downsample_2 = conv2d(concat1, 256, 3, strides=2)
                    concat2 = tf.concat([downsample_2, route_3], axis=3)
                    out_1 = conv2d(concat2, 256, 3, strides=2)
                    out_2 = conv2d(out_1, 256, 3, strides=1)
                    out_3 = conv2d(out_2, 256, 3, strides=1)
                    out_4 = tf.layers.flatten(out_3)
                    out_5 = tf.layers.dense(out_4, 256, activation=lambda x: tf.nn.relu(x),
                                    kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                    bias_initializer=tf.zeros_initializer(), use_bias=True)

                    logits_output = tf.layers.dense(out_5, self.class_num,
                                                    kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                                    bias_initializer=tf.zeros_initializer(), use_bias=False)

            return logits_output, out_5

