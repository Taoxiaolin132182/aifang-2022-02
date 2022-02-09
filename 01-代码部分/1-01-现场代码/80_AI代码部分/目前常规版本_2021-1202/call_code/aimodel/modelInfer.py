'''
检测通用infer接口
'''
import time
import cv2
import torch
import numpy as np
import math
from torchvision import ops
from torchvision import transforms as TT
# 快速存图
# from turbojpeg import TurboJPEG
# jpeg = TurboJPEG()

from tritonclient_new import inputDataProcess


def do_detection_common(model_detection, img, numclass, image_input_size, nms_threshold_detection,
                        score_threshold_detetection):
    data_process_time = time.time()
    height_detection, width_detection = img.shape[:2]
    img_detection = cv2.resize(img, tuple(image_input_size))
    # 使用torch gpu 加速进行数据处理
    img_detection = torch_Normalized(img_detection)
    # 新的server 模型是需要归一化的, 老的处理方式,速度慢
    # img_qj_detection = img_qj_detection[np.newaxis, :] / 255.
    # img_qj_detection = np.asarray(img_qj_detection, np.float32)
    boxes, scores, labels = detectionInfer(model_detection, img_detection, numclass,
                                           iou_thresh=nms_threshold_detection,
                                           score_thresh=score_threshold_detetection)
    # 防止输出为空数组时,报错
    boxes = np.reshape(boxes, (-1, 4))
    boxes[:, 0] *= (width_detection / image_input_size[0])
    boxes[:, 2] *= (width_detection / image_input_size[0])
    boxes[:, 1] *= (height_detection / image_input_size[1])
    boxes[:, 3] *= (height_detection / image_input_size[1])

    # # 目标识别框根据图片大小进行裁剪
    # if len(boxes) > 0:
    #     boxes = clamp_bboxs(boxes, [width_detection, height_detection], to_remove=1)

    return boxes, scores, labels


def do_detection_common_(model_detection, img, numclass, image_input_size, nms_threshold_detection,
                         score_threshold_detetection):
    data_process_time = time.time()
    height_detection, width_detection = img.shape[:2]
    img_detection = cv2.resize(img, tuple(image_input_size))
    cvtColor_time = time.time()
    img_detection = cv2.cvtColor(img_detection, cv2.COLOR_BGR2RGB)
    # 使用torch gpu 加速进行数据处理
    img_detection = torch_Normalized(img_detection)
    # 新的server 模型是需要归一化的, 老的处理方式,速度慢
    # img_qj_detection = img_qj_detection[np.newaxis, :] / 255.
    # img_qj_detection = np.asarray(img_qj_detection, np.float32)
    boxes, scores, labels = detectionInfer_(model_detection, img_detection, numclass,
                                            iou_thresh=nms_threshold_detection,
                                            score_thresh=score_threshold_detetection)
    # 防止输出为空数组时,报错
    boxes = np.reshape(boxes, (-1, 4))
    boxes[:, 0] *= (width_detection / image_input_size[0])
    boxes[:, 2] *= (width_detection / image_input_size[0])
    boxes[:, 1] *= (height_detection / image_input_size[1])
    boxes[:, 3] *= (height_detection / image_input_size[1])

    # # 目标识别框根据图片大小进行裁剪
    # if len(boxes) > 0:
    #     boxes = clamp_bboxs(boxes, [width_detection, height_detection], to_remove=1)

    return boxes, scores, labels


def do_detection_common_nodata_process(model_detection, oriimg, img, numclass, image_input_size,
                                       nms_threshold_detection,
                                       score_threshold_detetection):
    height_detection, width_detection = oriimg.shape[:2]
    img_detection = img
    img_detection = torch_Normalized(img_detection)
    # 新的server 模型是需要归一化的, 老的处理方式,速度慢
    # img_qj_detection = img_qj_detection[np.newaxis, :] / 255.
    # img_qj_detection = np.asarray(img_qj_detection, np.float32)
    boxes, scores, labels = detectionInfer_(model_detection, img_detection, numclass,
                                            iou_thresh=nms_threshold_detection,
                                            score_thresh=score_threshold_detetection)
    # 防止输出为空数组时,报错
    boxes = np.reshape(boxes, (-1, 4))
    boxes[:, 0] *= (width_detection / image_input_size[0])
    boxes[:, 2] *= (width_detection / image_input_size[0])
    boxes[:, 1] *= (height_detection / image_input_size[1])
    boxes[:, 3] *= (height_detection / image_input_size[1])

    # # 目标识别框根据图片大小进行裁剪
    # if len(boxes) > 0:
    #     boxes = clamp_bboxs(boxes, [width_detection, height_detection], to_remove=1)

    return boxes, scores, labels


