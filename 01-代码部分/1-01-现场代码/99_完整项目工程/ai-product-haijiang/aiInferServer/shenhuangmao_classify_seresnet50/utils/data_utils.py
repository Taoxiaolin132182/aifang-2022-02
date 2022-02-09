# -*- coding: utf-8
from __future__ import division, print_function
import numpy as np
import cv2
import sys
import random
import args
from utils.data_augmentation_back import data_augmentation, resize_image_and_correct_boxes
import re
import os

PY_VERSION = sys.version_info[0]
iter_cnt = 0

def parse_line_old(line, isb=True):
    '''
    Given a line from the training/test txt file, return parsed
    pic_path, boxes info, and label info.
    return:
        pic_path: string.
        boxes: shape [N, 4], N is the ground truth count, elements in the second
            dimension are [x_min, y_min, x_max, y_max]
    '''
    if isb:
        line = line.decode()
    # print(line)
    s = line.strip().split(' ')
    pic_path = s[0]
    s = s[1:]
    box_cnt = len(s) // 5
    boxes = []
    labels = []
    for i in range(box_cnt):
        label, x_min, y_min, x_max, y_max = int(s[i*5]), float(s[i*5+1]), float(s[i*5+2]), float(s[i*5+3]), float(s[i*5+4])
        # label, x_min, y_min, x_max, y_max = int(0), float(s[i * 5 + 1]), float(s[i * 5 + 2]), float(
        #     s[i * 5 + 3]), float(s[i * 5 + 4])
        boxes.append([x_min, y_min, x_max, y_max])
        labels.append(label)
    boxes = np.asarray(boxes, np.float32)
    labels = np.asarray(labels, np.int64)
    return pic_path, boxes, labels

def parse_line(line):
    '''
    Given a line from the training/test txt file, return parsed info.
    line format: line_index, img_path, img_width, img_height, [box_info_1 (5 number)], ...
    return:
        line_idx: int64
        pic_path: string.
        boxes: shape [N, 4], N is the ground truth count, elements in the second
            dimension are [x_min, y_min, x_max, y_max]
        labels: shape [N]. class index.
        img_width: int.
        img_height: int
    '''
    if 'str' not in str(type(line)):
        line = line.decode()
    s = line.strip().split(' ')
    # assert len(s) > 8, 'Annotation error! Please check your annotation file. Make sure there is at least one target object in each image.'
    line_idx = int(s[0])
    pic_path = s[1]
    img_width = int(s[2])
    img_height = int(s[3])
    s = s[4:]
    assert len(s) % 5 == 0, 'Annotation error! Please check your annotation file. Maybe partially missing some coordinates?'
    box_cnt = len(s) // 5
    boxes = []
    labels = []
    for i in range(box_cnt):
        label, x_min, y_min, x_max, y_max = int(s[i * 5]), float(s[i * 5 + 1]), float(s[i * 5 + 2]), float(
            s[i * 5 + 3]), float(s[i * 5 + 4])
        boxes.append([x_min, y_min, x_max, y_max])
        labels.append(label)
    boxes = np.asarray(boxes, np.float32)
    labels = np.asarray(labels, np.int64)
    return line_idx, pic_path, boxes, labels, img_width, img_height

def parse_line_polygon(line):
    if 'str' not in str(type(line)):
        line = line.decode()
    s = line.strip().split('%')
    pic_path = s[0]
    target_points = s[1:]
    boxes = []
    labels = []
    points = []
    for i in range(len(target_points)):
        s_temp = target_points[i].split(" ")
        label = s_temp[0]
        points_temp = s_temp[1:]
        points_temp = np.reshape(np.asarray(points_temp, dtype=np.float32), (-1, 2))
        x_min = np.min(points_temp[:, 0])
        x_max = np.max(points_temp[:, 0])
        y_min = np.min(points_temp[:, 1])
        y_max = np.max(points_temp[:, 1])
        boxes.append([x_min, y_min, x_max, y_max])
        labels.append(label)
        points.append(points_temp)
    boxes = np.asarray(boxes, np.float32)
    return pic_path, boxes, labels, points

