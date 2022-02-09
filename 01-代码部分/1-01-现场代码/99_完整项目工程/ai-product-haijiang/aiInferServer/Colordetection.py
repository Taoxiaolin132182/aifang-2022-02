import cv2 as cv
import numpy as np
import copy
import configparser
import os
import time
from shenhuangmao_classify_seresnet50.Classify_model import Model
from shenhuangmao_classify_seresnet50.printlogs import logger
from shenhuangmao_classify_seresnet50.yolov3 import wool_detection

TASK_PY_PATH = os.path.split(os.path.realpath(__file__))[0]


class Colordetection:
    def __init__(self, ):
        conf = configparser.ConfigParser()
        conf.read(os.path.join(TASK_PY_PATH, 'color.cfg'))

        self.zoom = float(conf.get("config", "zoom"))

        lower_backgroud = str(conf.get("config", "lower_backgroud")).split(',')
        self.lower_backgroud = np.array([int(lower_backgroud[0]), int(lower_backgroud[1]), int(lower_backgroud[2])],
                                        dtype=np.uint8)
        upper_backgroud = str(conf.get("config", "upper_backgroud")).split(',')
        self.upper_backgroud = np.array([int(upper_backgroud[0]), int(upper_backgroud[1]), int(upper_backgroud[2])],
                                        dtype=np.uint8)
        self.r_backgroud = int(int(conf.get("config", "r_backgroud")) * self.zoom)

        lower_hei_RGB = str(conf.get("config", "lower_hei_RGB")).split(',')
        self.lower_hei_RGB = np.array([int(lower_hei_RGB[0]), int(lower_hei_RGB[1]), int(lower_hei_RGB[2])],
                                      dtype=np.uint8)
        upper_hei_RGB = str(conf.get("config", "upper_hei_RGB")).split(',')
        self.upper_hei_RGB = np.array([int(upper_hei_RGB[0]), int(upper_hei_RGB[1]), int(upper_hei_RGB[2])],
                                      dtype=np.uint8)
        self.r_hei = int(int(conf.get("config", "r_hei")) * self.zoom)

        lower_qian_RGB = str(conf.get("config", "lower_qian_RGB")).split(',')
        self.lower_qian_RGB = np.array([int(lower_qian_RGB[0]), int(lower_qian_RGB[1]), int(lower_qian_RGB[2])],
                                       dtype=np.uint8)
        upper_qian_RGB = str(conf.get("config", "upper_qian_RGB")).split(',')
        self.upper_qian_RGB = np.array([int(upper_qian_RGB[0]), int(upper_qian_RGB[1]), int(upper_qian_RGB[2])],
                                       dtype=np.uint8)
        self.r_qian = int(int(conf.get("config", "r_qian")) * self.zoom)

        lower_zhong_RGB = str(conf.get("config", "lower_zhong_RGB")).split(',')
        self.lower_zhong_RGB = np.array([int(lower_zhong_RGB[0]), int(lower_zhong_RGB[1]), int(lower_zhong_RGB[2])],
                                        dtype=np.uint8)
        upper_zhong_RGB = str(conf.get("config", "upper_zhong_RGB")).split(',')
        self.upper_zhong_RGB = np.array([int(upper_zhong_RGB[0]), int(upper_zhong_RGB[1]), int(upper_zhong_RGB[2])],
                                        dtype=np.uint8)
        self.r_zhong = int(int(conf.get("config", "r_zhong")) * self.zoom)

        lower_shen_HSV = str(conf.get("config", "lower_shen_HSV")).split(',')
        self.lower_shen_HSV = np.array([int(lower_shen_HSV[0]), int(lower_shen_HSV[1]), int(lower_shen_HSV[2])],
                                       dtype=np.uint8)
        upper_shen_HSV = str(conf.get("config", "upper_shen_HSV")).split(',')
        self.upper_shen_HSV = np.array([int(upper_shen_HSV[0]), int(upper_shen_HSV[1]), int(upper_shen_HSV[2])],
                                       dtype=np.uint8)
        self.r_shen = int(int(conf.get("config", "r_shen")) * self.zoom)

        self.thre_qian_zhong = int(conf.get("config", "thre_qian_zhong"))
        self.thre_zhong_shen1 = int(conf.get("config", "thre_zhong_shen1"))
        self.thre_zhong_shen2 = int(conf.get("config", "thre_zhong_shen2"))
        self.thre_zhong_shen_S = int(conf.get("config", "thre_zhong_shen_S"))
        self.thre_zhong_shen_S1 = int(conf.get("config", "thre_zhong_shen_S1"))
        self.thre_zhong_shen3 = int(conf.get("config", "thre_zhong_shen3"))

        self.thre_area1 = int(int(conf.get("config", "thre_area1")) * self.zoom * self.zoom)
        self.thre_area2 = int(int(conf.get("config", "thre_area2")) * self.zoom * self.zoom)
        self.r_close = int(int(conf.get("config", "r_close")) * self.zoom)

        maskboxA = str(conf.get("config", "maskboxA")).split(',')
        self.maskboxA = np.array(
            [int(int(maskboxA[0]) * self.zoom), int(int(maskboxA[1]) * self.zoom), int(int(maskboxA[2]) * self.zoom),
             int(int(maskboxA[3]) * self.zoom)])
        maskboxB = str(conf.get("config", "maskboxB")).split(',')
        self.maskboxB = np.array(
            [int(int(maskboxB[0]) * self.zoom), int(int(maskboxB[1]) * self.zoom), int(int(maskboxB[2]) * self.zoom),
             int(int(maskboxB[3]) * self.zoom)])
        maskboxC = str(conf.get("config", "maskboxC")).split(',')
        self.maskboxC = np.array(
            [int(int(maskboxC[0]) * self.zoom), int(int(maskboxC[1]) * self.zoom), int(int(maskboxC[2]) * self.zoom),
             int(int(maskboxC[3]) * self.zoom)])

        self.label1 = str(conf.get("config", "label1"))
        self.label2 = str(conf.get("config", "label2"))
        self.label3 = str(conf.get("config", "label3"))

        self.classify_flag = int(conf.get("config", "classify_flag"))

        self.delect_mode = int(conf.get("config_classify", "mode"))
        self.batchsize = int(conf.get("config_classify", "batchsize"))
        self.box_if_fill = int(conf.get("config_classify", "boxiffill"))
        self.box_resize_ratio = float(conf.get("config_classify", "boxresizeratio"))

        self.yolo_model_path_detection = str(conf.get("config_classify", "yolo_model_path_detection"))
        self.yolo_model_path_classify = str(conf.get("config_classify", "yolo_model_path_classify"))
        self.yolo_class_name_path_detection = str(conf.get("config_classify", "yolo_class_name_path_detection"))
        self.yolo_class_name_path_classify = str(conf.get("config_classify", "yolo_class_name_path_classify"))
        self.yolo_do_classify = bool(conf.get("config_classify", "yolo_do_classify"))
        self.yolo_model = None
        self.yolo_model_init = None
        self.yolo_thre = float(conf.get("config_classify", "yolo_thre"))
        self.__yolo_init()

        # logger.info('Colordetection Config:  zoom='+str(self.zoom)+' lower_backgroud='+str(self.lower_backgroud)+' upper_backgroud='+str(self.upper_backgroud))

    def __yolo_init(self):
        self.yolo_model = wool_detection(self.yolo_model_path_detection, self.yolo_class_name_path_detection,
                                         self.yolo_model_path_classify, self.yolo_class_name_path_classify,
                                         self.yolo_do_classify)
        self.yolo_model_init = self.yolo_model.model_init_detection()
        self.yolo_model.forward(np.zeros([2048, 2448, 3], dtype=np.uint8), do_classify=self.yolo_do_classify)

        imglist = []
        for i in range(self.batchsize):
            imglist.append(np.zeros([200, 200, 3], dtype=np.uint8))
        Model.forward(imglist, 0)

    def __calculate_gray_mean(self, img, region):
        region = np.array(region, dtype=np.uint8)
        imgshow = copy.deepcopy(img)
        gray = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
        R = img[:, :, 0]
        G = img[:, :, 1]
        B = img[:, :, 2]
        S = cv.cvtColor(img, cv.COLOR_RGB2HSV)[:, :, 1]
        try:
            contours, _ = cv.findContours(region, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        except:
            __, contours, _ = cv.findContours(region, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        # cv.drawContours(imgshow, contours, -1, (0, 0, 255), 2)
        boxs = []
        labels = []
        for i in range(len(contours)):
            if cv.contourArea(contours[i]) >= self.thre_area2:
                mask = np.zeros(gray.shape, dtype=np.uint8)
                cv.drawContours(mask, contours, i, (1, 1, 1), -1)
                mean_gray = int(np.sum(cv.multiply(mask, gray)) / np.sum(mask))
                mean_S = int(np.sum(cv.multiply(mask, S)) / np.sum(mask))
                mean_R = int(np.sum(cv.multiply(mask, R)) / np.sum(mask))
                mean_G = int(np.sum(cv.multiply(mask, G)) / np.sum(mask))
                mean_B = int(np.sum(cv.multiply(mask, B)) / np.sum(mask))

                # if mean_gray <= self.thre_zhong_shen1 and mean_S >= self.thre_zhong_shen_S:
                if (mean_gray <= self.thre_zhong_shen1 and mean_S >= self.thre_zhong_shen_S) or (
                        mean_gray + mean_S <= self.thre_zhong_shen2 and mean_S >= self.thre_zhong_shen_S1 and mean_gray <= self.thre_zhong_shen3):
                    # if mean_gray <= self.thre_zhong_shen1:

                    labels.append(self.label1)
                    color = (255, 0, 0)
                    box = [int(min(contours[i][:, 0, 0]) / self.zoom), int(min(contours[i][:, 0, 1]) / self.zoom),
                           int(max(contours[i][:, 0, 0]) / self.zoom),
                           int(max(contours[i][:, 0, 1]) / self.zoom)]
                    boxs.append(box)
                    cv.drawContours(imgshow, contours, i, color, 1)
                    cv.putText(imgshow,
                               str(mean_gray) + ' ' + str(mean_S) + ' ' + str(mean_R) + ' ' + str(mean_G) + ' ' + str(
                                   mean_B),
                               (min(contours[i][:, 0, 0]), min(contours[i][:, 0, 1])),
                               cv.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
                # elif mean_gray <= 120:
                #     labels.append(self.label1)
                #     color = (255, 0, 0)
                #     box = [int(min(contours[i][:, 0, 0]) / self.zoom), int(min(contours[i][:, 0, 1]) / self.zoom),
                #            int(max(contours[i][:, 0, 0]) / self.zoom),
                #            int(max(contours[i][:, 0, 1]) / self.zoom)]
                #     boxs.append(box)
                #     cv.drawContours(imgshow, contours, i, (0, 0, 255), 1)
                #     cv.putText(imgshow, str(mean_gray) + ' ' + str(mean_S),
                #                (min(contours[i][:, 0, 0]), min(contours[i][:, 0, 1])),
                #                cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                else:
                    color = (0, 0, 255)
                    cv.drawContours(imgshow, contours, i, color, 1)
                    cv.putText(imgshow,
                               str(mean_gray) + ' ' + str(mean_S) + ' ' + str(mean_R) + ' ' + str(mean_G) + ' ' + str(
                                   mean_B),
                               (min(contours[i][:, 0, 0]), min(contours[i][:, 0, 1])),
                               cv.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
                # elif mean_gray <= self.thre_qian_zhong:
                #     labels.append(self.label2)
                #     color = (0, 255, 0)
                # else:
                #     labels.append(self.label3)
                #     color = (0, 0, 255)
        return imgshow, boxs, labels

    def __get_mask(self, imgHSV, r, yixianboxs, CameraId):
        region_background = cv.inRange(imgHSV, self.lower_backgroud, self.upper_backgroud)
        if r:
            element = cv.getStructuringElement(cv.MORPH_ELLIPSE, (r, r))
            element1 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (r * 2, r * 2))
            region_background = cv.morphologyEx(region_background, cv.MORPH_CLOSE, element)
            region_background = cv.morphologyEx(region_background, cv.MORPH_DILATE, element1)
        try:
            contours, _ = cv.findContours(region_background, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        except:
            __, contours, _ = cv.findContours(region_background, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        mask = np.zeros(region_background.shape, dtype=np.uint8)
        yixianmask = np.zeros(region_background.shape, dtype=np.uint8)
        for yixianbox in yixianboxs:
            cv.rectangle(yixianmask, (int(yixianbox[0] * self.zoom), int(yixianbox[1] * self.zoom)),
                         (int(yixianbox[2] * self.zoom), int(yixianbox[3] * self.zoom)), (1, 1, 1), -1)
        yixianmask = 1 - yixianmask
        Cameramask = np.zeros(region_background.shape, dtype=np.uint8)
        if CameraId == 'A':
            cv.rectangle(Cameramask, (self.maskboxA[0], self.maskboxA[1]), (self.maskboxA[2], self.maskboxA[3]),
                         (1, 1, 1), -1)
        elif CameraId == 'B':
            cv.rectangle(Cameramask, (self.maskboxB[0], self.maskboxB[1]), (self.maskboxB[2], self.maskboxB[3]),
                         (1, 1, 1), -1)
        else:
            cv.rectangle(Cameramask, (self.maskboxC[0], self.maskboxC[1]), (self.maskboxC[2], self.maskboxC[3]),
                         (1, 1, 1), -1)
        mask = cv.drawContours(mask, contours, -1, (1, 1, 1), -1)
        mask = 1 - mask
        # self.__show_img(mask, 'mask1')
        # self.__show_img(yixianmask, 'yixianmask')
        # self.__show_img(Cameramask, 'Cameramask')
        mask = cv.multiply(mask, cv.multiply(yixianmask, Cameramask))
        # self.__show_img(mask, 'mask')
        return mask

    def __get_region(self, img, lower, upper, mask, r):
        region = cv.inRange(img, lower, upper)
        region = cv.multiply(region, mask)
        if r:
            element = cv.getStructuringElement(cv.MORPH_ELLIPSE, (r, r))
            region = cv.morphologyEx(region, cv.MORPH_OPEN, element)
            region = cv.morphologyEx(region, cv.MORPH_CLOSE, element)
            region = cv.morphologyEx(region, cv.MORPH_ERODE, element)
        try:
            contours, _ = cv.findContours(region, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        except:
            __, contours, _ = cv.findContours(region, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        imgshow = np.zeros(img.shape[:2], dtype=np.uint8)
        for i in range(len(contours)):
            if cv.contourArea(contours[i]) >= self.thre_area1:
                cv.drawContours(imgshow, contours, i, (1, 1, 1), -1)
        # element1 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (21, 21))
        # imgshow = cv.morphologyEx(imgshow, cv.MORPH_CLOSE, element1)
        return imgshow

    def __show_img(self, img, name='', zoom=0.5):
        H, W = img.shape[:2]
        imgresize = cv.resize(img, (int(zoom * W), int(zoom * H)), cv.INTER_LINEAR)
        cv.imshow(name, imgresize)

    def __cut_fill_img(self, img, box):
        h, w = img.shape[:2]
        x0, y0, x1, y1 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
        x_c = int((x0 + x1) / 2)
        y_c = int((y0 + y1) / 2)
        W = int((x1 - x0) * self.box_resize_ratio)
        H = int((y1 - y0) * self.box_resize_ratio)

        new_x0 = max(0, int(x_c - W / 2))
        new_y0 = max(0, int(y_c - H / 2))

        new_x1 = min(w, int(x_c + W / 2))
        new_y1 = min(h, int(y_c + H / 2))
        cut_img = img[int(new_y0):int(new_y1), int(new_x0):int(new_x1), :]
        # self.__show_img(cut_img,'cut')
        # print(box, new_x0, new_x1, w, h, W, H)

        if self.box_if_fill:
            H, W = cut_img.shape[:2]
            if W >= H:
                darkmap = np.zeros([W, W, 3], dtype=np.uint8)
                darkmap[int((W - H) / 2):int((W - H) / 2) + H, :, :] = cut_img
            else:
                darkmap = np.zeros([H, H, 3], dtype=np.uint8)
                darkmap[:, int((H - W) / 2):int((H - W) / 2) + W, :] = cut_img
            # self.__show_img(darkmap, 'darkmap')
            # cv.waitKey(0)
            return darkmap
        else:
            return cut_img

    def __classify(self, img_RGB, boxs):
        img = cv.cvtColor(img_RGB, cv.COLOR_RGB2BGR)
        imglist = []
        # labels = []
        # scores = []
        for i in range(self.batchsize):
            if i < len(boxs):
                img_cut = self.__cut_fill_img(img, boxs[i])
            else:
                img_cut = np.zeros([200, 200, 3], dtype=np.uint8)
            imglist.append(img_cut)

        labels, scores = Model.forward(imglist, len(boxs))
        return labels, scores

    def __color_and_seresnet(self, img_rgb, yixianboxs, CameraId):
        labelsout = []
        boxsout = []
        img_RGB = copy.deepcopy(img_rgb)
        H, W = img_RGB.shape[:2]
        img_RGB = cv.resize(img_RGB, (int(W * self.zoom), int(H * self.zoom)))
        img_RGB = cv.bilateralFilter(img_RGB, int(9 * self.zoom), int(75 * self.zoom), int(75 * self.zoom))
        img_HSV = cv.cvtColor(img_RGB, cv.COLOR_RGB2HSV)
        mask = self.__get_mask(img_HSV, self.r_backgroud, yixianboxs, CameraId)
        shenimgshow = self.__get_region(img_HSV, self.lower_shen_HSV, self.upper_shen_HSV, mask, self.r_shen)
        blackimgshow = self.__get_region(img_RGB, self.lower_hei_RGB, self.upper_hei_RGB, mask, self.r_hei)
        imgand = (shenimgshow + blackimgshow) * 255
        # self.__show_img(imgand, 'imgand', 0.4 / self.zoom)
        img_show, boxs, labels = self.__calculate_gray_mean(img_RGB, imgand)
        # print(boxs, labels)
        logger.info('Colordetect output:' + str(boxs) + str(labels))
        if self.classify_flag:
            if len(boxs):
                labels, scores = self.__classify(img_rgb, boxs)
                # print(labels, scores)
                logger.info('Classify model output:' + str(boxs) + str(labels) + str(scores))
            for i, label in enumerate(labels):
                if label == self.label1:
                    labelsout.append(label)
                    boxsout.append(boxs[i])
        else:
            labelsout = labels
            boxsout = boxs
        # print(0,boxsout,labelsout)
        return boxsout, labelsout

    def __yolov3(self, img_rgb, CameraId):
        labelsout = []
        boxsout = []
        Cameramask = np.zeros(img_rgb.shape, dtype=np.uint8)
        if CameraId == 'A':
            cv.rectangle(Cameramask, (int(self.maskboxA[0] / self.zoom), int(self.maskboxA[1] / self.zoom)),
                         (int(self.maskboxA[2] / self.zoom), int(self.maskboxA[3] / self.zoom)),
                         (1, 1, 1), -1)
        elif CameraId == 'B':
            cv.rectangle(Cameramask, (int(self.maskboxB[0] / self.zoom), int(self.maskboxB[1] / self.zoom)),
                         (int(self.maskboxB[2] / self.zoom), int(self.maskboxB[3] / self.zoom)),
                         (1, 1, 1), -1)
        else:
            cv.rectangle(Cameramask, (int(self.maskboxC[0] / self.zoom), int(self.maskboxC[1] / self.zoom)),
                         (int(self.maskboxC[2] / self.zoom), int(self.maskboxC[3] / self.zoom)),
                         (1, 1, 1), -1)
        boxes_detection, scores_detection, labels_detection_name, scores_classify, labels_classify_name = self.yolo_model.forward(
            cv.cvtColor(img_rgb, cv.COLOR_RGB2BGR), do_classify=self.yolo_do_classify)
        boxes_detection = list(boxes_detection)
        scores_detection = list(scores_detection)
        for i, box in enumerate(boxes_detection):
            # if scores_detection[i] >= self.yolo_thre:
            if scores_detection[i] >= self.yolo_thre and Cameramask[
                int((box[1] + box[3]) / 2), int((box[0] + box[2]) / 2), 0]:
                boxsout.append([int(box[0]), int(box[1]), int(box[2]), int(box[3])])
                labelsout.append(self.label1)
        # print(1,boxsout,labelsout)
        return boxsout, labelsout

    def detect(self, img_rgb, yixianboxs, CameraId):
        # labelsout = []
        # boxsout = []
        if self.delect_mode == 0:
            boxsout, labelsout = self.__color_and_seresnet(img_rgb, yixianboxs, CameraId)

        elif self.delect_mode == 1:
            boxsout, labelsout = self.__yolov3(img_rgb, CameraId)
            if len(boxsout) > 0:
                logger.info('Yolov3 model output:' + str(boxsout) + str(labelsout))
        else:
            boxs1, labels1 = self.__color_and_seresnet(img_rgb, yixianboxs, CameraId)
            boxs2, labels2 = self.__yolov3(img_rgb, CameraId)
            boxsout = boxs1 + boxs2
            labelsout = labels1 + labels2
        # self.__show_img(cv.cvtColor(img_show, cv.COLOR_RGB2BGR), 'img_show', 0.4 / self.zoom)

        # print(boxsout, labelsout)
        return boxsout, labelsout


Cal = Colordetection()