'''
torch GPU 归一化图片
'''


def torch_Normalized(img):
    input_data = torch.from_numpy(img)
    # input_data = input_data.to(device)
    input_data = input_data.cuda()
    output_data = input_data / 255.
    out = output_data.cpu().data.numpy()
    out = out[np.newaxis, :]
    return out


# 带bgr to rgb
def torch_Normalized_backup(img):
    input_data = torch.from_numpy(img)
    # input_data = input_data.to(device)
    input_data = input_data.cuda()
    permute = [2, 1, 0]
    input_data = input_data[:, :, permute]
    output_data = input_data / 255.
    out = output_data.cpu().data.numpy()
    out = out[np.newaxis, :]
    return out


'''
目标检测模型infer
'''


def detectionInfer(model, img, num_class, iou_thresh=0.45, score_thresh=0.5):
    time1 = time.time()
    data = model.inference(img)
    # pred_confs = data['confs_result:0'].T
    # pred_probs = data['probs_result:0'].T
    pred_confs = data['confs_result:0']
    pred_probs = data['probs_result:0']

    pred_scores = pred_confs * pred_probs

    out_put_size = pred_confs.size
    pred_boxes = data['boxes_result:0'].reshape(-1, out_put_size).T

    boxes, scores, labels = cpu_nms(pred_boxes, pred_scores, num_class, max_boxes=150, score_thresh=score_thresh,
                                    iou_thresh=iou_thresh)
    return boxes, scores, labels


def detectionInfer_(model, img, num_class, iou_thresh=0.45, score_thresh=0.5):
    # global model_config
    data = model.inference(img)
    # pred_confs = data['confs_result:0'].T
    # pred_probs = data['probs_result:0'].T
    pred_confs = data['confs_result:0']
    pred_probs = data['probs_result:0']

    pred_scores = pred_confs * pred_probs

    out_put_size = pred_confs.size
    pred_boxes = data['boxes_result:0'].reshape(-1, out_put_size).T
    #
    # for label_id in model_config['model_detection_core']['need_10']:
    for label_id in [0]:  # 0 means yixian
        pred_scores[:, :, label_id] = pred_scores[:, :, label_id] * 10
        # 将阈值大于1的,还原到[0,1]
        pred_scores[:, :, label_id] = np.where(pred_scores[:, :, label_id] < 1, pred_scores[:, :, label_id],
                                               pred_scores[:, :, label_id] / 10)

    boxes, scores, labels = cpu_nms_one_class(pred_boxes, pred_scores, num_class, max_boxes=150,
                                              score_thresh=score_thresh,
                                              iou_thresh=iou_thresh)
    return boxes, scores, labels


'''
nms
'''


def py_nms(boxes, scores, max_boxes=50, iou_thresh=0.5):
    """
    Pure Python NMS baseline.

    Arguments: boxes: shape of [-1, 4], the value of '-1' means that dont know the
                      exact number of boxes
               scores: shape of [-1,]
               max_boxes: representing the maximum of boxes to be selected by non_max_suppression
               iou_thresh: representing iou_threshold for deciding to keep boxes
    """
    assert boxes.shape[1] == 4 and len(scores.shape) == 1

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)

        inds = np.where(ovr <= iou_thresh)[0]
        order = order[inds + 1]

    return keep[:max_boxes]


