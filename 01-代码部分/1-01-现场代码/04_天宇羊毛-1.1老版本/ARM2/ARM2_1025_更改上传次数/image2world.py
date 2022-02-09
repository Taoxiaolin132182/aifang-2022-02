#coding:utf-8
from numpy import *
import numpy as np
import configparser
import cv2 as cv

#低处相机模组，后段
#1-相机A，2-相机C，3-相机B
# pxy_add1 = [[155,-759],[1355,-759],[755,-759]]#与支架某一个固定点距离
# pxy_add1_a = [395,-185]#支架与固定点单位距离
# pxy_add2 = [[7.5,4.5],[-5.8,4.3],[0,0]]#相机之间由于世界坐标换算出现的误差--补偿值
# pxy_add1 = [[147,-768],[1347,-768],[747,-768]]#与支架某一个固定点距离
# pxy_add1_a = [395,-185]#支架与固定点单位距离
'''yuxin_2020_10_19'''
'''X总长707.6mm,Y总长580mm,AB之间图像重合96.1mm,BC之间图像重合108.6mm'''
'''镜头到传送带的距离为660，提高50mm标定，实际工作距离630mm,相机之间605mm'''
'''相机ABC排布，3颗相机对应的坐标系与PLC抓手X相反，Y同向'''
'''B点世界（0，0）像素坐标对应点，，到与支架前部内框点（近电柜处）某一个固定点距离（762,316）'''
'''AB距离611.5mm，BC距离599mm(由3颗相机拍一组卷尺换算长度得到数据（x=1224时的卷尺读数差）)'''
pxy_add1 = [[150.5,316 + 205],[1361,316 + 190],[762,316 + 190]]#与支架前部内框点（近电柜处）某一个固定点距离
# pxy_add1 = [[0,0],[0,0],[0,0]]#与支架前部内框点（近电柜处）某一个固定点距离
pxy_add1_a = [203,1099]#支架与固定点单位距离
#用中间相机的图给AC相机标外参，补偿值近乎0
pxy_add2 = [[-15,0],[-25,0],[-15,0]]#相机之间由于世界坐标换算出现的误差--补偿值（）
mtxa = [np.array([]),np.array([]),np.array([]),np.array([]),np.array([])]
mtxb = ['mtx1','mtx2','mtx3','mtx4','mtx5']
dista = [np.array([]),np.array([]),np.array([]),np.array([]),np.array([])]
distb = ['dist1','dist2','dist3','dist4','dist5']
rveca = [np.array([]),np.array([]),np.array([]),np.array([]),np.array([])]
rvecb = ['rvec1','rvec2','rvec3','rvec4','rvec5']
tveca = [np.array([]),np.array([]),np.array([]),np.array([]),np.array([])]
tvecb = ['tvec1','tvec2','tvec3','tvec4','tvec5']
buchongXY = [0,0,0,0,0,0]
buchongName = ['X1','Y1','X2','Y2','X3','Y3']
configflag = False
configpath = 'camera_pars.cfg'
configpath1 = 'distance_compensate.cfg'
camera_count1 = len(mtxa)
print(camera_count1)
# 相机内外参读取算子
def load_data(path):
    global camera_count1
    path2 = configpath1
    # print(camera_count1)
    configflag = False
    panding1 = True
    jishu01 = 0
    conf = configparser.ConfigParser()
    conf.read(path)
    while panding1:
        jishu01 += 1
        try:
            for i in range(camera_count1):
                mtxa[i] = conf.get("Camera_Config", mtxb[i]).split(',')
                mtxa[i] = np.array([[float(mtxa[i][0]), float(mtxa[i][1]), float(mtxa[i][2])],
                                 [float(mtxa[i][3]), float(mtxa[i][4]), float(mtxa[i][5])],
                                 [float(mtxa[i][6]), float(mtxa[i][7]), float(mtxa[i][8])]])
                dista[i] = conf.get("Camera_Config", distb[i]).split(',')
                dista[i] = np.array([float(dista[i][0]), float(dista[i][1]), float(dista[i][2]), float(dista[i][3]), float(dista[i][4])])
                rveca[i] = conf.get("Camera_Config", rvecb[i]).split(',')
                rveca[i] = np.array([[float(rveca[i][0])], [float(rveca[i][1])], [float(rveca[i][2])]])
                tveca[i] = conf.get("Camera_Config", tvecb[i]).split(',')
                tveca[i] = np.array([[float(tveca[i][0])], [float(tveca[i][1])], [float(tveca[i][2])]])


            configflag = True
            panding1 = False
        except:
            configflag = False
            camera_count1 = 3
            if jishu01 < 2:
                panding1 = True
            else:
                panding1 = False
    # try:
    conf1 = configparser.ConfigParser()
    conf1.read(path2)
    for j in range(3):
        buchongXY[j * 2] = float(conf1.get('Distance', buchongName[j * 2]))
        buchongXY[j * 2 + 1] = float(conf1.get('Distance', buchongName[j * 2 + 1]))
    print("casnhu:",buchongXY)
    # except:
    #     print('cuowu')
    #     buchongXY = [0,0,0,0,0,0]
    # print(mtxa)
    return configflag, mtxa, dista, rveca, tveca,buchongXY


