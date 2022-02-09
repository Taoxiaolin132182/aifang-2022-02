import cv2 as cv
import numpy as np


class fluorescence_detection():
    def __init__(self):
        self.element_size = 11
        self.element = cv.getStructuringElement(cv.MORPH_ELLIPSE, (self.element_size, self.element_size))
        self.zoom = 0.2
        # self.bin_thre = 120
        self.area_thre = self.element_size ** 2 * 2

    def detect(self, img_ori, bin_thre=130):
        # self.bin_thre = bin_thre
        boxesout = []
        h, w = img_ori.shape[:2]
        img = cv.resize(img_ori, (int(self.zoom * w), int(self.zoom * h)), cv.INTER_NEAREST)
        channel_b = img[:, :, 0]
        channel_b1 = cv.morphologyEx(channel_b, cv.MORPH_DILATE, self.element)
        channel_b2 = (np.square((channel_b1.astype(float) / 255)) * 255).astype(np.uint8)
        # _, bin = cv.threshold(channel_b2, self.bin_thre, 255, cv.THRESH_BINARY)
        _, bin = cv.threshold(channel_b2, bin_thre, 255, cv.THRESH_BINARY)
        contours, _ = cv.findContours(bin, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x0 = int(np.min(contour[:, 0, 0]) / self.zoom)
            y0 = int(np.min(contour[:, 0, 1]) / self.zoom)
            x1 = int(np.max(contour[:, 0, 0]) / self.zoom)
            y1 = int(np.max(contour[:, 0, 1]) / self.zoom)
            if (x1 - x0) * (y1 - y0) >= self.area_thre:
                boxesout.append([x0, y0, x1, y1])
        return boxesout


FD = fluorescence_detection()