def cpu_nms(boxes, scores, num_classes, max_boxes=50, score_thresh=0.5, iou_thresh=0.5):
    """
    Perform NMS on CPU.
    Arguments:
        boxes: shape [1, 10647, 4]
        scores: shape [1, 10647, num_classes]
    """

    boxes = boxes.reshape(-1, 4)
    scores = scores.reshape(-1, num_classes)
    # Picked bounding boxes
    picked_boxes, picked_score, picked_label = [], [], []

    for i in range(num_classes):
        indices = np.where(scores[:, i] >= score_thresh)
        filter_boxes = boxes[indices]
        filter_scores = scores[:, i][indices]
        if len(filter_boxes) == 0:
            continue
        # do non_max_suppression on the cpu
        indices = py_nms(filter_boxes, filter_scores,
                         max_boxes=max_boxes, iou_thresh=iou_thresh)
        picked_boxes.append(filter_boxes[indices])
        picked_score.append(filter_scores[indices])
        picked_label.append(np.ones(len(indices), dtype='int32') * i)
    if len(picked_boxes) == 0:
        return np.array([]), np.array([]), np.array([])

    boxes = np.concatenate(picked_boxes, axis=0)
    score = np.concatenate(picked_score, axis=0)
    label = np.concatenate(picked_label, axis=0)

    return boxes, score, label


def cpu_nms_one_class(boxes, scores, num_classes, max_boxes=50, score_thresh=0.5, iou_thresh=0.5):
    """
    Perform NMS on CPU.
    Arguments:
        boxes: shape [1, 10647, 4]
        scores: shape [1, 10647, num_classes]
    """

    boxes = boxes.reshape(-1, 4)
    labels = np.array([np.ones(boxes.shape[0], dtype='int32') * i for i in range(num_classes)])

    boxes = np.concatenate((boxes, boxes), axis=0)
    # scores = scores.reshape(-1, 2)
    scores = np.array([scores.reshape(-1, num_classes)[:, label_id] for label_id in range(num_classes)])
    scores = scores.reshape(-1, 1)
    # Picked bounding boxes
    picked_boxes, picked_score, picked_label = [], [], []

    labels = labels.reshape(-1, 1)

    for i in range(1):
        indices = np.where(scores[:, i] >= score_thresh)
        filter_boxes = boxes[indices]
        filter_scores = scores[:, i][indices]
        filter_labels = labels[:, i][indices]
        if len(filter_boxes) == 0:
            continue
        # do non_max_suppression on the cpu
        indices = py_nms(filter_boxes, filter_scores,
                         max_boxes=max_boxes, iou_thresh=iou_thresh)
        picked_boxes.append(filter_boxes[indices])
        picked_score.append(filter_scores[indices])
        picked_label.append(filter_labels[indices])
    if len(picked_boxes) == 0:
        return np.array([]), np.array([]), np.array([])

    boxes = np.concatenate(picked_boxes, axis=0)
    score = np.concatenate(picked_score, axis=0)
    label = np.concatenate(picked_label, axis=0)

    return boxes, score, label


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


'''
裁剪目标框到正确范围
'''


def clamp_bboxs(boxs, img_size, to_remove=1):
    boxs[:, 0].clip(min=0, max=img_size[0] - to_remove)
    boxs[:, 1].clip(min=0, max=img_size[1] - to_remove)
    boxs[:, 2].clip(min=0, max=img_size[0] - to_remove)
    boxs[:, 3].clip(min=0, max=img_size[1] - to_remove)

    return boxs


'''
ATSS模型，通用infer，没有数据处理的
'''


def box_decode(preds, anchors):
    anchors = anchors.to(preds.dtype)

    TO_REMOVE = 1  # TODO remove
    widths = anchors[:, 2] - anchors[:, 0] + TO_REMOVE
    heights = anchors[:, 3] - anchors[:, 1] + TO_REMOVE
    ctr_x = (anchors[:, 2] + anchors[:, 0]) / 2
    ctr_y = (anchors[:, 3] + anchors[:, 1]) / 2

    wx, wy, ww, wh = (10., 10., 5., 5.)
    dx = preds[:, 0::4] / wx
    dy = preds[:, 1::4] / wy
    dw = preds[:, 2::4] / ww
    dh = preds[:, 3::4] / wh

    # Prevent sending too large values into torch.exp()
    dw = torch.clamp(dw, max=math.log(1000. / 16))
    dh = torch.clamp(dh, max=math.log(1000. / 16))

    pred_ctr_x = dx * widths[:, None] + ctr_x[:, None]
    pred_ctr_y = dy * heights[:, None] + ctr_y[:, None]
    pred_w = torch.exp(dw) * widths[:, None]
    pred_h = torch.exp(dh) * heights[:, None]

    pred_boxes = torch.zeros_like(preds)
    pred_boxes[:, 0::4] = pred_ctr_x - 0.5 * (pred_w - 1)
    pred_boxes[:, 1::4] = pred_ctr_y - 0.5 * (pred_h - 1)
    pred_boxes[:, 2::4] = pred_ctr_x + 0.5 * (pred_w - 1)
    pred_boxes[:, 3::4] = pred_ctr_y + 0.5 * (pred_h - 1)
    return pred_boxes