# ******************************************************************
# 单目:像素坐标==》相机坐标
def pixal2camera(Pp, mtx, dist):
    k1 = dist[0]
    k2 = dist[1]
    k3 = dist[4]
    p1 = dist[2]
    p2 = dist[3]

    _Mc0 = np.linalg.inv(mtx)
    Pc = np.dot(_Mc0, Pp)
    r2 = pow(Pc[0], 2) + pow(Pc[1], 2)
    x1 = Pc[0]
    y1 = Pc[1]
    # Pc[0] = x1 * (1 + k1 * r2 + k2 * pow(r2, 2) + k3 * pow(r2, 3)) + 2 * p1 * x1 * y1 + p2 * (r2 + 2 * x1 * x1)
    # Pc[1] = y1 * (1 + k1 * r2 + k2 * pow(r2, 2) + k3 * pow(r2, 3)) + p1 * (r2 + 2 * y1 * y1) + 2 * p2 * x1 * y1

    Pc[0] = x1 * (1 - k1 * r2 - k2 * pow(r2, 2) - k3 * pow(r2, 3)) - 2 * p1 * x1 * y1 - p2 * (r2 + 2 * x1 * x1)
    Pc[1] = y1 * (1 - k1 * r2 - k2 * pow(r2, 2) - k3 * pow(r2, 3)) - p1 * (r2 + 2 * y1 * y1) - 2 * p2 * x1 * y1
    return Pc


# 单目:相机坐标==》世界坐标
def camera2world(Pc, tvec, rvec, h):
    R = cv.Rodrigues(rvec)[0]

    R_T = np.append(R, tvec, axis=1)
    R_T = np.append(R_T, [[0, 0, 0, 1]], axis=0)
    A = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, h / 1000], [0, 0, 0, 1]])

    S = np.dot(R_T, A)[:3, :]

    S = np.append(S[:, :2], S[:, 3:], axis=1)
    _S = np.linalg.inv(S)
    Pw = np.dot(_S, Pc)
    X = Pw[0] / Pw[2] * 1000
    Y = Pw[1] / Pw[2] * 1000

    return X, Y


# 单目:获取3D投影坐标
def image_points_to_world_plane(x, y, camera_No, h=0):
    global configflag, mtxa, dista, rveca, tveca,buchongXY
    if not configflag:
        configflag, mtxa, dista, rveca, tveca,buchongXY = load_data(configpath)
    try:
        # 读取相机参数文件
        for i in range(len(mtxa)):
            if camera_No == i+1:
                mtx = mtxa[i]
                dist = dista[i]
                rvec = rveca[i]
                tvec = tveca[i]
                Xa = buchongXY[i*2]
                Ya = buchongXY[i*2+1]
                # print("X:{},Y:{}".format(Xa,Ya))
    except Exception:
        # print('ERROR: Load camera_par fault')
        X = None
        Y = None
        Z = None
        return X, Y, Z
    try:
        Pp = np.ones([3])
        Pp[0] = x
        Pp[1] = y
        Pc = pixal2camera(Pp.T, mtx, dist)
        X, Y = camera2world(Pc, tvec, rvec, h)
        X1 = X + pxy_add2[camera_No-1][0]
        Y1 = Y + pxy_add2[camera_No-1][1]
        X = X1 + pxy_add1[camera_No-1][0] + pxy_add1_a[0]
        Y = -pxy_add1[camera_No - 1][1] + Y1 + pxy_add1_a[1]
        # X,Y = abs(X)+Xa,abs(Y)+Ya
        X, Y = X + Xa, Y + Ya
        Z = h
    except Exception:
        # print('ERROR: Input error')
        X = None
        Y = None
        Z = None

    return X, Y, Z


