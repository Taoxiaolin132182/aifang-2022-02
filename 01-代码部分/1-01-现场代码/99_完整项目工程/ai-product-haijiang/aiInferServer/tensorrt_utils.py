#!/usr/bin/env python3

import numpy as np
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit
import cv2
from torchvision import transforms
from PIL import Image


class TensorrtClient():
    def __init__(self, enginePath, itemSize=4):
        """
            enginePath: The path of tensorrt model.
            itemSize: The number of bytes of a single element.
            Default numpy is 4.
        """
        self.cfx = cuda.Device(0).make_context()
        self.V = eval(trt.__version__.split(".")[0])
        self.engine = self.__loadEngine(enginePath)
        self.itemSize = itemSize
        self.inputs, self.outputs, self.bindings = \
            self.__parseConfigCudaMemAlloc()
        self.context = self.engine.create_execution_context()
        # Synchronize the stream
        self.stream = cuda.Stream()
        self.cfx.pop()

    def __loadEngine(self, enginePath):
        TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
        with open(enginePath, "rb") as f, trt.Runtime(TRT_LOGGER) as runtime:
            engine = runtime.deserialize_cuda_engine(f.read())

        return engine

    def __parseConfigCudaMemAlloc(self):
        inputs, outputs, bindings = dict(), dict(), list()
        for binding in self.engine:
            size = trt.volume(self.engine.get_binding_shape(binding))
            dims = self.engine.get_binding_shape(binding)
            dtype = trt.nptype(self.engine.get_binding_dtype(binding))

            # Create empty page locked.
            hArr = cuda.pagelocked_empty(trt.volume(dims), dtype=np.float32)
            dArr = cuda.mem_alloc(hArr.nbytes)

            if self.engine.binding_is_input(binding):
                inputs[binding] = {'name': binding, 'size': size, 'dim': dims,
                                   'dtype': dtype, 'hArr': hArr, 'dArr': dArr}
            else:
                outputs[binding] = {'name': binding, 'size': size, 'dim': dims,
                                    'dtype': dtype, 'hArr': hArr, 'dArr': dArr}

            # Create a stream in which to copy inputs/outputs and run inference.
            bindings.append(int(dArr))

        return inputs, outputs, bindings

    def __transferInputToGPU(self, dInput, data, stream):
        assert eval(f"np.{data.dtype}") == dInput['dtype'], \
            f"Get dtype {eval(f'np.{data.dtype}')} but current {dInput['dtype']}."
        cuda.memcpy_htod_async(
            dInput['dArr'], np.ascontiguousarray(data), stream)

    def __memcpyDtohAsync(self, hOutput, dOutput, stream):
        cuda.memcpy_dtoh_async(hOutput, dOutput, stream)

    def inference(self, imageData):
        """
            imageData: Image to infer. Single ndarrary or a list(tuple, dict)
            ndarray if your model is multi input, ndarray format (n, C, H, W) or
            (n, H, W, C).
        """
        # Transfer input data to the GPU.
        self.cfx.push()
        if isinstance(imageData, (list, tuple, dict)):
            if isinstance(imageData, dict):
                for k, d in imageData.items():
                    assert k in self.inputs.keys(), f"No such output : {k}"
                    self.__transferInputToGPU(
                        self.inputs[k], d, self.stream)
            else:
                for i, data in imageData:
                    self.__transferInputToGPU(
                        list(self.inputs.values())[i], data, self.stream)
        else:
            self.__transferInputToGPU(
                list(self.inputs.values())[0], imageData, self.stream)

        # Run inference.
        if self.V >= 7:
            self.context.execute_async_v2(
                bindings=self.bindings, stream_handle=self.stream.handle)
        else:
            self.context.execute_async(
                bindings=self.bindings, stream_handle=self.stream.handle)

        # Transfer predictions back from the GPU.
        for k, out in self.outputs.items():
            self.__memcpyDtohAsync(out['hArr'], out['dArr'], self.stream)

        # Synchronize the stream
        self.stream.synchronize()
        self.cfx.pop()

        return {o: v['hArr'].reshape(v['dim']) for o, v in self.outputs.items()}


def softmax(x):
    x_exp = np.exp(x)
    x_exp_row_sum = x_exp.sum(axis=-1).reshape(list(x.shape)[:-1] + [1])
    softmax = x_exp / x_exp_row_sum
    return softmax


