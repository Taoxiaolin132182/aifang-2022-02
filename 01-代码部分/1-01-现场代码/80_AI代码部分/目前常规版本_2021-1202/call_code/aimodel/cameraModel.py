# camera
from dfkGetPhotoArr.dfk_get_photo_arr import DfsGetPhoto
import cv2
import datetime
import os
from torchvision import transforms as TT
from multiprocessing.dummy import Pool as processPool
from aimodel.modelInfer import *


class camera_model:
    def __init__(self, model_config):
        # 摄像头数据 {sn: [imgdata, saveName, img_data_process]}
        self.cameraData = {}
        self.sns = None
        self.dfsGetPhoto = None
        self.model_config = model_config
        # 图像处理进程
        self.poolPicProcess = None
        # 图像保存进程
        self.poolPicSave = None

    def cameraInit(self):
        retObj = {"return_code": 0, "return_message": "cameraInit successful"}
        self.dfsGetPhoto = DfsGetPhoto()
        self.dfsGetPhoto.camera_init()
        enumSerials = self.dfsGetPhoto.enumSerials  # 枚举所有摄像头的串号
        initSerials = self.dfsGetPhoto.initSerials  # 初始化成功的摄像头串号

        if initSerials != enumSerials:
            dif = [y for y in (enumSerials) if y not in initSerials]
            retObj["return_code"] = 1
            retObj["return_message"] = "camera %s init failed" % str(dif)
        # 保存初始化成功的摄像头串号
        self.sns = initSerials
        for sn in self.sns:
            # cameraData[sn] = [None, None]  # img imgname
            self.cameraData[sn] = [None, None, None]  # img imgname, data_prcess_img
        # 图片处理进程
        cameraNum = len(self.sns)
        self.poolPicProcess = processPool(cameraNum)
        # 图片保存进程
        self.poolPicSave = processPool(cameraNum)
        return retObj

    def takePic(self):
        # retObj = {"return_code": 0, "return_message": "takePic successful"}
        images = self.dfsGetPhoto.thread_get_photo(self.sns)
        dt_ms = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
        save_pic_name = []

        inputImgSize = self.model_config["model_detection_core"]["image_input_size"]
        inputs = [{"img": images[i], "inputsize": inputImgSize} for i in range(len(self.sns))]
        img_detection = self.poolPicProcess.map(atssPicProcess, inputs)

        for i, sn in enumerate(self.sns):
            saveName = "camera" + sn + "_" + dt_ms + ".jpg"
            self.cameraData[sn][0] = images[i]
            self.cameraData[sn][1] = saveName
            self.cameraData[sn][2] = img_detection[i]

            save_pic_name.append(saveName)

        # retObj["data"] = save_pic_name
        return save_pic_name

    def takePic_back(self):
        # retObj = {"return_code": 0, "return_message": "takePic successful"}
        images = self.dfsGetPhoto.thread_get_photo(self.sns)
        dt_ms = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
        save_pic_name = []
        for i, sn in enumerate(self.sns):
            saveName = "camera" + sn + "_" + dt_ms + ".jpg"
            self.cameraData[sn][0] = images[i]
            self.cameraData[sn][1] = saveName
            # 数据处理: 得根据不同的检测模型来进行相应的数据处理
            if self.model_config["detectionNmae"] == "YOLO3":
                img_detection = cv2.resize(images[i], tuple(self.model_config["model_detection_core"][
                                                                "image_input_size"]))
                img_detection = cv2.cvtColor(img_detection, cv2.COLOR_BGR2RGB)
                # # 使用torch gpu 加速进行数据处理
                # img_detection = torch_Normalized(img_detection)
            elif self.model_config["detectionNmae"] == "ATSS":
                img_detection = cv2.resize(images[i], tuple(self.model_config["model_atss_detection"][
                                                                "image_input_size"]))
                img_detection = cv2.cvtColor(img_detection, cv2.COLOR_BGR2RGB)

                mean = [0.485, 0.456, 0.406]
                std = [0.229, 0.224, 0.225]
                transform = TT.Compose([TT.ToTensor(),
                                        TT.Normalize(mean, std)])

                img_detection = transform(img_detection).unsqueeze(0).numpy()

            self.cameraData[sn][2] = img_detection

            save_pic_name.append(saveName)

        # retObj["data"] = save_pic_name
        return save_pic_name

    def savePic(self, pic_dir):
        data = {}
        allImgs = []
        allImgPaths = []
        for k, v in self.cameraData.items():  # {sn: [imgdata, saveName]}
            img, picName = v[0], v[1]
            image_path = os.path.join(
                pic_dir,
                picName
            )
            # t1 = time.time()
            # out_file = open(image_path, 'wb')
            # out_file.write(jpeg.encode(img, quality=95))
            # out_file.close()
            # t2 = time.time()
            # logger.info_ai(meg="PyTurboJPEG time: %f" % (t2 - t1))

            # new_image_path = image_path[:-4] + '_cv.jpg'
            # cv2.imwrite(image_path, img)
            # logger.info_ai(meg="cv time: %f" % (time.time() - t2))
            # 数据汇总
            data[k] = image_path
            allImgs.append(img)
            allImgPaths.append(image_path)
        # 图片保存
        # start_time = time.time()
        inputs = [{"imgpath": allImgPaths[i], "img": allImgs[i]} for i in range(len(allImgPaths))]
        self.poolPicSave.map(cvImwrite, inputs)
        return data