def polygon2boxes(ploygons):
    boxes = []
    for ploygon in ploygons:
        points_temp = np.reshape(np.asarray(ploygon, dtype=np.int32), (-1, 2))
        x_min = np.min(points_temp[:, 0])
        x_max = np.max(points_temp[:, 0])
        y_min = np.min(points_temp[:, 1])
        y_max = np.max(points_temp[:, 1])
        boxes.append([x_min, y_min, x_max, y_max])

    return boxes
#
# def random_add_object_polygon(image, points, labels, object_data_lines, add_num):
#     def calc_iou(pred_boxes, true_boxes):
#         try:
#             pred_boxes = np.expand_dims(pred_boxes, -2)
#             # [1, V, 4]
#             true_boxes = np.expand_dims(true_boxes, 0)
#             # [N, 1, 2] & [1, V, 2] ==> [N, V, 2]
#             intersect_mins = np.maximum(pred_boxes[..., :2], true_boxes[..., :2])
#             intersect_maxs = np.minimum(pred_boxes[..., 2:], true_boxes[..., 2:])
#             intersect_wh = np.maximum(intersect_maxs - intersect_mins, 0.)
#             # shape: [N, V]
#             intersect_area = intersect_wh[..., 0] * intersect_wh[..., 1]
#             # shape: [N, 1, 2]
#             pred_box_wh = pred_boxes[..., 2:] - pred_boxes[..., :2]
#             # shape: [N, 1]
#             pred_box_area = pred_box_wh[..., 0] * pred_box_wh[..., 1]
#             # [1, V, 2]
#             true_boxes_wh = true_boxes[..., 2:] - true_boxes[..., :2]
#             # [1, V]
#             true_boxes_area = true_boxes_wh[..., 0] * true_boxes_wh[..., 1]
#             # shape: [N, V]
#             iou = intersect_area / (pred_box_area + true_boxes_area - intersect_area + 1e-10)
#             return iou
#         except:
#             print(pred_boxes)
#             print(true_boxes)
#             return None
#
#     def parse_line_polygon(line):
#         if 'str' not in str(type(line)):
#             line = line.decode()
#         s = line.strip().split('_')
#         pic_path = s[0]
#         target_points = s[1:]
#         boxes = []
#         labels = []
#         points = []
#         for i in range(len(target_points)):
#             s_temp = target_points[i].split(" ")
#             label = s_temp[0]
#             points_temp = s_temp[1:]
#
#             points_temp = np.reshape(np.asarray(points_temp, dtype=np.int32), (-1, 2))
#
#             x_min = np.min(points_temp[:, 0])
#             x_max = np.max(points_temp[:, 0])
#             y_min = np.min(points_temp[:, 1])
#             y_max = np.max(points_temp[:, 1])
#             boxes.append([x_min, y_min, x_max, y_max])
#             labels.append(label)
#             points.append(points_temp)
#         boxes = np.asarray(boxes, np.int32)
#         return pic_path, boxes, labels, points
#
#     def get_polygon_regions(select_lines):
#         regions_select = []
#         labels_select = []
#         masks_select = []
#         points_select = []
#         add_margin = 0
#         for line in select_lines:
#             pic_path, boxes, labels, points = parse_line_polygon(line)
#             labels_temp = [args.class_names.index(label) for label in labels]
#             labels = np.array(labels_temp, dtype=np.float32)
#             image = cv2.imread(pic_path)
#             if image is None:
#                 print("get region:",pic_path)
#             for id in range(len(boxes)):
#                 x0, y0, x1, y1 = boxes[id]
#                 point = points[id]
#                 point[:, 0] = point[:, 0] - x0 + add_margin
#                 point[:, 1] = point[:, 1] - y0 + add_margin
#                 mask = np.zeros((y1 - y0 + add_margin * 2, x1 - x0 + add_margin * 2, 3), dtype=np.int32)
#                 mask = cv2.fillConvexPoly(mask, point, (1, 1, 1))
#                 masks_select.append(mask)
#                 labels_select.append(labels[id])
#                 region = image[y0:y1, x0:x1, :]
#                 regions_select.append(region)
#                 points_select.append(point)
#
#         return regions_select, masks_select, labels_select, points_select
#
#     def polygon2boxes(ploygons):
#         boxes = []
#         for ploygon in ploygons:
#             points_temp = np.reshape(np.asarray(ploygon, dtype=np.int32), (-1, 2))
#             x_min = np.min(points_temp[:, 0])
#             x_max = np.max(points_temp[:, 0])
#             y_min = np.min(points_temp[:, 1])
#             y_max = np.max(points_temp[:, 1])
#             boxes.append([x_min, y_min, x_max, y_max])
#
#         return boxes
#
#     add_num = random.choice(range(4, add_num))
#     boxes = polygon2boxes(points)
#     points_temp = [points[id] for id in range(len(points))]
#     points = points_temp
#     labels = labels.tolist()
#     img_h, img_w, _ = image.shape
#     select_data = random.sample(object_data_lines, add_num)
#     regions_select, masks_select, labels_select, points_select = get_polygon_regions(select_data)
#     add_id = random.sample([i for i in range(len(regions_select))], add_num)
#
#     for id in range(add_num):
#         region = regions_select[add_id[id]]
#         mask = masks_select[add_id[id]]
#         label = labels_select[add_id[id]]
#         point = points_select[add_id[id]]
#         add_h, add_w, c = region.shape
#
#         id = 0
#         while id < 100:
#             x0 = random.choice(range(0, img_w - add_w))
#             y0 = random.choice(range(0, img_h - add_h))
#             box_add = [[x0, y0, x0 + add_w, y0 + add_h]]
#             iou = calc_iou(box_add, boxes)
#             if iou is not None:
#                 iou = iou[0]
#                 if max(iou) <= 0.:
#                     img_insert_region = image[y0:y0 + add_h, x0:x0 + add_w]
#                     img_insert_region = np.where(mask > 0, region, img_insert_region)
#                     image[y0:y0 + add_h, x0:x0 + add_w] = img_insert_region
#                     point[:, 0] = point[:, 0] + x0
#                     point[:, 1] = point[:, 1] + y0
#                     points.append(point)
#                     labels.append(label)
#                     boxes = polygon2boxes(np.array(points))
#                     break
#                 else:
#                     pass
#
#     return image, np.array(points), np.array(labels)