class TensorrtClientAdd:
    def __init__(self, trt_path, input_size, batch_size, class_name):
        self.tensorrtClientModel = TensorrtClient(trt_path)
        self.class_name = class_name
        self.input_size = input_size
        self.batch_size = batch_size

    def dataProcess(self, img):
        img = cv2.resize(img, (self.input_size, self.input_size), cv2.INTER_NEAREST)
        new_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert('RGB')

        # dataProcess
        mean = [0.5, 0.5, 0.5]
        std = [0.5, 0.5, 0.5]
        transform = transforms.Compose([
            # transforms.Resize([input_shape[1], input_shape[2]]),  # [h,w]
            # transforms.Normalize(mean, std),
            transforms.ToTensor(),
            transforms.Normalize(mean, std)
        ])
        img = transform(new_img).unsqueeze(0)
        img = img.numpy()
        return img

    def inference(self, img):
        imgData = self.dataProcess(img)
        output = self.tensorrtClientModel.inference(imgData)["class_result:0"]
        index = int(np.argmax(softmax(output)))
        return self.class_name[index]


'''
ATSS模型，通用infer，没有数据处理的
'''
import torch
import math
from torchvision import ops


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
                 post_top_n=20, nms_iou_thres=0.01, score_thresh=0.01):
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
    # print("detections: ", detections)
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


'''
裁剪目标框到正确范围
'''


def clamp_bboxs(boxs, img_size, to_remove=1):
    boxs[:, 0].clip(min=0, max=img_size[0] - to_remove)
    boxs[:, 1].clip(min=0, max=img_size[1] - to_remove)
    boxs[:, 2].clip(min=0, max=img_size[0] - to_remove)
    boxs[:, 3].clip(min=0, max=img_size[1] - to_remove)

    return boxs


from anchor import *


class TensorrtClientDetect:
    def __init__(self, trt_path, input_size, batch_size, class_num, iou_thresh, score_thresh):
        self.tensorrtClientModel = TensorrtClient(trt_path)
        self.class_num = class_num
        self.input_size = input_size
        self.batch_size = batch_size
        self.iou_thresh = iou_thresh
        self.score_thresh = score_thresh

        # 预anchor的尺寸
        anchor_strides = [8, 16, 32, 64, 128]
        # anchor_scale = [8]
        anchor_scale = [2]

        # 根据模型尺寸来的, 1280/32 = 40  1024/32 = 32
        neck_shapes = [[160, 160], [80, 80], [40, 40], [20, 20], [10, 10]]
        self.anchors = prepare_anchors(neck_shapes, anchor_strides, anchor_scale)
        self.anchors = torch.cat(self.anchors, dim=0)

    def dataProcess(self, img):
        img = cv2.resize(img, (self.input_size, self.input_size), cv2.INTER_NEAREST)
        # new_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert('RGB')

        # dataProcess
        mean = [0.485, 0.456, 0.406]
        std = [0.229, 0.224, 0.225]
        transform = transforms.Compose([
            # transforms.Resize([input_shape[1], input_shape[2]]),  # [h,w]
            # transforms.Normalize(mean, std),
            transforms.ToTensor(),
            transforms.Normalize(mean, std)
        ])
        img = transform(img).unsqueeze(0)
        img = img.numpy()
        return img

    def atssDetectInfer(self, output, input_size, ori_w, ori_h, numclass, anchors):
        # logits
        # print("##logits##")
        logits1 = torch.from_numpy(output["logits1"])
        # print(output["logits1"])
        # print(logits1.shape)
        logits2 = torch.from_numpy(output["logits2"])
        logits3 = torch.from_numpy(output["logits3"])
        logits = torch.cat([logits1, logits2, logits3], dim=0)
        # print("logits.shape: ", logits.shape)
        # bbox_reg
        # print("##bbox_reg##")
        bbox_reg1 = torch.from_numpy(output["bbox_reg1"])
        # print(output["bbox_reg1"])
        # print(bbox_reg1.shape)
        bbox_reg2 = torch.from_numpy(output["bbox_reg2"])
        bbox_reg3 = torch.from_numpy(output["bbox_reg3"])
        bbox_reg = torch.cat([bbox_reg1, bbox_reg2, bbox_reg3], dim=0)
        # print(bbox_reg)
        # print("bbox_reg.shape: ", bbox_reg.shape)
        # centerness
        # print("##centerness##")
        centerness1 = torch.from_numpy(output["centerness1"].T)
        # print(output["centerness1"])
        # print(centerness1.shape)
        centerness2 = torch.from_numpy(output["centerness2"].T)
        centerness3 = torch.from_numpy(output["centerness3"].T)
        centerness = torch.cat([centerness1, centerness2, centerness3], dim=0)
        # print("centerness.shape: ", centerness.shape)
        # print(ori_w, ori_h)

        model_output = [logits, bbox_reg, centerness]
        scale = [input_size / ori_w, input_size / ori_h]
        shift = [0, 0]
        # print("anchors: ", anchors)
        result = post_process(model_output, anchors, scale, shift, numclass, nms_iou_thres=self.iou_thresh,
                              score_thresh=self.score_thresh)
        # print("result: ", result)
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

    def inference(self, img):
        ori_h, ori_w, c = img.shape
        imgData = self.dataProcess(img)
        # output = self.tensorrtClientModel.inference(imgData)["class_result:0"]
        output = self.tensorrtClientModel.inference(imgData)

        boxes_core, scores_core, labels_core = self.atssDetectInfer(output, self.input_size, ori_w, ori_h,
                                                                    self.class_num,
                                                                    self.anchors)
        # 如果识别出来目标，把目标裁剪到合理范围
        s = []
        if len(boxes_core) > 0:
            boxes_core = clamp_bboxs(boxes_core, [ori_w, ori_h], to_remove=1)
            w = boxes_core[:, 2] - boxes_core[:, 0]
            h = boxes_core[:, 3] - boxes_core[:, 1]
            s = w * h

        boxes_return = boxes_core.tolist()
        scores_return = scores_core.tolist()
        labels_return = labels_core.tolist()
        returnObj = {}
        returnObj['boxes'] = boxes_return
        returnObj['scores'] = scores_return
        returnObj['labels'] = labels_return
        returnObj['s'] = s
        return returnObj