# ******************************************************************
# 双目:获取内外参矩阵
def get_R_T(rvec, tvec):
    R = cv.Rodrigues(rvec)[0]
    R_T = np.append(R, tvec, axis=1)
    return R_T


# 双目:畸变矫正
def LensDistortionCorrection(Pp, dist, mtx):
    k1 = dist[0]
    k2 = dist[1]
    p1 = dist[2]
    p2 = dist[3]
    k3 = dist[4]

    _mtx = np.linalg.inv(mtx)
    Pc = np.dot(_mtx, Pp)
    r2 = pow(Pc[0], 2) + pow(Pc[1], 2)
    x1 = Pc[0]
    y1 = Pc[1]
    Pc[0] = x1 * (1 + k1 * r2 + k2 * pow(r2, 2) + k3 * pow(r2, 3)) + 2 * p1 * x1 * y1 + p2 * (r2 + 2 * x1 * x1)
    Pc[1] = y1 * (1 + k1 * r2 + k2 * pow(r2, 2) + k3 * pow(r2, 3)) + p1 * (r2 + 2 * y1 * y1) + 2 * p2 * x1 * y1
    return Pc


# 双目:获取3D坐标
def get_point_3D(pxA, pyA, camera_NoA, pxB, pyB, camera_NoB):
    global configflag, mtxa, dista, rveca, tveca
    if not configflag:
        configflag, mtxa, dista, rveca, tveca = load_data(configpath)
    PpA = np.array([[pxA], [pyA], [1]])
    PpB = np.array([[pxB], [pyB], [1]])
    try:
        # 读取相机参数文件
        for i in range(len(mtxa)):
            if camera_NoA == i + 1:
                mtxA1 = mtxa[i]
                distA1 = dista[i]
                rvecA1 = rveca[i]
                tvecA1 = tveca[i]
            if camera_NoB == i + 1:
                mtxB1 = mtxa[i]
                distB1 = dista[i]
                rvecB1 = rveca[i]
                tvecB1 = tveca[i]

    except Exception:
        # print('ERROR: Load camera_par fault')
        X = None
        Y = None
        Z = None
        return X, Y, Z
    try:
        # 解析并获得参数
        R_TA = get_R_T(rvecA1, tvecA1)
        R_TB = get_R_T(rvecB1, tvecB1)

        PcA = LensDistortionCorrection(PpA, distA1, mtxA1)
        PcB = LensDistortionCorrection(PpB, distB1, mtxB1)

        PpA = np.dot(mtxA1, PcA)
        PpB = np.dot(mtxB1, PcB)
        mtx_R_TA = np.dot(mtxA1, R_TA)
        mtx_R_TB = np.dot(mtxB1, R_TB)
        Pw = cv.triangulatePoints(mtx_R_TA, mtx_R_TB, (PpA[0, 0], PpA[1, 0]), (PpB[0, 0], PpB[1, 0]))
        Pw = Pw / Pw[3]
        X = float(Pw[0] * 1000)
        Y = float(Pw[1] * 1000)
        Z = float(Pw[2] * 1000)
    except Exception:
        print('ERROR: Input error')
        X = None
        Y = None
        Z = None

    return X, Y, Z


# 测试函数
def image_points_to_world_plane_mock(x, y, camera_No, h):
    return 1.0, 2.0, 3.0
#end def


if __name__ == '__main__':
    # point001 = [[0,1024],
    #             [2448,1024],
    #             [0,0],
    #             [2448,0]]
    point001 = [[647, 791],
                [1751, 793],
                [1746, 1566],
                [648, 1559]]
    # point001 = [[0,1024],
    #             [2448,1024],
    #             [1224,0],
    #             [1224,2048]]
    # point001 = [[2084.625,39.83333337306976],
    #             [2102.15625, 1646.666748046875],
    #             [1702, 1460],
    #             [629, 1466]]
    for j in range(1,4):
        print("-----------------------")
        print("相机{}的点位如下：".format(j))
        for i in range(4):
            x,y,z = image_points_to_world_plane(point001[i][0],point001[i][1],j,0)
            pw = [x,y,z]
            print('世界坐标：',pw)