def remove_small_boxes(bboxes, min_size):
    """
    Only keep boxes with both sides >= min_size

    Arguments:
        bboxes (bbox tensors)
        min_size (int)
    """
    # TODO maybe add an API for querying the ws / hs
    # xywh_boxes = boxlist.convert("xywh").bbox
    # _, _, ws, hs = xywh_boxes.unbind(dim=1)

    ws = bboxes[:, 2] - bboxes[:, 0]
    hs = bboxes[:, 3] - bboxes[:, 1]
    keep = (
            (ws >= min_size) & (hs >= min_size)
    ).nonzero(as_tuple=False).squeeze(1)
    # print('remove_small_boxes', keep.shape)
    return keep


def post_process(model_output, anchors, scale, shift, num_classes, pre_nms_thresh=0.01, pre_nms_top_n=1000,
                 post_top_n=20, nms_iou_thres=0.1, score_thresh=0.01):
    # print(scale, shift)
    bbox_cls_logits, bbox_reg, centerness = model_output
    # print(bbox_cls_logits.shape, bbox_reg.shape, centerness.shape)

    # t = time.time()

    # bbox_cls_logits = bbox_cls_logits.cpu()
    # bbox_reg = bbox_reg.cpu()
    # centerness = centerness.cpu()
    # anchors = anchors.cpu()
    # print('t1 time:', time.time() - t)

    # t = time.time()

    bbox_cls_prob = bbox_cls_logits.reshape(-1, num_classes).sigmoid()
    # print(bbox_cls_prob)
    # bbox_cls_prob[:, 1:] = 0.0  # 只选取特定的类别
    # print('bbox_cls_prob', bbox_cls_prob)
    candidate_inds = bbox_cls_prob >= pre_nms_thresh
    pre_nms_num = candidate_inds.view(-1).sum()
    pre_nms_num = pre_nms_num.clamp(max=pre_nms_top_n)
    # print("candidate_inds", candidate_inds)

    centerness = centerness.reshape(-1, 1).sigmoid()
    bbox_scores = (bbox_cls_prob * centerness)[candidate_inds]
    # bbox_scores = bbox_cls_prob[candidate_inds]

    bbox_scores, top_k_indices = bbox_scores.topk(pre_nms_num, sorted=False)
    candidate_nonzeros = candidate_inds.nonzero(as_tuple=False)[top_k_indices, :]

    bbox_loc = candidate_nonzeros[:, 0]
    bbox_labels = candidate_nonzeros[:, 1]
    # print('t1 time:', time.time() - t)

    # bbox_reg = bbox_reg.reshape(-1, 4)[box_loc, :]
    # anchors = anchors[box_loc, :]
    # t = time.time()
    detections = box_decode(bbox_reg.reshape(-1, 4)[bbox_loc, :], anchors[bbox_loc, :])
    # print('t1 time:', time.time() - t)

    # remove small boxes
    keep = remove_small_boxes(detections, min_size=0)
    detections = detections[keep]
    bbox_labels = bbox_labels[keep]
    # bbox_scores = bbox_scores[keep]
    bbox_scores = torch.sqrt(bbox_scores[keep])
    # print('t1 time:', time.time() - t)

    # nms
    # t = time.time()
    keep = ops.nms(detections, bbox_scores, nms_iou_thres)
    # print('nms time:', time.time() - t)
    # print("after nms keep", keep.shape)

    # t = time.time()

    # detections = detections.cpu()
    # bbox_labels = bbox_labels.cpu()
    # bbox_scores = bbox_scores.cpu()

    detections = detections[keep]
    bbox_labels = bbox_labels[keep]
    bbox_scores = bbox_scores[keep]

    # top 20
    post_top_n = min(keep.shape[0], post_top_n)
    # score thresh
    for i in range(post_top_n):
        if bbox_scores[i].item() <= score_thresh:
            post_top_n = i
            break

    detections = detections[:post_top_n]
    bbox_labels = bbox_labels[:post_top_n]
    bbox_scores = bbox_scores[:post_top_n]
    # print("bbox_scores", bbox_scores)

    # scale & shift back
    # detections[:, [0, 2]] = (detections[:, [0, 2]] - shift[0])
    # detections[:, [1, 3]] = (detections[:, [1, 3]] - shift[1])
    # detections = detections / scale

    detections[:, [0, 2]] = (detections[:, [0, 2]] - shift[0]) / scale[0]
    detections[:, [1, 3]] = (detections[:, [1, 3]] - shift[1]) / scale[1]

    # print('t2 time:', time.time() - t)

    det_result = []
    for i in range(num_classes):
        is_cls_i = (bbox_labels == i)

        try:
            bboxes = detections[is_cls_i]
            scores = bbox_scores[is_cls_i]
        except Exception:
            print(Exception)
            print('detections, bbox_scores', detections, bbox_scores)
            print('is_cls_i', is_cls_i)

        det_bboxes = torch.cat([bboxes, scores[:, None]], dim=1)
        det_result.append(det_bboxes.numpy())

    # det_result[0] = np.concatenate((det_result[0], det_result[1]), axis=0)

    return det_result


