import cv2
import os
import sys
import numpy as np
import copy



def delete_background(image):
    kernel = np.ones((40, 40), np.uint8)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image_channel = gray
    background_region = np.asarray(np.where(image_channel < 40, 0, 1) * 255, np.uint8)
    background_region = cv2.erode(background_region, kernel=kernel, iterations=1)
    background_region = cv2.dilate(background_region, kernel=kernel, iterations=1)
    # cv2.imshow("background_region_1", cv2.resize(background_region, (800, 800)))
    background_region = background_region[..., np.newaxis]
    background_region = np.concatenate([background_region, background_region, background_region], axis=-1)
    cv2.imshow("background_region", cv2.resize(background_region, (800, 800)))
    background_region = background_region / 255
    image = image * background_region
    image = image + (255 - background_region*255)
    image = np.asarray(image, np.uint8)
    return image

img_path = "/opt/data/temp/120243891588055248536.7456.jpg"
image_ori = cv2.imread(img_path)
image = copy.deepcopy(image_ori)
cv2.imshow("ori", cv2.resize(image, (800, 800)))
image = delete_background(image)
image = cv2.resize(image, (800, 800))
cv2.imshow("result", image)
cv2.waitKey(0)