def random_add_object_polygon(image, points, labels, object_data_lines, add_num):
    def calc_iou(pred_boxes, true_boxes):
        try:
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
            # shape: [N, 1]
            pred_box_area = pred_box_wh[..., 0] * pred_box_wh[..., 1]
            # [1, V, 2]
            true_boxes_wh = true_boxes[..., 2:] - true_boxes[..., :2]
            # [1, V]
            true_boxes_area = true_boxes_wh[..., 0] * true_boxes_wh[..., 1]
            # shape: [N, V]
            iou = intersect_area / (pred_box_area + true_boxes_area - intersect_area + 1e-10)
            return iou
        except:
            print(pred_boxes)
            print(true_boxes)
            return None

    def parse_line_polygon(line):
        if 'str' not in str(type(line)):
            line = line.decode()
        s = line.strip().split('_')
        pic_path = s[0]
        target_points = s[1:]
        boxes = []
        labels = []
        points = []
        for i in range(len(target_points)):
            s_temp = target_points[i].split(" ")
            label = s_temp[0]
            points_temp = s_temp[1:]
            points_temp = np.reshape(np.asarray(points_temp, dtype=np.int32), (-1, 2))
            x_min = np.min(points_temp[:, 0])
            x_max = np.max(points_temp[:, 0])
            y_min = np.min(points_temp[:, 1])
            y_max = np.max(points_temp[:, 1])
            boxes.append([x_min, y_min, x_max, y_max])
            labels.append(label)
            points.append(points_temp)
        boxes = np.asarray(boxes, np.int32)
        return pic_path, boxes, labels, points

    def get_polygon_regions(select_lines):
        regions_select = []
        labels_select = []
        masks_select = []
        points_select = []
        add_margin = 0
        for line in select_lines:
            pic_path, boxes, labels, points = parse_line_polygon(line)
            image = cv2.imread(pic_path)
            for id in range(len(boxes)):
                x0, y0, x1, y1 = boxes[id]
                point = points[id]
                point[:, 0] = point[:, 0] - x0 + add_margin
                point[:, 1] = point[:, 1] - y0 + add_margin
                mask = np.zeros((y1 - y0 + add_margin * 2, x1 - x0 + add_margin * 2, 3), dtype=np.int32)
                mask = cv2.fillConvexPoly(mask, point, (1, 1, 1))
                masks_select.append(mask)
                labels_select.append(labels[id])
                region = image[y0:y1, x0:x1, :]
                regions_select.append(region)
                points_select.append(point)

        return regions_select, masks_select, labels_select, points_select

    def polygon2boxes(ploygons):
        boxes = []
        for ploygon in ploygons:
            points_temp = np.reshape(np.asarray(ploygon, dtype=np.int32), (-1, 2))
            x_min = np.min(points_temp[:, 0])
            x_max = np.max(points_temp[:, 0])
            y_min = np.min(points_temp[:, 1])
            y_max = np.max(points_temp[:, 1])
            boxes.append([x_min, y_min, x_max, y_max])

        return boxes

    add_num = random.choice(range(4, add_num))
    boxes = polygon2boxes(points)
    points_temp = [points[id] for id in range(len(points))]
    points = points_temp
    labels = labels.tolist()
    img_h, img_w, _ = image.shape
    select_data = random.sample(object_data_lines, add_num)
    regions_select, masks_select, labels_select, points_select = get_polygon_regions(select_data)
    add_id = random.sample([i for i in range(len(regions_select))], add_num)

    for id in range(add_num):
        region = regions_select[add_id[id]]
        mask = masks_select[add_id[id]]
        label = labels_select[add_id[id]]
        point = points_select[add_id[id]]
        add_h, add_w, c = region.shape

        id = 0
        while id < 100:
            x0 = random.choice(range(0, img_w - add_w))
            y0 = random.choice(range(0, img_h - add_h))
            box_add = [[x0, y0, x0 + add_w, y0 + add_h]]
            iou = calc_iou(box_add, boxes)
            if iou is not None:
                iou = iou[0]
                if max(iou) <= 0.:
                    img_insert_region = image[y0:y0 + add_h, x0:x0 + add_w]
                    img_insert_region = np.where(mask > 0, region, img_insert_region)
                    image[y0:y0 + add_h, x0:x0 + add_w] = img_insert_region
                    point[:, 0] = point[:, 0] + x0
                    point[:, 1] = point[:, 1] + y0
                    points.append(point)
                    labels.append(label)
                    # boxes = polygon2boxes(np.array(points))
                    boxes = polygon2boxes(points)
                    break
                else:
                    pass
    points_temp = []
    for point in points:
        points_temp.append(np.asarray(point, np.int32))
    points = points_temp
    return image, points, np.array(labels)


