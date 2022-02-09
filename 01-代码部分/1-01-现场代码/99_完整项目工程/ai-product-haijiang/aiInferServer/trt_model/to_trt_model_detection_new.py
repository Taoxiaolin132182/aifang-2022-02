from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import imghdr
import json
import os
import sys
import time
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.contrib.saved_model.python.saved_model import reader
import tensorflow.contrib.tensorrt as trt
# from utils.data_generator import DataGenerator
# from tensorflow.python.platform import gfile

def get_trt_graph(graph_def, precision_mode, output_node, batch_size=1, workspace_size=2 << 10):
    trt_graph = trt.create_inference_graph(
        graph_def, output_node, max_batch_size=batch_size,
        max_workspace_size_bytes=workspace_size << 20,
        precision_mode=precision_mode)
    return trt_graph

def get_trt_calib_graph(graph_def, precision_mode, output_node, batch_size=1, workspace_size=2 << 10):
    trt_graph = trt.create_inference_graph(
        graph_def, output_node, max_batch_size=batch_size,
        max_workspace_size_bytes=workspace_size << 20,
        precision_mode=precision_mode)
    return trt_graph

def write_graph_to_file(graph_name, graph_def, output_dir):
    output_path = os.path.join(output_dir, graph_name)
    with tf.gfile.GFile(output_path, "wb") as f:
        f.write(graph_def.SerializeToString())
    print(output_path)

def get_iterator(data):
    dataset = tf.data.Dataset.from_tensors(data).repeat()
    return dataset.make_one_shot_iterator()

def run_graph(graph, input_name, output_names, data, times):
    def get_gpu_config():
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.50)
        return tf.ConfigProto(gpu_options=gpu_options)
    tf.reset_default_graph()
    g = tf.Graph()
    with g.as_default():
        iterator = get_iterator(data)
        return_tensors = tf.import_graph_def(
            graph_def=graph,
            input_map={input_name: iterator.get_next()},
            return_elements=output_names
        )
        output = return_tensors
    with tf.Session(graph=g, config=get_gpu_config()) as sess:
        for _ in range(times):
            start_time = time.time()
            sess.run([output])
            end_time = time.time()
            print(end_time - start_time)

def convert_to_frozen_graph(savedmodel_dir):
    saved_model = reader.read_saved_model(savedmodel_dir)
    meta_graph_def = saved_model.meta_graphs[0]
    graph = tf.Graph()
    with tf.Session(graph=graph) as sess:
        tf.saved_model.loader.load(
            sess, meta_graph_def.meta_info_def.tags, savedmodel_dir)
        frozen_graph_def = tf.graph_util.convert_variables_to_constants(
            sess, graph.as_graph_def(), output_names)
    return frozen_graph_def


savedmodel_dir = "./yolov3_model_sjht_detection"
img_ori = cv2.imread("./camera0_2019_12_19_17_15_48.jpg")
img = cv2.resize(img_ori, tuple([2016, 3008]))
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

#img = np.asarray(img, np.float32)
#data = img[np.newaxis, :] / 255.
data = img[np.newaxis, :]
data = np.tile(data, (1, 1, 1, 1))

input_name = "input_data:0" 
output_names = ["boxes_result", "scores_result", "class_result"]
#output_names = ["class_result"]
frozen_graph_def = convert_to_frozen_graph(savedmodel_dir)
# write_graph_to_file("yolov3_sjht_frozen.pb", frozen_graph_def, "./trt_model")
# trt_graph_fp32 = get_trt_graph(frozen_graph_def, "FP32", output_names, batch_size=1, workspace_size=2 << 10)
# # run_graph(trt_graph_fp32, input_name, output_names, data, 10)
# write_graph_to_file("yolov3_sjht_fp32.pb", trt_graph_fp32, "./trt_model")

trt_graph_fp16 = get_trt_graph(frozen_graph_def, "FP16", output_names, batch_size=1, workspace_size=2 << 10)
write_graph_to_file("yolov3_sjht_fp16_detection.pb", trt_graph_fp16, "./trt_model")
run_graph(trt_graph_fp16, input_name, output_names, data, 10)

#calib_graph_int8 = get_trt_calib_graph(frozen_graph_def, "INT8", output_names, batch_size=1, workspace_size=2 << 10)
#run_graph(calib_graph_int8, input_name, output_names, data, 1)
#trt_graph = trt.calib_graph_to_infer_graph(calib_graph_int8)
#write_graph_to_file("yolov3_sjht_int8_detection.pb", trt_graph, "./trt_model")