def atssDetectionInferCommonNoDataProcess(model_detection, oriimg, img, anchors, numclass, image_input_size,
                                          nms_threshold_detection,
                                          score_threshold_detetection):
    # data = model_detection.inference(img)  # old infer
    data = model_detection.inferenceNew(img)  # new infer
    model_output = [torch.from_numpy(data['logits'][0]), torch.from_numpy(data['bbox_reg'][0]),
                    torch.from_numpy(data['centerness'][0])]
    image_h, image_w, c = oriimg.shape

    scale = [image_input_size[1] / image_w, image_input_size[0] / image_h]
    shift = [0, 0]

    result = post_process(model_output, anchors, scale, shift, numclass, nms_iou_thres=nms_threshold_detection,
                          score_thresh=score_threshold_detetection)
    # 数据解析
    boxes_, scores_, labels_ = [], [], []
    for label_id in range(numclass):
        for i in range(len(result[label_id])):
            box = result[label_id].tolist()
            x0, y0, x1, y1 = int(box[i][0]), int(box[i][1]), int(box[i][2]), int(box[i][3])
            box_ = [x0, y0, x1, y1]
            score = float(box[i][4])
            label = label_id

            boxes_.append(box_)
            scores_.append(score)
            labels_.append(label)
    boxes = np.array(boxes_)
    scores = np.array(scores_)
    labels = np.array(labels_)
    return boxes, scores, labels


def atssPicProcess(inputs):
    image, image_input_size = inputs["img"], inputs["inputsize"]
    img_detection = cv2.resize(image, (image_input_size[0], image_input_size[1]))
    # img_detection = cv2.cvtColor(img_detection, cv2.COLOR_BGR2RGB)  # 现在的模型都是BGR模型,所以不需要进行转换

    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    transform = TT.Compose([TT.ToTensor(),
                            TT.Normalize(mean, std)])

    img_detection = transform(img_detection).unsqueeze(0).numpy()
    # 进行set_data_from_numpy处理
    input_names = 'input_data'
    img_detection = inputDataProcess(img_detection, input_names)
    return img_detection


def cvImwrite(inputs):
    # global jpeg
    imgpath = inputs["imgpath"]
    img = inputs["img"]
    cv2.imwrite(imgpath, img)
    # out_file = open(imgpath, 'wb')
    # out_file.write(jpeg.encode(img, quality=95))
    # out_file.close()