def random_add_object_polygon_include_background(image, points, labels, object_data_lines, add_num):
    def calc_iou(pred_boxes, true_boxes):
        try:
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
            # shape: [N, 1]
            pred_box_area = pred_box_wh[..., 0] * pred_box_wh[..., 1]
            # [1, V, 2]
            true_boxes_wh = true_boxes[..., 2:] - true_boxes[..., :2]
            # [1, V]
            true_boxes_area = true_boxes_wh[..., 0] * true_boxes_wh[..., 1]
            # shape: [N, V]
            iou = intersect_area / (pred_box_area + true_boxes_area - intersect_area + 1e-10)
            return iou
        except:
            print(pred_boxes)
            print(true_boxes)
            return None

    def parse_line_polygon(line):
        if 'str' not in str(type(line)):
            line = line.decode()
        s = line.strip().split('_')
        pic_path = s[0]
        target_points = s[1:]
        boxes = []
        labels = []
        points = []
        for i in range(len(target_points)):
            s_temp = target_points[i].split(" ")
            label = s_temp[0]
            points_temp = s_temp[1:]
            points_temp = np.reshape(np.asarray(points_temp, dtype=np.int32), (-1, 2))
            x_min = np.min(points_temp[:, 0])
            x_max = np.max(points_temp[:, 0])
            y_min = np.min(points_temp[:, 1])
            y_max = np.max(points_temp[:, 1])
            boxes.append([x_min, y_min, x_max, y_max])
            labels.append(label)
            points.append(points_temp)
        boxes = np.asarray(boxes, np.int32)
        return pic_path, boxes, labels, points

    def get_polygon_regions(select_lines):
        regions_select = []
        labels_select = []
        masks_select = []
        points_select = []
        add_margin = 0
        for line in select_lines:
            pic_path, boxes, labels, points = parse_line_polygon(line)
            image = cv2.imread(pic_path)
            for id in range(len(boxes)):
                x0, y0, x1, y1 = boxes[id]
                point = points[id]
                point[:, 0] = point[:, 0] - x0 + add_margin
                point[:, 1] = point[:, 1] - y0 + add_margin
                mask = np.zeros((y1 - y0 + add_margin * 2, x1 - x0 + add_margin * 2, 3), dtype=np.int32)
                mask = cv2.fillConvexPoly(mask, point, (1, 1, 1))
                masks_select.append(mask)
                labels_select.append(labels[id])
                region = image[y0:y1, x0:x1, :]
                regions_select.append(region)
                points_select.append(point)

        return regions_select, masks_select, labels_select, points_select

    def polygon2boxes(ploygons):
        boxes = []
        for ploygon in ploygons:
            points_temp = np.reshape(np.asarray(ploygon, dtype=np.int32), (-1, 2))
            x_min = np.min(points_temp[:, 0])
            x_max = np.max(points_temp[:, 0])
            y_min = np.min(points_temp[:, 1])
            y_max = np.max(points_temp[:, 1])
            boxes.append([x_min, y_min, x_max, y_max])

        return boxes

    add_num = random.choice(range(4, add_num))
    boxes = polygon2boxes(points)
    points_temp = [points[id] for id in range(len(points))]
    points = points_temp
    labels = labels.tolist()
    img_h, img_w, _ = image.shape
    select_data = random.sample(object_data_lines, add_num)
    regions_select, masks_select, labels_select, points_select = get_polygon_regions(select_data)
    add_id = random.sample([i for i in range(len(regions_select))], add_num)

    for id in range(add_num):
        region = regions_select[add_id[id]]
        mask = masks_select[add_id[id]]
        label = labels_select[add_id[id]]
        point = points_select[add_id[id]]
        add_h, add_w, c = region.shape

        id = 0
        while id < 100:
            x0 = random.choice(range(0, img_w - add_w))
            y0 = random.choice(range(0, img_h - add_h))
            box_add = [[x0, y0, x0 + add_w, y0 + add_h]]
            iou = calc_iou(box_add, boxes)
            if iou is not None:
                iou = iou[0]
                if max(iou) <= 0.:
                    img_insert_region = image[y0:y0 + add_h, x0:x0 + add_w]
                    img_insert_region = np.where(mask > 0, region, img_insert_region)
                    image[y0:y0 + add_h, x0:x0 + add_w] = img_insert_region
                    point[:, 0] = point[:, 0] + x0
                    point[:, 1] = point[:, 1] + y0
                    points.append(point)
                    labels.append(label)
                    # boxes = polygon2boxes(np.array(points))
                    boxes = polygon2boxes(points)
                    break
                else:
                    pass
    points_temp = []
    for point in points:
        points_temp.append(np.asarray(point, np.int32))
    points = points_temp
    return image, points, np.array(labels)