"""
You can inference any tensorrt model with this script. 
The following demo.
if __name__ == "__main__":
    '''
    enginePath: The tensorrt model path.
    img: Image to infer. Single ndarrary or a list(tuple) ndarray 
    if multi input, ndarray format (n, C, H, W) or (n, H, W, C).
    Other args look from the class.
    '''
    tensorrtClient = TensorrtClient(enginePath)
    output = tensorrtClient.inference(img)

"""

import os
import time
import copy

if __name__ == "__main__":
    trt_path = '/mnt/data/zzb/pytorch/wool/20211012/trt/wool_atss_2_1015.pb'
    trt_path = 'model/wool_atss_2_1015.pb'
    class_name = ["yixian", "shenhuangmao", "black", "other"]
    class_num = 2
    input_size = 1280
    batch_size = 1
    start = time.time()
    # yixian_classfy = TensorrtClientAdd(trt_path, input_size, batch_size, class_name)
    yixian_classfy = TensorrtClientDetect(trt_path, input_size, batch_size, class_num)
    # yixian_classfy = TensorrtClient(trt_path)
    print("context time: ", time.time() - start)

    img_path = 'test'
    save_path = 'save'
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    img_list = os.listdir(img_path)
    for img_name in img_list:
        print(img_name)
        tt = time.time()
        each_path = os.path.join(img_path, img_name)
        img = cv2.imread(each_path)
        ori_img = copy.deepcopy(img)
        out_label = yixian_classfy.inference(img)
        print(out_label)
        print("infer time: ", time.time() - tt)
        # save draw
        boxes = out_label["boxes"]
        scores = out_label["scores"]
        labels = out_label["labels"]

        for i, box in enumerate(boxes):
            x0, y0, x1, y1 = box[0], box[1], box[2], box[3]
            cv2.rectangle(ori_img, (int(x0), int(y0)), (int(x1), int(y1)), [255, 255, 0], 5)
            label = class_name[labels[i]][0]
            txt = "%s|%f" % (label, scores[i])
            cv2.putText(ori_img, txt, (int(x0), int(y0) + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)

        cv2.imwrite(os.path.join(save_path, img_name), ori_img)


