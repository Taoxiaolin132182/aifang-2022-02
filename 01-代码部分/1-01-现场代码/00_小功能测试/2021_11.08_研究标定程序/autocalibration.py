from numpy import *
import numpy as np
import cv2 as cv
import configparser

configpath = 'camera_pars.cfg'
# 相机内外参读取算子
def load_data(path):
    conf = configparser.ConfigParser()
    conf.read(path)
    mtx1 = conf.get("Camera_Config", "mtx1").split(',')
    mtx1 = np.array([[float(mtx1[0]), float(mtx1[1]), float(mtx1[2])],
                     [float(mtx1[3]), float(mtx1[4]), float(mtx1[5])],
                     [float(mtx1[6]), float(mtx1[7]), float(mtx1[8])]])
    dist1 = conf.get("Camera_Config", "dist1").split(',')
    dist1 = np.array([float(dist1[0]), float(dist1[1]), float(dist1[2]), float(dist1[3]), float(dist1[4])])
    rvec1 = conf.get("Camera_Config", "rvec1").split(',')
    rvec1 = np.array([[float(rvec1[0])], [float(rvec1[1])], [float(rvec1[2])]])
    tvec1 = conf.get("Camera_Config", "tvec1").split(',')
    tvec1 = np.array([[float(tvec1[0])], [float(tvec1[1])], [float(tvec1[2])]])

    mtx2 = conf.get("Camera_Config", "mtx2").split(',')
    mtx2 = np.array([[float(mtx2[0]), float(mtx2[1]), float(mtx2[2])],
                     [float(mtx2[3]), float(mtx2[4]), float(mtx2[5])],
                     [float(mtx2[6]), float(mtx2[7]), float(mtx2[8])]])
    dist2 = conf.get("Camera_Config", "dist2").split(',')
    dist2 = np.array([float(dist2[0]), float(dist2[1]), float(dist2[2]), float(dist2[3]), float(dist2[4])])
    rvec2 = conf.get("Camera_Config", "rvec2").split(',')
    rvec2 = np.array([[float(rvec2[0])], [float(rvec2[1])], [float(rvec2[2])]])
    tvec2 = conf.get("Camera_Config", "tvec2").split(',')
    tvec2 = np.array([[float(tvec2[0])], [float(tvec2[1])], [float(tvec2[2])]])

    mtx3 = conf.get("Camera_Config", "mtx3").split(',')
    mtx3 = np.array([[float(mtx3[0]), float(mtx3[1]), float(mtx3[2])],
                     [float(mtx3[3]), float(mtx3[4]), float(mtx3[5])],
                     [float(mtx3[6]), float(mtx3[7]), float(mtx3[8])]])
    dist3 = conf.get("Camera_Config", "dist3").split(',')
    dist3 = np.array([float(dist3[0]), float(dist3[1]), float(dist3[2]), float(dist3[3]), float(dist3[4])])
    rvec3 = conf.get("Camera_Config", "rvec3").split(',')
    rvec3 = np.array([[float(rvec3[0])], [float(rvec3[1])], [float(rvec3[2])]])
    tvec3 = conf.get("Camera_Config", "tvec3").split(',')
    tvec3 = np.array([[float(tvec3[0])], [float(tvec3[1])], [float(tvec3[2])]])
    configflag = True

    return configflag, mtx1, dist1, rvec1, tvec1, mtx2, dist2, rvec2, tvec2, mtx3, dist3, rvec3, tvec3


def write_data(tvec, rvec, path, camera_No):
    conf = configparser.ConfigParser()
    conf.read(path)
    if camera_No == 1:
        conf.set("Camera_Config", "tvec1", tvec)
        conf.set("Camera_Config", "rvec1", rvec)
    elif camera_No == 2:
        conf.set("Camera_Config", "tvec2", tvec)
        conf.set("Camera_Config", "rvec2", rvec)
    elif camera_No == 3:
        conf.set("Camera_Config", "tvec3", tvec)
        conf.set("Camera_Config", "rvec3", rvec)
    conf.write(open(path, "w"))
    return


def calibration_photo(path, camera_No):
    par_path = 'camera_pars.cfg'
    configflag, mtx1, dist1, rvec1, tvec1, mtx2, dist2, rvec2, tvec2, mtx3, dist3, rvec3, tvec3 = load_data(configpath)
    if camera_No == 1:
        mtx = mtx1
        dist = dist1
    elif camera_No == 2:
        mtx = mtx2
        dist = dist2
    elif camera_No == 3:
        mtx = mtx3
        dist = dist3

    criteria = (cv.TERM_CRITERIA_EPS + cv.TermCriteria_MAX_ITER, 13, 0.09)
    x_nums = 11
    y_nums = 8

    world_point = np.zeros((x_nums * y_nums, 3), np.float32)
    world_point[:, :2] = np.mgrid[0:0.3:11j, 0:0.21:8j].T.reshape(-1, 2)

    img = cv.imread(path)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    _, corners = cv.findChessboardCorners(gray, (11, 8), flags=cv.CALIB_CB_ADAPTIVE_THRESH)
    corners_SubPix = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
    cv.drawChessboardCorners(img, (x_nums, y_nums), corners_SubPix, _)
    cv.imwrite('output/' + str(camera_No) + '.jpg', img)
    _, rvec, tvec = cv.solvePnP(world_point, corners_SubPix, mtx, dist, flags=cv.SOLVEPNP_UPNP)

    # rvec = np.around(rvec, decimals=4)
    # tvec = np.around(tvec, decimals=4)

    print('平移向量',tvec)
    print('旋转向量',rvec)
    # tvec = str(tvec[0]) + ',' + str(tvec[1]) + ',' + str(tvec[2])
    # rvec = str(rvec[0, 0]) + ',' + str(rvec[1, 0]) + ',' + str(rvec[2, 0])
    # print('平移向量111', tvec)
    # print('旋转向量111', rvec)
    tvec = str(tvec[0, 0]) + ',' + str(tvec[1, 0]) + ',' + str(tvec[2, 0])
    rvec = str(rvec[0, 0]) + ',' + str(rvec[1, 0]) + ',' + str(rvec[2, 0])

    write_data(tvec, rvec, par_path, camera_No)


if __name__ == '__main__':
    img_No = 1
    calibration_photo('input/1.jpg', 1)
    calibration_photo('input/2.jpg', 2)
    calibration_photo('input/3.jpg', 3)