def process_box(boxes, labels, img_size, class_num, anchors):
    '''
    Generate the y_true label, i.e. the ground truth feature_maps in 3 different scales.
    params:
        boxes: [N, 5] shape, float32 dtype. `x_min, y_min, x_max, y_mix, mixup_weight`.
        labels: [N] shape, int64 dtype.
        class_num: int64 num.
        anchors: [9, 4] shape, float32 dtype.
    '''
    anchors_mask = [[6, 7, 8], [3, 4, 5], [0, 1, 2]]
    # print(boxes)
    # print(labels)
    # print("++++")
    # convert boxes form:
    # shape: [N, 2]
    # (x_center, y_center)
    box_centers = None
    box_sizes = None
    if len(boxes) > 0:
        box_centers = (boxes[:, 0:2] + boxes[:, 2:4]) / 2
        # (width, height)
        box_sizes = boxes[:, 2:4] - boxes[:, 0:2]

    # [13, 13, 3, 5+num_class+1] `5` means coords and labels. `1` means mix up weight.
    y_true_13 = np.zeros((img_size[1] // 32, img_size[0] // 32, 3, 6 + class_num), np.float32)
    y_true_26 = np.zeros((img_size[1] // 16, img_size[0] // 16, 3, 6 + class_num), np.float32)
    y_true_52 = np.zeros((img_size[1] // 8, img_size[0] // 8, 3, 6 + class_num), np.float32)

    # mix up weight default to 1.
    y_true_13[..., -1] = 1.
    y_true_26[..., -1] = 1.
    y_true_52[..., -1] = 1.

    y_true = [y_true_13, y_true_26, y_true_52]

    if boxes.shape[0] > 0:
        # [N, 1, 2]
        box_sizes = np.expand_dims(box_sizes, 1)
        # broadcast tricks
        # [N, 1, 2] & [9, 2] ==> [N, 9, 2]
        mins = np.maximum(- box_sizes / 2, - anchors / 2)
        maxs = np.minimum(box_sizes / 2, anchors / 2)
        # [N, 9, 2]
        whs = maxs - mins

        # [N, 9]
        iou = (whs[:, :, 0] * whs[:, :, 1]) / (
            box_sizes[:, :, 0] * box_sizes[:, :, 1] + anchors[:, 0] * anchors[:, 1] - whs[:, :, 0] * whs[:, :, 1] + 1e-10)
        # [N]
        best_match_idx = np.argmax(iou, axis=1)

        ratio_dict = {1.: 8., 2.: 16., 3.: 32.}
        for i, idx in enumerate(best_match_idx):
            # idx: 0,1,2 ==> 2; 3,4,5 ==> 1; 6,7,8 ==> 0
            feature_map_group = 2 - idx // 3
            # scale ratio: 0,1,2 ==> 8; 3,4,5 ==> 16; 6,7,8 ==> 32
            ratio = ratio_dict[np.ceil((idx + 1) / 3.)]
            x = int(np.floor(box_centers[i, 0] / ratio))
            y = int(np.floor(box_centers[i, 1] / ratio))
            k = anchors_mask[feature_map_group].index(idx)
            c = labels[i]
            # c = 0
            # print(feature_map_group, '|', y,x,k,c)

            # y_true[feature_map_group][y, x, k, :2] = box_centers[i]
            # y_true[feature_map_group][y, x, k, 2:4] = box_sizes[i]
            # y_true[feature_map_group][y, x, k, 4] = 1.
            # y_true[feature_map_group][y, x, k, 5 + c] = 1.
            # y_true[feature_map_group][y, x, k, -1] = boxes[i, -1]
            # key2key = [6, 7, 8, 3, 4, 5, 0, 1, 2]

            list_temp = [32., 16., 8.]
            for k in range(3):
                ratio = list_temp[k]
                x = int(np.floor(box_centers[i, 0] / ratio))
                y = int(np.floor(box_centers[i, 1] / ratio))
                # print(box_centers)
                # print(x, y)
                for m in range(3):
                    # if iou[i, key2key[k*3 + m]] < 0.5:
                    #     continue
                    y_true[k][y, x, m, :2] = box_centers[i]
                    y_true[k][y, x, m, 2:4] = box_sizes[i]
                    y_true[k][y, x, m, 4] = 1.
                    y_true[k][y, x, m, 5 + c] = 1.
                    y_true[k][y, x, m, -1] = boxes[i, -1]

    return y_true_13, y_true_26, y_true_52


def parse_data(line, class_num, img_size, anchors, mode, batch_size, letterbox_resize):
    '''
    param:
        line: a line from the training/test txt file
        class_num: totol class nums.
        img_size: the size of image to be resized to. [width, height] format.
        anchors: anchors.
        mode: 'train' or 'val'. When set to 'train', data_augmentation will be applied.
        letterbox_resize: whether to use the letterbox resize, i.e., keep the original aspect ratio in the resized image.
    '''
    pic_path = ""
    img_idx, img, boxes, labels = 0, None, None, None
    if not isinstance(line, list):
        # img_idx, pic_path, boxes, labels, _, _ = parse_line(line)
        # path_pattern = re.compile(r'^/')
        # if not re.search(path_pattern, pic_path):
        #     pic_path = os.path.join(args.img_path, pic_path)
        pic_path, boxes, labels, points = parse_line_polygon(line)
        # labels_temp = [args.class_names.index(label) for label in labels]
        # labels = np.array(labels_temp, dtype=np.float32)
        # print(labels)
        pic_path = args.train_data_nfs_path_2 + pic_path
        img = cv2.imread(pic_path)
        if img is None:
            img = np.zeros((2048, 2448, 3))
            boxes = np.array([])
            labels = np.array([])
            points = []
            print(pic_path)
        elif len(points) > 0:
            labels = np.array(labels)
            img, points, labels = random_add_object_polygon(img, points, labels, args.object_data_lines, 8)

            boxes = polygon2boxes(points)
            # labels = np.array(labels)
            labels_temp = [args.class_names.index(label) for label in labels]
            labels = np.array(labels_temp, dtype=np.float32)
        else:
            labels_temp = [args.class_names.index(label) for label in labels]
            labels = np.array(labels_temp, dtype=np.float32)
            # labels = np.array(labels)

        labels = np.asarray(labels, dtype=np.int32)
        boxes = np.array(boxes, dtype=np.float32)
        # print(pic_path)
        # expand the 2nd dimension, mix up weight default to 1.
        # boxes = np.concatenate((boxes, np.full(shape=(boxes.shape[0], 1), fill_value=1., dtype=np.float32)), axis=-1)
    # else:
    #     # the mix up case
    #     _, pic_path1, boxes1, labels1, _, _ = parse_line(line[0])
    #     # pic_path = pic_path.replace("/mnt/AIdata/", "/media/lantiancug/data1/AIdata/")
    #     if "/mnt/AIdata/Datas/" in pic_path:
    #         pic_path = pic_path.replace("/mnt/AIdata/", args.trian_data_nfs_path_1)
    #     else:
    #         pic_path = pic_path.replace("/mnt/AIdata/images4code2/", args.trian_data_nfs_path_2)
    #     img1 = cv2.imread(pic_path1)
    #     img_idx, pic_path2, boxes2, labels2, _, _ = parse_line(line[1])
    #     img2 = cv2.imread(pic_path2)
    #
    #     img, boxes = mix_up(img1, img2, boxes1, boxes2)
    #     labels = np.concatenate((labels1, labels2))

    # print(boxes)
    # print(labels)
    # print("%%%%%%%%%%%%%%%%%%")
    confs = np.ones(labels.shape)
    if mode == 'train':
        img, boxes, label, confs = data_augmentation(pic_path, img, boxes, labels, img_size, mode, batch_size, False)
    else:
        # img, boxes, label, confs = data_augmentation(pic_path, img, boxes, labels, img_size, mode, batch_size, False)

        img, boxes = resize_image_and_correct_boxes(img, boxes, img_size)

        # random color jittering
        # NOTE: applying color distort may lead to bad performance sometimes
    #     img = random_color_distort(img)
    #
    #     # random expansion with prob 0.5
    #     if np.random.uniform(0, 1) > 0.5:
    #         img, boxes = random_expand(img, boxes, 4)
    #
    #     # random cropping
    #     h, w, _ = img.shape
    #     boxes, crop = random_crop_with_constraints(boxes, (w, h))
    #     x0, y0, w, h = crop
    #     img = img[y0: y0+h, x0: x0+w]
    #
    #     # resize with random interpolation
    #     h, w, _ = img.shape
    #     interp = np.random.randint(0, 5)
    #     img, boxes = resize_with_bbox(img, boxes, img_size[0], img_size[1], interp=interp, letterbox=letterbox_resize)
    #
    #     # random horizontal flip
    #     h, w, _ = img.shape
    #     img, boxes = random_flip(img, boxes, px=0.5)
    # else:
    #     img, boxes = resize_with_bbox(img, boxes, img_size[0], img_size[1], interp=1, letterbox=letterbox_resize)
    if len(boxes) > 0:
        boxes = np.concatenate((boxes, np.full(shape=(boxes.shape[0], 1), fill_value=1., dtype=np.float32)), axis=-1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)

    # the input of yolo_v3 should be in range 0~1
    img = img / 255.
    # print(pic_path)
    y_true_13, y_true_26, y_true_52 = process_box(boxes, labels, img_size, class_num, anchors)

    return img_idx, img, y_true_13, y_true_26, y_true_52


def get_batch_data(batch_line, class_num, img_size, anchors, mode, multi_scale=False, mix_up=False, letterbox_resize=True, interval=10):
    '''
    generate a batch of imgs and labels
    param:
        batch_line: a batch of lines from train/val.txt files
        class_num: num of total classes.
        img_size: the image size to be resized to. format: [width, height].
        anchors: anchors. shape: [9, 2].
        mode: 'train' or 'val'. if set to 'train', data augmentation will be applied.
        multi_scale: whether to use multi_scale training, img_size varies from [320, 320] to [640, 640] by default. Note that it will take effect only when mode is set to 'train'.
        letterbox_resize: whether to use the letterbox resize, i.e., keep the original aspect ratio in the resized image.
        interval: change the scale of image every interval batches. Note that it's indeterministic because of the multi threading.
    '''
    global iter_cnt
    if 'str' not in str(type(mode)):
        mode = mode.decode()
    # multi_scale training
    if multi_scale and mode == 'train':
        random.seed(iter_cnt // interval)
        random_img_size = [[x * 32, x * 32] for x in range(10, 20)]
        img_size = random.sample(random_img_size, 1)[0]
    iter_cnt += 1

    img_idx_batch, img_batch, y_true_13_batch, y_true_26_batch, y_true_52_batch = [], [], [], [], []

    if mode == "train":
        batch_line = batch_line.tolist()[0].decode().split(" * ")
    batch_size = len(batch_line)
    if batch_size == 2:
        img_size = args.train_img_size_0
    elif batch_size == 6:
        img_size = args.train_img_size_1
    else:
        img_size = args.val_img_size
    # mix up strategy
    if mix_up and mode == 'train':
        mix_lines = []
        batch_line = batch_line.tolist()
        for idx, line in enumerate(batch_line):
            if np.random.uniform(0, 1) < 0.5:
                mix_lines.append([line, random.sample(batch_line[:idx] + batch_line[idx+1:], 1)[0]])
            else:
                mix_lines.append(line)
        batch_line = mix_lines

    for line in batch_line:
        img_idx, img, y_true_13, y_true_26, y_true_52 = parse_data(line, class_num, img_size, anchors, mode, batch_size, letterbox_resize)

        img_idx_batch.append(img_idx)
        img_batch.append(img)
        y_true_13_batch.append(y_true_13)
        y_true_26_batch.append(y_true_26)
        y_true_52_batch.append(y_true_52)

    img_idx_batch, img_batch, y_true_13_batch, y_true_26_batch, y_true_52_batch = np.asarray(img_idx_batch, np.int64), np.asarray(img_batch), np.asarray(y_true_13_batch), np.asarray(y_true_26_batch), np.asarray(y_true_52_batch)

    return img_idx_batch, img_batch, y_true_13_batch, y_true_26_batch, y_true_52_batch
