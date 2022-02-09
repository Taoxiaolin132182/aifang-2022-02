import numpy as np
import os
import cv2 as cv
import time
import configparser


def write_camerapars(path, mtx1, dist1, mtx2, dist2, mtx3, dist3):
    mtx1 = str(mtx1[0, 0]) + ',' + str(mtx1[0, 1]) + ',' + str(mtx1[0, 2]) + ',' + str(mtx1[1, 0]) + ',' + str(
        mtx1[1, 1]) + ',' + str(mtx1[1, 2]) + ',' + str(mtx1[2, 0]) + ',' + str(mtx1[2, 1]) + ',' + str(mtx1[2, 2])
    dist1 = str(dist1[0, 0]) + ',' + str(dist1[0, 1]) + ',' + str(dist1[0, 2]) + ',' + str(dist1[0, 3]) + ',' + str(
        dist1[0, 4])
    mtx2 = str(mtx2[0, 0]) + ',' + str(mtx2[0, 1]) + ',' + str(mtx2[0, 2]) + ',' + str(mtx2[1, 0]) + ',' + str(
        mtx2[1, 1]) + ',' + str(mtx2[1, 2]) + ',' + str(mtx2[2, 0]) + ',' + str(mtx2[2, 1]) + ',' + str(mtx2[2, 2])
    dist2 = str(dist2[0, 0]) + ',' + str(dist2[0, 1]) + ',' + str(dist2[0, 2]) + ',' + str(dist2[0, 3]) + ',' + str(
        dist2[0, 4])
    mtx3 = str(mtx3[0, 0]) + ',' + str(mtx3[0, 1]) + ',' + str(mtx3[0, 2]) + ',' + str(mtx3[1, 0]) + ',' + str(
        mtx3[1, 1]) + ',' + str(mtx3[1, 2]) + ',' + str(mtx3[2, 0]) + ',' + str(mtx3[2, 1]) + ',' + str(mtx3[2, 2])
    dist3 = str(dist3[0, 0]) + ',' + str(dist3[0, 1]) + ',' + str(dist3[0, 2]) + ',' + str(dist3[0, 3]) + ',' + str(
        dist3[0, 4])




    conf = configparser.ConfigParser()
    cfgfile = open(path, 'w')
    conf.add_section("Camera_Config")
    conf.set("Camera_Config", "mtx1", mtx1)
    conf.set("Camera_Config", "dist1", dist1)
    conf.set("Camera_Config", "rvec1", '0.0,0.0,0.0')
    conf.set("Camera_Config", "tvec1", '0.0,0.0,0.0')

    conf.set("Camera_Config", "mtx2", mtx2)
    conf.set("Camera_Config", "dist2", dist2)
    conf.set("Camera_Config", "rvec2", '0.0,0.0,0.0')
    conf.set("Camera_Config", "tvec2", '0.0,0.0,0.0')

    conf.set("Camera_Config", "mtx3", mtx3)
    conf.set("Camera_Config", "dist3", dist3)
    conf.set("Camera_Config", "rvec3", '0.0,0.0,0.0')
    conf.set("Camera_Config", "tvec3", '0.0,0.0,0.0')

    conf.write(cfgfile)
    cfgfile.close()
    return


def stereo_calibrate():
    start_time = time.process_time()
    input_path = './images/'
    output_path = './output/'
    ctrl1 = []  # 相机参数控制
    # ctrl2 = ['mtx1', 'dist1', 'mtx2', 'dist2', 'mtx3', 'dist3']
    criteria = (cv.TERM_CRITERIA_EPS + cv.TermCriteria_MAX_ITER, 13, 0.09)
    x_nums = 11
    y_nums = 8
    world_point = np.zeros((x_nums * y_nums, 3), np.float32)
    world_point[:, :2] = np.mgrid[0:0.30:11j, 0:0.21:8j].T.reshape(-1, 2)

    try:
        for pathlist in os.listdir(input_path):  # 分 每个相机代号
            path001 = os.path.join(output_path, pathlist)  # 结果路径-每个相机路径
            if not os.path.exists(output_path):  # 创建 结果路径
                os.makedirs(output_path)
            if not os.path.exists(path001):  # 创建 结果路径 -每个相机路径
                os.makedirs(path001)
            world_position = []
            image_position = []
            j = 0
            list1 = os.listdir(os.path.join(input_path, pathlist))  # 分 该相机下的 每张图
            print(len(list1))
            if len(list1) < 2:
                print("相机{}无图片".format(pathlist))
                continue
            for path in list1:
                time1 = time.process_time()
                filepath = os.path.join(os.path.join(input_path, pathlist), path)
                print((filepath))
                img = cv.imread(filepath)
                height, width = img.shape[:2]
                gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
                ret, corners = cv.findChessboardCorners(gray, (x_nums, y_nums), flags=cv.CALIB_CB_ADAPTIVE_THRESH)
                print(ret)
                if ret:
                    j += 1
                    world_position.append(world_point)
                    corners_SubPix = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                    image_position.append(corners_SubPix)
                    cv.drawChessboardCorners(img, (x_nums, y_nums), corners_SubPix, ret)
                    cv.imwrite(os.path.join(os.path.join(output_path, pathlist), path), img)
                print(int(time.process_time() - time1), 's')

            # print("步骤1，完成")
            if pathlist == '1':
                ctrl1.append(1)
                ret1, mtx1, dist1, rvecs1, tvecs1 = cv.calibrateCamera(world_position, image_position, (width, height),
                                                                       None, None)
            elif pathlist == '2':
                ctrl1.append(2)
                ret2, mtx2, dist2, rvecs2, tvecs2 = cv.calibrateCamera(world_position, image_position, (width, height),
                                                                       None, None)
                # print('mtx2',mtx2)
                # print('dist2',dist2)
            elif pathlist == '3':
                ctrl1.append(3)
                ret3, mtx3, dist3, rvecs3, tvecs3 = cv.calibrateCamera(world_position, image_position, (width, height),
                                                                       None, None)
        print('相机参数控制',ctrl1)

        if 1 not in ctrl1:
            # print(1)
            mtx1, dist1 = np.zeros(9).reshape(3,3),np.zeros(5).reshape(1,5)
        if 2 not in ctrl1:
            # print(2)
            mtx2, dist2 = np.zeros(9).reshape(3,3),np.zeros(5).reshape(1,5)
        if 3 not in ctrl1:
            # print(3)
            mtx3, dist3 = np.zeros(9).reshape(3,3),np.zeros(5).reshape(1,5)
        write_camerapars('output/camera_pars.cfg', mtx1, dist1, mtx2, dist2, mtx3, dist3)
        print('Save camera parameters FINISH')
        print(int(time.process_time() - start_time), 's')
    except:
        print('ERROR: Calibration FAIL')


if __name__ == '__main__':
    # cd = np.zeros(9).reshape(1,9)
    # print(cd)
    stereo_calibrate()
