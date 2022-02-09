import cv2
import numpy as np
import random
import os
import copy
import math
import albumentations as A
# from utils.data_utils import parse_line, parse_line_old
# from utils.plot_utils import plot_one_box
# from eval_utils import calc_iou

background_path = [
                   #"/home/chenhong/data/images4code/images/cotton_chenhong/20200602_cotton_background",
                   #"/home/chenhong/data/images4code/images/cotton_chenhong/pic_data_cotton_factory_background",
                   #"/home/chenhong/data/images4code/images/cotton_chenhong/20200606_cotton_background_pm",
                   "/home/chenhong/data/20200819_cotton_background"
                   ]
child_paths = []
def get_chile_path(path):
    return_path = []
    for name in os.listdir(path):
        return_path.append(os.path.join(path, name))
    return return_path
#for path in background_path:
#    child_paths = child_paths + get_chile_path(path)
#background_lines = child_paths
# for child_path in child_paths:
#     # child_path = os.path.join(background_path, child_path)
#     for name in os.listdir(child_path):
#         background_lines.append(os.path.join(child_path, name))

def add_background_box(img, boxes, background_data, add_num):
    def calc_iou(pred_boxes, true_boxes):
        '''
        Maintain an efficient way to calculate the ios matrix using the numpy broadcast tricks.
        shape_info: pred_boxes: [N, 4]
                    true_boxes: [V, 4]
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
        # shape: [N, 1]
        pred_box_area = pred_box_wh[..., 0] * pred_box_wh[..., 1]
        # [1, V, 2]
        true_boxes_wh = true_boxes[..., 2:] - true_boxes[..., :2]
        # [1, V]
        true_boxes_area = true_boxes_wh[..., 0] * true_boxes_wh[..., 1]
        # shape: [N, V]
        iou = intersect_area / (pred_box_area + true_boxes_area - intersect_area + 1e-10)
        return iou
    add_num = random.choice(range(4, add_num))
    boxes = boxes.tolist()
    img_h, img_w, _ = img.shape
    background_data_id = [id for id in range(len(background_data))]
    select_data = random.sample(background_data_id, add_num)
    for id in range(add_num):
        try:
            add_data = cv2.imread(background_data[select_data[id]])
            add_h, add_w, _ = add_data.shape
            find = False
            id = 0
            while not find:
                x0 = random.choice(range(0, img_w - add_w))
                y0 = random.choice(range(0, img_h - add_h))
                box_add = [[x0, y0, x0+add_w, y0+add_h]]
                iou = calc_iou(box_add, boxes)[0]
                if max(iou) <= 0.:
                    find = True
                    img[y0:y0+add_h, x0:x0+add_w] = add_data
                    boxes.append([x0, y0, x0+add_w, y0+add_h])
                else:
                    pass
                id = id + 1
                if id > 500:
                    find = True
        except:
            print("add background fail")
    return img
def calc_iou(pred_boxes, true_boxes):
    '''
    Maintain an efficient way to calculate the ios matrix using the numpy broadcast tricks.
    shape_info: pred_boxes: [N, 4]
                true_boxes: [V, 4]
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
    # shape: [N, 1]
    pred_box_area = pred_box_wh[..., 0] * pred_box_wh[..., 1]
    # [1, V, 2]
    true_boxes_wh = true_boxes[..., 2:] - true_boxes[..., :2]
    # [1, V]
    true_boxes_area = true_boxes_wh[..., 0] * true_boxes_wh[..., 1]

    # shape: [N, V]
    iou = intersect_area / (pred_box_area + true_boxes_area - intersect_area + 1e-10)

    return iou


def resize_image_and_correct_boxes(img, boxes, img_size):
    # convert gray scale image to 3-channel fake RGB image
    if len(img) == 2:
        img = np.expand_dims(img, -1)
    ori_height, ori_width = img.shape[:2]
    new_width, new_height = img_size
    # shape to (new_height, new_width)
    img = cv2.resize(img, (new_width, new_height))

    # convert to float
    # img = np.asarray(img, np.float32)
    # print(boxes)
    # boxes
    # xmin, xmax
   # boxes[:, 0] = boxes[:, 0] / ori_width * new_width
   # boxes[:, 2] = boxes[:, 2] / ori_width * new_width
    # ymin, ymax
    #boxes[:, 1] = boxes[:, 1] / ori_height * new_height
    #boxes[:, 3] = boxes[:, 3] / ori_height * new_height
    for id in range(len(boxes)):
        boxes[id, 0] = boxes[id, 0] / ori_width * new_width
        boxes[id, 2] = boxes[id, 2] / ori_width * new_width
        boxes[id, 1] = boxes[id, 1] / ori_height * new_height
        boxes[id, 3] = boxes[id, 3] / ori_height * new_height
    return img, boxes

def img_rotation(imgrgb, angle):
    '''
    Rotate a image
    :param imgrgb: image which wait for rotating
    :param angle: rotate angle
    :return: image rotated
    '''
    rows, cols, channel = imgrgb.shape
    rotation = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
    img_rotation = cv2.warpAffine(imgrgb, rotation, (cols, rows), borderValue=125)
    return img_rotation

def gaussian_img(img):
    """
    gaussion noise
    """
    im = cv2.GaussianBlur(img, (9, 9), 5)
    return im

def line_img(img):
    """
    drow 1 - 10 lines noise
    """
    num_line = np.random.randint(5, 10)
    for i in range(num_line):
        row = np.random.randint(0, img.shape[0], 2)
        col = np.random.randint(0, img.shape[1], 2)
        im = cv2.line(img, (row[0], col[0]), (row[1], col[1]), 0, 2)
    return im

def erode_img(img):
    """
       erode noise
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    im = cv2.erode(img, kernel)
    return im

def salt_img(img):
    """
       salt noise
       the number of sale dot is n
    """
    n = int(img.shape[0] * img.shape[1] * 0.1)
    ilist = np.random.randint(0, img.shape[1], n)
    jlist = np.random.randint(0, img.shape[0], n)
    for k in range(n):
        i = ilist[k]
        j = jlist[k]
        if img.ndim == 2:
            img[j, i] = 255
        elif img.ndim == 3:
            img[j:j + 1, i:i + 1, :] = 255
    return img

def img_blur(imgrgb):
    '''
    Randomly different grade fuzzy process
    :param imgrgb: image wait for fuzziing process
    :return: fuzzied image
    '''
    choice_list = [3, 5]
    my_choice = random.sample(choice_list, 1)
    img_blur = cv2.blur(imgrgb, (my_choice[0], my_choice[0]))
    return img_blur


def img_addweight(imgrgb):
    '''
    Randomly mixed weighting
    :param imgrgb: image wait for mixing
    :return: mixed image
    '''
    choice_list = [i * 10 for i in range(1, 18)]
    my_choice = random.sample(choice_list, 1)
    blur = cv2.GaussianBlur(imgrgb, (0, 0), my_choice[0])
    img_addweight = cv2.addWeighted(imgrgb, 1.2, blur, -0.2, 0)
    return img_addweight


def img_addcontrast_brightness(imgrgb):
    '''
    Randomly add bright
    :param imgrgb: image wait for adding bright
    :return: image added bright
    '''
    a = random.sample([i / 10 for i in range(8, 13)], 1)[0]
    g = random.sample([i for i in range(0, 3)], 1)[0]
    h, w, ch = imgrgb.shape
    src2 = np.zeros([h, w, ch], imgrgb.dtype)
    img_bright = cv2.addWeighted(imgrgb, a, src2, 1 - a, g)
    return img_bright
def flip_rl(img, boxes, labels):
    h, w = img.shape[0], img.shape[1]
    # chage boxes
    if len(boxes)>0:
        oldx1 = boxes[:, 0].copy()
        oldx2 = boxes[:, 2].copy()
        boxes[:, 0] = w - oldx2
        boxes[:, 2] = w - oldx1
    else:
        pass
    # change img
    img = img[:, ::-1, :]

    return img, boxes, labels

def flip_ud(img, boxes, labels):
    h, w = img.shape[0], img.shape[1]
    # chage boxes
    if len(boxes) > 0:
        oldy1 = boxes[:, 1].copy()
        oldy2 = boxes[:, 3].copy()
        boxes[:, 1] = h - oldy2
        boxes[:, 3] = h - oldy1
    else:
        pass
    # change img
    img = img[::-1, :, :]

    return img, boxes, labels

def cut_random(img_path, img, boxes, labels, img_size, cut_size_boundary=10, cut_rate = 0.1):
    h, w = img.shape[0], img.shape[1]
    if len(boxes) > 0:
        h_up = np.min(boxes[:,1])
        h_down = np.max(boxes[:,3])
        w_left = np.min(boxes[:,0])
        w_right = np.max(boxes[:,2])
        boxes[:, 0] = boxes[:, 0] + 1
        boxes[:, 2] = boxes[:, 2] - 1
        boxes[:, 1] = boxes[:, 1] + 1
        boxes[:, 3] = boxes[:, 3] - 1
    else:
        h_up = 0
        h_down = h
        w_left = 0
        w_right = w


    h_up_cut = 0
    h_down_cut = 0
    w_left_cut = 0
    w_right_cut = 0
    find = False
    while(not find):
        h_up_cut = random.choice(range(min(max(int(h_up - cut_size_boundary), 1), int(h * cut_rate))))
        h_down_cut = random.choice(range(max(min(int(h_down + cut_size_boundary), h-1), int(h * (1-cut_rate))), h))
        w_left_cut = random.choice(range(min(max(int(w_left - cut_size_boundary), 1), int(w * cut_rate))))
        w_right_cut = random.choice(range(max(min(int(w_right + cut_size_boundary), w-1), int(w * (1-cut_rate))), w))
        if 0.8<(w-(w_right_cut-w_left_cut))/(h-(h_down_cut-h_up_cut)) <1.2:
            find = True

    img = img[h_up_cut:h_down_cut, w_left_cut:w_right_cut, :]
    # h_new, w_new = img.shape[0], img.shape[1]
    if len(boxes) > 0:
        boxes[:, 0] = boxes[:, 0] - w_left_cut
        boxes[:, 2] = boxes[:, 2] - w_left_cut
        boxes[:, 1] = boxes[:, 1] - h_up_cut
        boxes[:, 3] = boxes[:, 3] - h_up_cut
    else:
        pass

    return img, boxes, labels
# def cut_random(img_path, img, boxes, labels, img_size, cut_size_boundary=10, cut_rate = 0.2):
#     h, w = img.shape[0], img.shape[1]
#     h_up = np.min(boxes[:,1])
#     h_down = np.max(boxes[:,3])
#     w_left = np.min(boxes[:,0])
#     w_right = np.max(boxes[:,2])
#
#     boxes[:, 0] = boxes[:, 0] + 1
#     boxes[:, 2] = boxes[:, 2] - 1
#     boxes[:, 1] = boxes[:, 1] + 1
#     boxes[:, 3] = boxes[:, 3] - 1
#     boxes_cut = copy.copy(boxes)
#     img_cut = copy.copy(img)
#     cut_right = False
#     is_hair = False
#     num = int(img_path.split('/')[-1].split(".")[0])
#     if 15597158253270000 < num < 15597162522699999 or 15597297137050000 < num < 15603357032269999:
#         is_hair = True
#     times = 0
#     while(not cut_right):
#         if is_hair:
#             cut_rate = 0.3
#         h_up_cut = random.choice(range(min(max(int(h_up - cut_size_boundary), 1), int(h * cut_rate))))
#         h_down_cut = random.choice(range(max(min(int(h_down + cut_size_boundary), h-1), int(h * (1-cut_rate))), h))
#         w_left_cut = random.choice(range(min(max(int(w_left - cut_size_boundary), 1), int(w * cut_rate))))
#         w_right_cut = random.choice(range(max(min(int(w_right + cut_size_boundary), w-1), int(w * (1-cut_rate))), w))
#
#         times = times + 1
#
#         if is_hair:
#             h_new = h_down_cut - h_up_cut
#             w_new = w_right_cut - w_left_cut
#             if (h_new / h < 0.8 and w_new / w < 0.8) or times > 500:
#                 if times > 500:
#                     h_up_cut = int(max(np.min(boxes[:,1]) - 1, 0))
#                     h_down_cut = int(min(np.max(boxes[:,3]) + 1, h))
#                     w_left_cut = int(max(np.min(boxes[:,0]) - 1, 0))
#                     w_right_cut = int(min(np.max(boxes[:,2]) + 1, w))
#
#                 else:
#                     pass
#             else:
#                 continue
#         else:
#             pass
#
#         img_cut = img[h_up_cut:h_down_cut, w_left_cut:w_right_cut, :]
#         # h_new, w_new = img.shape[0], img.shape[1]
#         boxes_cut[:, 0] = boxes[:, 0] - w_left_cut
#         boxes_cut[:, 2] = boxes[:, 2] - w_left_cut
#         boxes_cut[:, 1] = boxes[:, 1] - h_up_cut
#         boxes_cut[:, 3] = boxes[:, 3] - h_up_cut
#         #
#         # img = cv2.resize(img, (h, w))
#         # boxes[:, 0] = boxes[:, 0] * w / w_new + 1
#         # boxes[:, 1] = boxes[:, 1] * h / h_new + 1
#         # boxes[:, 2] = boxes[:, 2] * w / w_new - 1
#         # boxes[:, 3] = boxes[:, 3] * h / h_new - 1
#
#         ori_height, ori_width = img.shape[:2]
#         new_width, new_height = img_size
#
#         boxes_cut_copy = copy.copy(boxes_cut)
#         boxes_cut_copy[:, 0] = boxes_cut[:, 0] / ori_width * new_width
#         boxes_cut_copy[:, 2] = boxes_cut[:, 2] / ori_width * new_width
#         # ymin, ymax
#         boxes_cut_copy[:, 1] = boxes_cut[:, 1] / ori_height * new_height
#         boxes_cut_copy[:, 3] = boxes_cut[:, 3] / ori_height * new_height
#         boxes_cut_copy_w = boxes_cut_copy[:, 2] - boxes_cut_copy[:, 0]
#         boxes_cut_copy_h = boxes_cut_copy[:, 3] - boxes_cut_copy[:, 1]
#
#         if boxes_cut_copy_w.min() > 10 and boxes_cut_copy_h.min() > 10:
#             cut_right = True
#         elif times > 500:
#             # print("++++++++++++++")
#             cut_right = True
#         else:
#             pass
#
#     return img_cut, boxes_cut, labels



def rotation_random(img, boxes, labels):
    angle = random.choice([90, 180])
    h, w = img.shape[0], img.shape[1]
    if angle == 90:
        img = img_rotation(img, -90)
        if len(boxes)>0:
            boxe_tem = boxes.copy()
            boxes[:, 0] = h - boxe_tem[:, 3]
            boxes[:, 1] = boxe_tem[:, 0]
            boxes[:, 2] = h - boxe_tem[:, 1]
            boxes[:, 3] = boxe_tem[:, 2]
        else:
            pass
    else:
        img = img_rotation(img, -180)
        if len(boxes) > 0:
            boxe_tem = boxes.copy()
            boxes[:, 0] = w - boxe_tem[:, 2]
            boxes[:, 1] = h - boxe_tem[:, 3]
            boxes[:, 2] = w - boxe_tem[:, 0]
            boxes[:, 3] = h - boxe_tem[:, 1]
        else:
            pass

    return img, boxes, labels

def seamless(img, box, obj, boxes = None):
    success = True
    try:
        obj_resize = cv2.resize(obj, (box[2] - box[0], box[3] - box[1]))
        img[box[1]:box[3], box[0]:box[2], :] = obj_resize
    except:
        success = False
    return img, success
def color_random(img):
    b, g, r = cv2.split(img)
    B = np.mean(b)
    G = np.mean(g)
    R = np.mean(r)
    K = (R + G + B) / 3
    Kb = K / B
    Kg = K / G
    Kr = K / R
    cv2.addWeighted(b, Kb, 0, 0, 0, b)
    cv2.addWeighted(g, Kg, 0, 0, 0, g)
    cv2.addWeighted(r, Kr, 0, 0, 0, r)
    b_ratio = 0
    g_ratio = 0
    r_ratio = 0
    option_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
    b = b.astype(np.float32)
    g = g.astype(np.float32)
    r = r.astype(np.float32)
    find = False
    while (not find):
        b_ratio = random.sample(option_list, 1)[0]
        g_ratio = random.sample(option_list, 1)[0]
        r_ratio = random.sample(option_list, 1)[0]
        if (b_ratio + g_ratio + r_ratio) > 1.5 and b_ratio > 0.3 and g_ratio > 0.3 and r_ratio > 0.3:
            find = True
    b = b * b_ratio
    g = g * g_ratio
    r = r * r_ratio
    b = b.astype(np.uint8)
    g = g.astype(np.uint8)
    r = r.astype(np.uint8)
    img = cv2.merge([b,g,r])
    return img

def occlusion_random(img, boxes, labels, cut_size_boundary=20):
    h, w = img.shape[0], img.shape[1]
    choice_list = [0, 1]
    for i in range(labels.shape[0]):
        choice = random.sample(choice_list, 1)[0]
        if choice == 0:
            box = boxes[i]
            x0, y0, x1, y1 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
            w_temp = x1-x0
            h_temp = y1-y0
            if w_temp > h_temp and w_temp >=15:
                add_w = max(random.choice(range(int(w_temp*1/4), int(w_temp*1/2))), 2)
                # print(add_w)
                find = False
                box_temp = np.array([[0, 0, 0, 0]])
                while(not find):
                    x_temp = random.choice(range(cut_size_boundary, w - add_w - cut_size_boundary))
                    y_temp = random.choice(range(cut_size_boundary, h - h_temp - cut_size_boundary))
                    box_temp = np.array([[x_temp, y_temp, x_temp + add_w, y_temp + h_temp]])
                    iou_temp = calc_iou(box_temp, boxes)
                    if np.sum(iou_temp) == 0:
                        find = True
                # print(box_temp[0])
                choice = random.sample(choice_list, 1)[0]
                if choice == 0:
                    # img[y0:y1, x0:x0+add_w, :] = img[box_temp[0][1]:box_temp[0][3], box_temp[0][0]:box_temp[0][2], :]
                    img, success = seamless(img, [x0, y0, x0+add_w, y1], img[box_temp[0][1]:box_temp[0][3], box_temp[0][0]:box_temp[0][2], :], boxes)
                    if success:
                        boxes[i][0] = boxes[i][0] + add_w
                    else:
                        pass
                else:
                    # img[y0:y1, x1-add_w:x1, :] = img[box_temp[0][1]:box_temp[0][3], box_temp[0][0]:box_temp[0][2], :]
                    img, success = seamless(img, [x1-add_w, y0, x1, y1],
                                   img[box_temp[0][1]:box_temp[0][3], box_temp[0][0]:box_temp[0][2], :], boxes)
                    if success:
                        boxes[i][2] = boxes[i][2] - add_w
                    else:
                        pass

            elif w_temp <= h_temp and h_temp >=15:
                add_h = max(random.choice(range(int(h_temp*1/4), int(h_temp*1/2))), 2)

                find = False
                box_temp = np.array([[0, 0, 0, 0]])
                while (not find):
                    x_temp = random.choice(range(cut_size_boundary, w - cut_size_boundary - w_temp))
                    y_temp = random.choice(range(cut_size_boundary, h - cut_size_boundary - add_h))
                    box_temp = np.array([[x_temp, y_temp, x_temp + w_temp, y_temp + add_h]])
                    iou_temp = calc_iou(box_temp, boxes)
                    if np.sum(iou_temp) == 0:
                        find = True
                choice = random.sample(choice_list, 1)[0]
                # print(box_temp[0])
                if choice == 0:
                    # img[y0:y0+add_h, x0:x1, :] = img[box_temp[0][1]:box_temp[0][3], box_temp[0][0]:box_temp[0][2], :]
                    img, success = seamless(img, [x0, y0, x1, y0+add_h],
                                   img[box_temp[0][1]:box_temp[0][3], box_temp[0][0]:box_temp[0][2], :], boxes)
                    if success:
                        boxes[i][1] = boxes[i][1] + add_h
                    else:
                        pass
                else:
                    # img[y1-add_h:y1, x0:x1, :] = img[box_temp[0][1]:box_temp[0][3], box_temp[0][0]:box_temp[0][2], :]
                    img, success = seamless(img, [x0, y1-add_h, x1, y1],
                                   img[box_temp[0][1]:box_temp[0][3], box_temp[0][0]:box_temp[0][2], :], boxes)
                    if success:
                        boxes[i][3] = boxes[i][3] - add_h
                    else:
                        pass
            else:
                pass

    # print("+++")
    return img, boxes, labels

def judge_box(obj, img_path, img, boxes):

    h, w = img.shape[0], img.shape[1]
    for i in range(len(boxes)):
        x0, y0, x1, y1 = boxes[i]
        if x0 < 0 or y0< 0 or x1 > w or y1 > h:
            cv2.imwrite("wrong.jpg", img)

def find_id(boxes, box):
    for id in range(boxes.shape[0]):
        if np.sum(boxes[id] - box) == 0:
            return id

def merge_box(boxes, labels, confs, threshold = 0.4):
    boxes_temp = []
    boxes_rest = []
    id_temp = []
    for id in range(boxes.shape[0]):
        if id not in id_temp:
            for i in range(boxes[id+1:].shape[0]):
                if id+i+1 not in id_temp:
                    boxes_rest.append(boxes[id+i+1])
            if len(boxes_rest) > 0:
                box_temp = np.array([[boxes[id][0], boxes[id][1], boxes[id][2], boxes[id][3]]])
                iou_temp = calc_iou(box_temp, boxes_rest)[0].tolist()
                iou_max = max(iou_temp)
                if iou_max > threshold:
                    id_temp.append(find_id(boxes, boxes_rest[iou_temp.index(iou_max)]))
                    box_delete = boxes_rest[iou_temp.index(iou_max)]
                    x1 = min(boxes[id][0], box_delete[0])
                    y1 = min(boxes[id][1], box_delete[1])
                    x2 = max(boxes[id][2], box_delete[2])
                    y2 = max(boxes[id][3], box_delete[3])
                    boxes_temp.append([x1, y1, x2, y2])
                else:
                    boxes_temp.append(boxes[id])
            else:
                boxes_temp.append(boxes[id])
        boxes_rest = []
    boxes_temp = np.array(boxes_temp)
    labels_temp = np.array([0]*len(boxes_temp))
    confs_temp = np.array([1]*len(boxes_temp))

    return boxes_temp, labels_temp, confs_temp


def random_color_distort(img, brightness_delta=10, hue_vari=10, sat_vari=0.1, val_vari=0.1):
    '''
    randomly distort image color. Adjust brightness, hue, saturation, value.
    param:
        img: a BGR uint8 format OpenCV image. HWC format.
    '''

    def random_hue(img_hsv, hue_vari, p=0.5):
        if np.random.uniform(0, 1) > p:
            hue_delta = np.random.randint(-hue_vari, hue_vari)
            img_hsv[:, :, 0] = (img_hsv[:, :, 0] + hue_delta) % 180
        return img_hsv

    def random_saturation(img_hsv, sat_vari, p=0.5):
        if np.random.uniform(0, 1) > p:
            sat_mult = 1 + np.random.uniform(-sat_vari, sat_vari)
            img_hsv[:, :, 1] *= sat_mult
        return img_hsv

    def random_value(img_hsv, val_vari, p=0.5):
        if np.random.uniform(0, 1) > p:
            val_mult = 1 + np.random.uniform(-val_vari, val_vari)
            img_hsv[:, :, 2] *= val_mult
        return img_hsv

    def random_brightness(img, brightness_delta, p=0.5):
        if np.random.uniform(0, 1) > p:
            img = img.astype(np.float32)
            brightness_delta = int(np.random.uniform(-brightness_delta, brightness_delta))
            img = img + brightness_delta
        return np.clip(img, 0, 255)

    # brightness
    img = random_brightness(img, brightness_delta)
    img = img.astype(np.uint8)

    # color jitter
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)

    if np.random.randint(0, 2):
        img_hsv = random_value(img_hsv, val_vari)
        img_hsv = random_saturation(img_hsv, sat_vari)
        img_hsv = random_hue(img_hsv, hue_vari)
    else:
        img_hsv = random_saturation(img_hsv, sat_vari)
        img_hsv = random_hue(img_hsv, hue_vari)
        img_hsv = random_value(img_hsv, val_vari)

    img_hsv = np.clip(img_hsv, 0, 255)
    img = cv2.cvtColor(img_hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    return img


def random_change_contrast(img):
    rate = np.random.uniform(0.8, 1.3)
    add = np.random.uniform(-20, 20)
    img = np.uint8(np.clip((img * rate + add), 0, 255))
    return img


def cut_random_with_cut_scope(img_path, img, boxes, labels, img_size, cut_rate = 0.4, cut_box_rate = 0.5, img_rate = 0.84):
    h, w = img.shape[0], img.shape[1]

    w_cut_bound = int(cut_rate * w)
    h_cut_bound = int(w_cut_bound * img_rate)


   # boxes[:, 0] = boxes[:, 0] + 1
   # boxes[:, 2] = boxes[:, 2] - 1
   # boxes[:, 1] = boxes[:, 1] + 1
   # boxes[:, 3] = boxes[:, 3] - 1

    def box_iou(box, w_left_cut, h_up_cut, w_right_cut, h_down_cut):
        left_line = max(box[0], w_left_cut) + 1
        right_line = min(box[2], w_right_cut) - 1
        top_line = max(box[1], h_up_cut) + 1
        bottom_line = min(box[3], h_down_cut) -1

        # judge if there is an intersect
        if left_line >= right_line or top_line >= bottom_line:
            return 0, []
        else:
            intersect = (right_line - left_line) * (bottom_line - top_line)
            return intersect / ((box[2] - box[0])*(box[3] - box[1])) * 1.0, [left_line - w_left_cut, top_line - h_up_cut, right_line - w_left_cut, bottom_line - h_up_cut]


    def cut_box(boxes, labels, w_left_cut, h_up_cut, w_right_cut, h_down_cut, find):
        boxes_cut = []
        labels_cut = []
        find = True
        for id in range(len(boxes)):
            box = boxes[id]
            iou, box_cut = box_iou(box, w_left_cut, h_up_cut, w_right_cut, h_down_cut)
            if 0< iou < cut_box_rate:
                find = False
            if len(box_cut) > 0:
                boxes_cut.append(box_cut)
                labels_cut.append(labels[id])
        return find, boxes_cut, labels_cut

    find = False
    h_up_cut = 0
    h_down_cut = 0
    w_left_cut = 0
    w_right_cut = 0
    boxes_temp = []
    labels_temp = []
    times = 0
    not_find = False
    while (not find):
        times = times + 1
        h_up_cut = random.randint(0, h - h_cut_bound)
        h_down_cut = h_up_cut + h_cut_bound
        w_left_cut = random.randint(0, w - w_cut_bound)
        w_right_cut = w_left_cut + w_cut_bound
        # boxes_temp = copy.deepcopy(boxes)
        # boxes_temp[:, 0] = boxes_temp[:, 0] - w_left_cut
        # boxes_temp[:, 2] = boxes_temp[:, 2] - w_left_cut
        # boxes_temp[:, 1] = boxes_temp[:, 1] - h_up_cut
        # boxes_temp[:, 3] = boxes_temp[:, 3] - h_up_cut

        find, boxes_temp, labels_temp = cut_box(boxes, labels, w_left_cut, h_up_cut, w_right_cut, h_down_cut, find)
        if len(boxes_temp) <= 0:
            find = False
        if times > 500 and times > 0:
            print("not find")
            find = True
            not_find = True


        #     print(times)
        #      print("+++++++++++++++++++++++++++++++++++++++++++++++")
        #      find = True
        #      return img, boxes, labels
    if not not_find:
        img = img[h_up_cut:h_down_cut, w_left_cut:w_right_cut, :]
        # h_new, w_new = img.shape[0], img.shape[1]
        boxes_temp = np.array(boxes_temp)
        labels_temp = np.array(labels_temp)
    else:
        num_box = len(boxes)
        box_select_id = random.choice(range(num_box))
        h_min = int(max(0, boxes[box_select_id][3] - h_cut_bound))
        h_max = int(min(boxes[box_select_id][1] + h_cut_bound, h - h_cut_bound))
        w_min = int(max(0, boxes[box_select_id][2] - w_cut_bound))
        w_max = int(min(boxes[box_select_id][0] + w_cut_bound, w - w_cut_bound))
        find_child = False
        times = 0
        while (not find_child):
            times = times + 1
            h_up_cut = random.randint(h_min, h_max)
            h_down_cut = h_up_cut + h_cut_bound
            w_left_cut = random.randint(w_min, w_max)
            w_right_cut = w_left_cut + w_cut_bound
            find_child, boxes_temp, labels_temp = cut_box(boxes, labels, w_left_cut, h_up_cut, w_right_cut, h_down_cut, find_child)
            if len(boxes_temp) <= 0:
                find_child = False
            if times > 500 and times > 0:
                box_select_id = random.choice(range(num_box))
                h_min = int(max(0, boxes[box_select_id][3] - h_cut_bound))
                h_max = int(min(boxes[box_select_id][1] + h_cut_bound, h - h_cut_bound))
                w_min = int(max(0, boxes[box_select_id][2] - w_cut_bound))
                w_max = int(min(boxes[box_select_id][0] + w_cut_bound, w - w_cut_bound))
            if times > 2500:
                return img, boxes, labels
                # find_child = True


        img = img[h_up_cut:h_down_cut, w_left_cut:w_right_cut, :]
        # h_new, w_new = img.shape[0], img.shape[1]
        boxes_temp = np.array(boxes_temp)
        labels_temp = np.array(labels_temp)

        if len(boxes_temp > 0):
            print("find children")
        else:
            print("+++++++++++")

    return img, boxes_temp, labels_temp





def cut_random_with_cut_scope_and_random_box(img_path, img, boxes, labels, img_size, cut_rate = 0.4, cut_box_rate = 0.5, img_rate = 0.84):
    h, w = img.shape[0], img.shape[1]
    w_cut_bound = int(cut_rate * w)
    h_cut_bound = int(w_cut_bound * img_rate)

    def box_iou(box, w_left_cut, h_up_cut, w_right_cut, h_down_cut):
        left_line = max(box[0], w_left_cut) + 1
        right_line = min(box[2], w_right_cut) - 1
        top_line = max(box[1], h_up_cut) + 1
        bottom_line = min(box[3], h_down_cut) -1

        # judge if there is an intersect
        if left_line >= right_line or top_line >= bottom_line:
            return 0, []
        else:
            intersect = (right_line - left_line) * (bottom_line - top_line)
            return intersect / ((box[2] - box[0])*(box[3] - box[1])) * 1.0, [left_line - w_left_cut, top_line - h_up_cut, right_line - w_left_cut, bottom_line - h_up_cut]


    def cut_box(boxes, labels, w_left_cut, h_up_cut, w_right_cut, h_down_cut, find):
        boxes_cut = []
        labels_cut = []
        find = True
        for id in range(len(boxes)):
            box = boxes[id]
            iou, box_cut = box_iou(box, w_left_cut, h_up_cut, w_right_cut, h_down_cut)
            if 0< iou < cut_box_rate:
                find = False
            if len(box_cut) > 0:
                boxes_cut.append(box_cut)
                labels_cut.append(labels[id])
        return find, boxes_cut, labels_cut

    h_up_cut = 0
    h_down_cut = 0
    w_left_cut = 0
    w_right_cut = 0
    boxes_temp = []
    labels_temp = []

    if len(boxes) == 0:
        h_up_cut = random.randint(0, h - h_cut_bound)
        h_down_cut = h_up_cut + h_cut_bound
        w_left_cut = random.randint(0, w - w_cut_bound)
        w_right_cut = w_left_cut + w_cut_bound
        img = img[h_up_cut:h_down_cut, w_left_cut:w_right_cut, :]

        return img, boxes, labels

    else:
        num_box = len(boxes)
        box_select_id = random.choice(range(num_box))
        # h_min = int(max(0, boxes[box_select_id][3] - h_cut_bound))
        # h_max = int(min(boxes[box_select_id][1] + h_cut_bound, h - h_cut_bound))
        # w_min = int(max(0, boxes[box_select_id][2] - w_cut_bound))
        # w_max = int(min(boxes[box_select_id][0] + w_cut_bound, w - w_cut_bound))
        h_min = int(max(0, boxes[box_select_id][3] - h_cut_bound))
        h_max = int(min(boxes[box_select_id][1], h - h_cut_bound))
        w_min = int(max(0, boxes[box_select_id][2] - w_cut_bound))
        w_max = int(min(boxes[box_select_id][0], w - w_cut_bound))
        find_child = False
        times = 0
        while (not find_child):
            times = times + 1
            if h_min >= h_max:
                h_up_cut = h_min
            else:
                h_up_cut = random.randint(h_min, h_max)
            h_down_cut = h_up_cut + h_cut_bound
            if w_min >= w_max:
                w_left_cut = w_min
            else:
                w_left_cut = random.randint(w_min, w_max)
            w_right_cut = w_left_cut + w_cut_bound
            find_child, boxes_temp, labels_temp = cut_box(boxes, labels, w_left_cut, h_up_cut, w_right_cut, h_down_cut, find_child)
            if len(boxes_temp) <= 0:
                find_child = False
            if times > 500 and times > 0 and times%500==0:
                box_select_id = random.choice(range(num_box))
                h_min = int(max(0, boxes[box_select_id][3] - h_cut_bound))
                h_max = int(min(boxes[box_select_id][1] + h_cut_bound, h - h_cut_bound))
                w_min = int(max(0, boxes[box_select_id][2] - w_cut_bound))
                w_max = int(min(boxes[box_select_id][0] + w_cut_bound, w - w_cut_bound))
            if times > 2500:
                return img, boxes, labels
                # find_child = True


        img = img[h_up_cut:h_down_cut, w_left_cut:w_right_cut, :]
        # h_new, w_new = img.shape[0], img.shape[1]
        boxes_temp = np.array(boxes_temp)
        labels_temp = np.array(labels_temp)

        return img, boxes_temp, labels_temp


def cut_random_with_cut_scope_new(img_path, img, boxes, labels, img_size, cut_rate = 0.4, cut_box_rate = 0.5, img_rate = 0.84):
    h, w = img.shape[0], img.shape[1]

    w_cut_bound = int(cut_rate * w)
    h_cut_bound = int(w_cut_bound * img_rate)


   # boxes[:, 0] = boxes[:, 0] + 1
   # boxes[:, 2] = boxes[:, 2] - 1
   # boxes[:, 1] = boxes[:, 1] + 1
   # boxes[:, 3] = boxes[:, 3] - 1

    def box_iou(box, w_left_cut, h_up_cut, w_right_cut, h_down_cut):
        left_line = max(box[0], w_left_cut) + 1
        right_line = min(box[2], w_right_cut) - 1
        top_line = max(box[1], h_up_cut) + 1
        bottom_line = min(box[3], h_down_cut) -1

        # judge if there is an intersect
        if left_line >= right_line or top_line >= bottom_line:
            return 0, []
        else:
            intersect = (right_line - left_line) * (bottom_line - top_line)
            return intersect / ((box[2] - box[0])*(box[3] - box[1])) * 1.0, [left_line - w_left_cut, top_line - h_up_cut, right_line - w_left_cut, bottom_line - h_up_cut]


    def cut_box(boxes, labels, w_left_cut, h_up_cut, w_right_cut, h_down_cut, find):
        boxes_cut = []
        labels_cut = []
        find = True
        for id in range(len(boxes)):
            box = boxes[id]
            iou, box_cut = box_iou(box, w_left_cut, h_up_cut, w_right_cut, h_down_cut)
            if 0< iou < cut_box_rate:
                find = False
            if len(box_cut) > 0:
                boxes_cut.append(box_cut)
                labels_cut.append(labels[id])
        return find, boxes_cut, labels_cut

    h_up_cut = 0
    h_down_cut = 0
    w_left_cut = 0
    w_right_cut = 0
    boxes_temp = []
    labels_temp = []
    num_box = len(boxes)
    box_select_id = random.choice(range(num_box))
    h_min = int(max(0, boxes[box_select_id][3] - h_cut_bound))
    h_max = int(min(boxes[box_select_id][1] + h_cut_bound, h - h_cut_bound))
    w_min = int(max(0, boxes[box_select_id][2] - w_cut_bound))
    w_max = int(min(boxes[box_select_id][0] + w_cut_bound, w - w_cut_bound))
    find_child = False
    times = 0
    while (not find_child):
        times = times + 1
        h_up_cut = random.randint(h_min, h_max)
        h_down_cut = h_up_cut + h_cut_bound
        w_left_cut = random.randint(w_min, w_max)
        w_right_cut = w_left_cut + w_cut_bound
        find_child, boxes_temp, labels_temp = cut_box(boxes, labels, w_left_cut, h_up_cut, w_right_cut, h_down_cut, find_child)
        if len(boxes_temp) <= 0:
            find_child = False
        if times > 500 and times > 0 and times%500==0:
            box_select_id = random.choice(range(num_box))
            h_min = int(max(0, boxes[box_select_id][3] - h_cut_bound))
            h_max = int(min(boxes[box_select_id][1] + h_cut_bound, h - h_cut_bound))
            w_min = int(max(0, boxes[box_select_id][2] - w_cut_bound))
            w_max = int(min(boxes[box_select_id][0] + w_cut_bound, w - w_cut_bound))
        if times > 2500:
            return img, boxes, labels
                # find_child = True

    img = img[h_up_cut:h_down_cut, w_left_cut:w_right_cut, :]
    # h_new, w_new = img.shape[0], img.shape[1]
    boxes_temp = np.array(boxes_temp)
    labels_temp = np.array(labels_temp)

    return img, boxes_temp, labels_temp




def replace_random(img, boxes, labels, max_num_replace=1, replace_box_scope=(30, 500)):
    img_ori = copy.deepcopy(img)
    ori_height, ori_width = img.shape[:2]
    num_box = len(boxes)
    num_box_ids = [id for id in range(num_box)]
    select_data = random.sample(num_box_ids, min(max_num_replace, num_box))
    for id in select_data:
        x0, y0, x1, y1 = boxes[id].astype(np.int32)
        if x1-x0 < 5 and y1-y0 < 5:
            continue
        replace_box_w = random.choice(range(replace_box_scope[0], replace_box_scope[1]))
        replace_box_h = random.choice(range(replace_box_scope[0], replace_box_scope[1]))
        replace_box_center_x = random.choice(range(x0, x1))
        replace_box_center_y = random.choice(range(y0, y1))
        replace_box_center_x0 = int(max(0, replace_box_center_x - replace_box_w / 2))
        replace_box_center_x1 = int(min(replace_box_center_x + replace_box_w / 2, ori_width))
        replace_box_center_y0 = int(max(0, replace_box_center_y - replace_box_h / 2))
        replace_box_center_y1 = int(min(replace_box_center_y + replace_box_h / 2, ori_height))

        replace_box_w = replace_box_center_x1 - replace_box_center_x0
        replace_box_h = replace_box_center_y1 - replace_box_center_y0

        box_temp = np.array([[0, 0, 0, 0]])
        find = False
        while (not find):
            x_temp = random.choice(range(0, ori_width - replace_box_w))
            y_temp = random.choice(range(0, ori_height - replace_box_h))
            box_temp = np.array([[x_temp, y_temp, x_temp + replace_box_w, y_temp + replace_box_h]])
            iou_temp = calc_iou(box_temp, boxes)
            if np.sum(iou_temp) == 0:
                find = True

        img[replace_box_center_y0:replace_box_center_y1, replace_box_center_x0:replace_box_center_x1, :] = img[box_temp[0][1]:box_temp[0][3], box_temp[0][0]:box_temp[0][2], :]
        img[y0:y1, x0:x1, :] = img_ori[y0:y1, x0:x1, :]

    return img, boxes, labels


def gamma_adjust(image, gamma):

    #具体做法先归一化到1，然后gamma作为指数值求出新的像素值再还原
    gamma_table = [np.power(x/255.0,gamma)*255.0 for x in range(256)]
    gamma_table = np.round(np.array(gamma_table)).astype(np.uint8)
    #实现映射用的是Opencv的查表函数
    image = cv2.LUT(image,gamma_table)
    return image



transform = A.Compose([
        # A.augmentations.transforms.GridDistortion(num_steps=25, distort_limit=0.5, interpolation=1, border_mode=0, value=None, mask_value=None, always_apply=False, p=1.)

        A.RandomResizedCrop(1280, 1280, scale=(0.8, 1.2)),
        A.IAAPerspective(scale=(0.05, 0.1)),
        A.Rotate(),
        A.Flip(),


    ], bbox_params=A.BboxParams(format='pascal_voc',
                         label_fields=['cls_ids'],
                         min_area=0.3,
                         min_visibility=0.3))




def adjust_box(img_path, img, boxes, labels):
    h, w, c = img.shape
    min_w = np.min(boxes[:, 0])
    max_w = np.max(boxes[:, 2])
    min_h = np.min(boxes[:, 1])
    max_h = np.max(boxes[:, 3])
    if min_w < 0 or min_h < 0 or max_w >= w or max_h >= h:
        print(img_path, min_w, max_w, min_h, max_h)
        print(boxes)
    boxes[:, 0] = boxes[:, 0].clip(min=0, max=w-1)
    boxes[:, 2] = boxes[:, 2].clip(min=0, max=w-1)
    boxes[:, 1] = boxes[:, 1].clip(min=0, max=h-1)
    boxes[:, 3] = boxes[:, 3].clip(min=0, max=h-1)

    return img, boxes, labels


def random_rotation(img_path, img, boxes, labels, img_size, angle_value=10, angle_set=None):
    h, w = img.shape[0], img.shape[1]
    num_boxes = boxes.shape[0]
    def rotate_point(x, y, angle):
        x = x - int(w / 2)
        y = -1 * (y - int(h / 2))
        x_temp = copy.deepcopy(x)
        y_temp = copy.deepcopy(y)
        x = x_temp * math.cos(angle / 180. * math.pi) - y_temp * math.sin(angle / 180. * math.pi)
        y = x_temp * math.sin(angle / 180. * math.pi) + y_temp * math.cos(angle / 180. * math.pi)
        x = x + int(w / 2)
        y = -1 * y + int(h / 2)
        return x, y
    img_temp = copy.deepcopy(img)
    boxes_temp = copy.deepcopy(boxes)
    find = False
    try_id = 0
    while (not find):
        if angle_set is not None:
            angle = random.sample([-90, 90, 180], 1)[0]
        else:
            angle = random.randint(-1*angle_value, angle_value)
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        img_change = cv2.warpAffine(img_temp, M, (w, h),  borderValue=(0, 0, 0))#borderMode=cv2.INTER_LINEAR, borderValue=cv2.BORDER_REPLICATE
        boxes_change = copy.deepcopy(boxes)
        find = True
        if num_boxes > 0:
            for i in range(num_boxes):
                x0, y0, x3, y3 = boxes_temp[i]
                x1, y1, x2, y2 = x3, y0, x0, y3
                x0, y0 = rotate_point(x0, y0, angle)
                x1, y1 = rotate_point(x1, y1, angle)
                x2, y2 = rotate_point(x2, y2, angle)
                x3, y3 = rotate_point(x3, y3, angle)
                x_min = min(x0, x1, x2, x3)
                x_max = max(x0, x1, x2, x3)
                y_min = min(y0, y1, y2, y3)
                y_max = max(y0, y1, y2, y3)
                if x_min <= 0 or y_min <= 0 or x_max >= w or y_max >= h:
                    find = False
                    break
                boxes_change[i][0] = x_min
                boxes_change[i][1] = y_min
                boxes_change[i][2] = x_max
                boxes_change[i][3] = y_max
            if find:
                img = img_change
                boxes = boxes_change
        else:
            pass
        try_id = try_id + 1
        if try_id > 100:
            break

    return img, boxes, labels

def data_augmentation(img_path, img, boxes, labels, img_size, mode, batch_size, use_label_smothing = False):
    confs = np.ones(labels.shape)
    img_temp = [img.copy()]
    boxes_temp = [boxes.copy()]
    labels_temp = [labels.copy()]
    choice_list = [0, 1]
    # choice = random.sample(choice_list, 1)[0]
    choice = 0
    judge_box("original", img_path, img, boxes)
    if choice == 0:
        choice = random.sample(choice_list, 1)[0]
        choice = 1
        if choice == 0 and len(boxes) > 0:
           img, boxes, labels = occlusion_random(img, boxes, labels)
           judge_box("occlusion_random", img_path, img, boxes)
        # new_size = random.randint(2448, 3200)
        # image_height, image_width, C = img.shape
        # image_large_size = np.maximum(image_width, image_height)
        # rate = new_size / image_large_size
        # resized_height = int(image_height * rate)
        # resized_width = int(image_width * rate)
        # img, boxes = resize_image_and_correct_boxes(img, boxes, (resized_height, resized_width))
        # do_gamma_adjust = False
        # for batch in ["wxmfc-20200807-01", "wxmfc-20200806-01", "wxmfc-20200804-01", "wxmfc-20200717-01", "wxmfc-20200717-02", "wxmfc-20200716-02", "wxmfc-20200715-02", "wxmfc-20200714-01"]:
        #     if batch in img_path:
        #         do_gamma_adjust = True
        # if do_gamma_adjust:
        #     #print("gamma", img_path)
        #     img = gamma_adjust(img, 0.41)
        # choice = random.sample([0, 1], 1)[0]
        # # choice = 0
        # if choice != 0:
        #     img = add_background_box(img, boxes, background_lines, 8)

        choice = random.sample(choice_list, 1)[0]
        choice = 1
        if choice == 0 and len(boxes) > 1:
            img, boxes, labels = replace_random(img, boxes, labels, max_num_replace=1, replace_box_scope=(30, 500))

        #img, boxes, labels = cut_random_with_size(img, boxes, labels, cut_size=(1024, 1204), cut_factor=0.8)
        choice = random.sample(choice_list, 1)[0]
        #choice = 1
        if choice == 0:
            img, boxes, labels = random_rotation(img_path, img, boxes, labels, img_size, angle_value=20, angle_set=None)
        
        #img, boxes, labels = adjust_box(img_path, img, boxes, labels)
        #another_transformed = transform(image=img, bboxes=boxes, cls_ids=labels)
        #img = another_transformed["image"]
        #boxes = another_transformed["bboxes"]
        #labels = another_transformed["cls_ids"]
        #boxes = np.asarray(boxes, dtype=np.int32)
        #if batch_size != 2:
            # print(batch_size)
        #    cut_rate = random.sample([0.4, 0.5, 0.6], 1)[0]
        #    img, boxes, labels = cut_random_with_cut_scope_and_random_box(img_path, img, boxes, labels, img_size, cut_rate=cut_rate, cut_box_rate=0.5)
        #else:
          #  cut_rate = random.sample([0.7, 0.8, 0.9], 1)[0]
         #   img, boxes, labels = cut_random_with_cut_scope_and_random_box(img_path, img, boxes, labels, img_size, cut_rate=cut_rate, cut_box_rate=0.5)

        choice = random.sample(choice_list, 1)[0]
        #choice = 1
        if choice == 0:
            try:
                img, boxes, labels = cut_random(img_path, img, boxes, labels, img_size)
            except:
                print(boxes)
                print(type(boxes))
                img, boxes, labels = cut_random(img_path, img, boxes, labels, img_size)
            img_temp.append(img.copy())
            boxes_temp.append(boxes.copy())
            labels_temp.append(labels.copy())
            judge_box("cut_random", img_path, img, boxes)
        boxes = np.array(boxes)
        try:
            img, boxes = resize_image_and_correct_boxes(img, boxes, img_size)
        except:
            print(boxes)
            img, boxes = resize_image_and_correct_boxes(img, boxes, img_size)
         
        choice = random.sample(choice_list, 1)[0]
        #choice = 1
        if choice == 0:
            img, boxes, labels = flip_rl(img, boxes, labels)
            img_temp.append(img.copy())
            boxes_temp.append(boxes.copy())
            labels_temp.append(labels.copy())
            judge_box("flip_rl", img_path, img, boxes)

        choice = random.sample(choice_list, 1)[0]
        #choice = 1
        if choice == 0:
            img, boxes, labels = flip_ud(img, boxes, labels)
            img_temp.append(img.copy())
            boxes_temp.append(boxes.copy())
            labels_temp.append(labels.copy())
            judge_box("flip_ud", img_path, img, boxes)
        choice = random.sample(choice_list, 1)[0]
        #choice = 1
        if choice == 0:
            img, boxes, labels = rotation_random(img, boxes, labels)
            img_temp.append(img.copy())
            boxes_temp.append(boxes.copy())
            labels_temp.append(labels.copy())
            judge_box("rotation_random", img_path, img, boxes)

        if len(boxes) > 0:
            img, boxes, labels = adjust_box(img_path, img, boxes, labels)

        if use_label_smothing:
            if np.sum((boxes_temp[0] == boxes).astype(int)) == boxes.shape[0] * boxes.shape[1]:
                pass
            else:
                choice = random.sample(choice_list, 1)[0]
                if choice == 0 and len(labels_temp) > 1:
                    id_0, id_1 = random.sample(range(len(labels_temp)), 2)
                    rate = random.choice(range(18,22)) / 10
                    img = 1/rate * img_temp[id_0] + (1-1/rate)*img_temp[id_1]
                    img = np.asarray(img, np.uint8)
                    boxes = np.append(boxes_temp[id_0], boxes_temp[id_1], axis=0)
                    labels = np.append(labels_temp[id_0], labels_temp[id_1], axis=0)
                    confs = np.append(1/rate * confs, (1-1/rate) * confs, axis=0)
                judge_box("label_smothing", img_path, img, boxes)
        choice = random.sample(choice_list, 1)[0]
        #choice = 1
        if choice == 0:
            img = img_addcontrast_brightness(img)
        choice = random.sample(choice_list, 1)[0]
        #choice = 1
        if choice == 0:
            img = img_blur(img)
        choice = random.sample(choice_list, 1)[0]
        #choice = 1
        if choice == 0:
            img = img_addweight(img)
        # choice = random.sample(choice_list, 1)[0]
        # choice = 0
        # if choice == 0:
        #     img = random_change_contrast(img)
        choice = random.sample(choice_list, 1)[0]
        choice = 1
        if choice == 0:
            img = random_color_distort(img)

        # boxes, labels, confs = merge_box(boxes, labels, confs, threshold = 0.2)
    # img = img.astype(np.float32)
    boxes = boxes.astype(np.float32)
    confs = confs.astype(np.float32)

    return img, boxes, labels, confs

# if __name__ == "__main__":
#     # file = "./data/my_data/cotton_val_0428.txt"
#     # datafile = open(file, 'r')
#     while(True):
#         img_size = [640, 640]
#         # lines = ["/media/lantiancug/DATADRIVE1/lantiancug/projects/work/YOLOv3_TensorFlow/imgdata/15579983025632784.png 0 1842 879 2005 1022 0 1658 390 1817 520 0 1774 1326 1921 1372"]
#         lines = ["/mnt/AIdata/images4code2/images/wxmfc/wxmfc-20190509/1/1559184487169644.png 1812,924,2326,1327,0 807,807,1003,1097,0 1032,73,1370,616,0"]
#         for line in lines:
#             # pic_path, boxes, labels = parse_line(line, False)
#             # print(pic_path)
#             # img = cv2.imread(pic_path)
#             line = line.split()
#             img_path = line[0]
#             img = cv2.imread(img_path)
#             # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#             boxes_labels = np.array([np.array(list(map(int, box.split(',')))) for box in line[1:]])
#             boxes = boxes_labels[:, :4]
#             labels = boxes_labels[:, 4]
#             # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#             #
#             # img, boxes = resize_image_and_correct_boxes(img, boxes, img_size)
#             # img = np.asarray(img, np.uint8)
#             img_ori = img.copy()
#             # for i in range(len(boxes)):
#             #     x0, y0, x1, y1 = boxes[i]
#             #     # x0 = x0 * 3264/710
#             #     # x1 = x1 * 3264/710
#             #     # y0 = y0 * 2448/530
#             #     # y1 = y1 * 2448/530
#             #     plot_one_box(img, [x0, y0, x1, y1], label=labels[i], color=[255,255,0])
#             # img = cv2.resize(img, (800, 800))
#             # cv2.imshow('old', img)
#             # cv2.waitKey(0)
#             # do data augmentation here
#             img_ori, boxes, labels, confs = data_augmentation("pic_path", img_ori, boxes, labels, img_size, False)
#             # cv2.imshow('new', img_ori)
#             # cv2.waitKey(0)
#             img_ori = np.asarray(img_ori, np.uint8)
#             img_new = img_ori.copy()
#             # print(boxes.shape)
#             for i in range(len(boxes)):
#                 x0, y0, x1, y1 = boxes[i]
#                 cv2.rectangle(img_new, (int(x0), int(y0)), (int(x1), int(y1)), [255, 255, 0], 2)
#             # img_new = cv2.resize(img_new, (640, 640))
#             cv2.imshow('new', img_new)
#             cv2.waitKey(0)
#
#
if __name__ == "__main__":
    # file = "./data/my_data/cotton_val_0428.txt"
    # datafile = open(file, 'r')
    while(True):
        num_epoch = 0
        img_size = [960, 960]
        # lines = ["/media/lantiancug/DATADRIVE1/lantiancug/projects/work/YOLOv3_TensorFlow/imgdata/15579983025632784.png 0 1842 879 2005 1022 0 1658 390 1817 520 0 1774 1326 1921 1372"]
        # lines = ["/mnt/AIdata/Datas/Cotton/ProcessData/6_20_addnewcotton_from_factory_small/save/newadd/1386.jpg"]
        # lines = open("./data/my_data/cotton_07_26_train.txt")
        lines = ["Q:/images/wxmfc/wxmfc-20190416/1/15597120786935141.JPG 0 1255 2552 1402 2724 0 1255 2099 1402 2209 0 2440 1724 2565 1821 0 1061 1509 1218 1665"]
        for line in lines:
            num_epoch = num_epoch + 1
            print(num_epoch)
            print(line)
            pic_path, boxes, labels = parse_line_old(line, False)
            # print(pic_path)
            img = cv2.imread(pic_path)
            # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            #
            # img, boxes = resize_image_and_correct_boxes(img, boxes, img_size)
            # img = np.asarray(img, np.uint8)
            img_ori = img.copy()
            for i in range(len(boxes)):
                x0, y0, x1, y1 = boxes[i]
                # x0 = x0 * 3264/710
                # x1 = x1 * 3264/710
                # y0 = y0 * 2448/530
                # y1 = y1 * 2448/530
                plot_one_box(img, [x0, y0, x1, y1], label=labels[i], color=[255,255,0])
            img = cv2.resize(img, (800, 800))
            cv2.imshow('old', img)
            # cv2.waitKey(0)
            # do data augmentation hereimg_path, img, boxes, labels, img_size, mode, batch_size, use_label_smothing = False
            img_ori, boxes, labels, confs = data_augmentation(pic_path, img_ori, boxes, labels, img_size, mode = "train", batch_size=2, use_label_smothing =False)
            # cv2.imshow('new', img_ori)
            # cv2.waitKey(0)
            img_ori = np.asarray(img_ori, np.uint8)
            img_new = img_ori.copy()
            # print(boxes.shape)
            for i in range(len(boxes)):
                x0, y0, x1, y1 = boxes[i]
                cv2.rectangle(img_new, (int(x0), int(y0)), (int(x1), int(y1)), [255, 255, 0], 2)
            img_new = cv2.resize(img_new, (800, 800))
            cv2.imshow('new', img_new)
            cv2.waitKey(0)
