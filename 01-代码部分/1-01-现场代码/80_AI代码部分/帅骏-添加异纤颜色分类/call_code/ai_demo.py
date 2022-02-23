from aimodel.config import *
from aimodel.cameraModel import *
from aimodel.aiModel import *
from aimodel.tritonserver import *
import sys


def main():
    # 加载配置文件
    config_path = ''
    model_config = load_config(config_path)

    # tritonserver init
    tritonserverModel = tritonserver(model_config)
    # 杀掉可能已经启动的tritonserver模块
    tritonserverModel.kill_tritonserver()
    # 启动算法服务模块
    connect_flag = tritonserverModel.start_tritonserver()
    if connect_flag:
        print("Triton_server is ready")
    else:
        print("aimodelInit error Triton_server is not ready")
        sys.exit(0)

    # 检测模型初始化
    if model_config["detectionNmae"] == "YOLO3":
        detectionModel = model_detection_core(model_config)
    elif model_config["detectionNmae"] == "ATSS":
        detectionModel = model_atss_detection(model_config)
    else:
        print("please choose a model name")
        sys.exit(0)



    # camera init
    cameraModel = camera_model(model_config)
    cameraModel.cameraInit()
    # take pic  savePicName  ==> []
    savePicName = cameraModel.takePic()
    # save pic
    pic_dir = ''
    picData = cameraModel.savePic(pic_dir)

    # aiInfer cameraData  ==>  {sn: [imgdata, saveName, img_data_process]}
    sn = ''
    # 处理后的图片
    img = cameraModel.cameraData[sn][2]
    # oriImg 原始图片数据
    oriImg = cameraModel.cameraData[sn][0]
    # 当前预测的图片
    img_name = cameraModel.cameraData[sn][1]
    # ai的返回结果
    returnAiData = detectionModel.aiInfer(oriImg, img, img_name)


def test_pic():
    # 加载配置文件
    config_path = ''
    model_config = load_config(config_path)

    # tritonserver init
    tritonserverModel = tritonserver(model_config)
    # 杀掉可能已经启动的tritonserver模块
    tritonserverModel.kill_tritonserver()
    # 启动算法服务模块
    connect_flag = tritonserverModel.start_tritonserver()
    if connect_flag:
        print("Triton_server is ready")
    else:
        print("aimodelInit error Triton_server is not ready")
        sys.exit(0)

    # 检测模型初始化
    if model_config["detectionNmae"] == "YOLO3":
        detectionModel = model_detection_core(model_config)
    elif model_config["detectionNmae"] == "ATSS":
        detectionModel = model_atss_detection(model_config)
    else:
        print("please choose a model name")
        sys.exit(0)

    img_path = ''
    ori_img = cv2.imread(img_path)
    img_detection = cv2.resize(ori_img, (1280, 1280))
    img_detection = cv2.cvtColor(img_detection, cv2.COLOR_BGR2RGB)


    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    transform = TT.Compose([TT.ToTensor(),
                            TT.Normalize(mean, std)])

    img_detection = transform(img_detection).unsqueeze(0).numpy()

    # ai的返回结果
    img_name = img_path.split('/')[-1]
    returnAiData = detectionModel.aiInfer(ori_img, img_detection, img_name)
    print(returnAiData)


def test_mutiprocess():
    # 加载配置文件
    config_path = ''
    model_config = load_config(config_path)

    # tritonserver init
    tritonserverModel = tritonserver(model_config)
    # 杀掉可能已经启动的tritonserver模块
    tritonserverModel.kill_tritonserver()
    # 启动算法服务模块
    connect_flag = tritonserverModel.start_tritonserver()
    if connect_flag:
        print("Triton_server is ready")
    else:
        print("aimodelInit error Triton_server is not ready")
        sys.exit(0)

    # 检测模型初始化
    if model_config["detectionNmae"] == "YOLO3":
        detectionModel = model_detection_core(model_config)
    elif model_config["detectionNmae"] == "ATSS":
        detectionModel = model_atss_detection(model_config)
    else:
        print("please choose a model name")
        sys.exit(0)

    # camera init
    cameraModel = camera_model(model_config)
    cameraModel.cameraInit()


def test_wool_double():
    # 加载配置文件
    config_path = ''
    model_config = load_config(config_path)

    # tritonserver init
    tritonserverModel = tritonserver(model_config)
    # 杀掉可能已经启动的tritonserver模块
    tritonserverModel.kill_tritonserver()
    # 启动算法服务模块
    connect_flag = tritonserverModel.start_tritonserver()
    if connect_flag:
        print("Triton_server is ready")
    else:
        print("aimodelInit error Triton_server is not ready")
        sys.exit(0)

    # 检测模型初始化
    detectionModel = model_detection_wool_double(model_config)

    # camera init
    cameraModel = camera_model(model_config)
    cameraModel.cameraInit()
    # take pic  savePicName  ==> []
    savePicName = cameraModel.takePic()
    # save pic
    pic_dir = ''
    picData = cameraModel.savePic(pic_dir)

    # aiInfer cameraData  ==>  {sn: [imgdata, saveName, img_data_process]}
    sn = ''
    # 处理后的图片
    img = cameraModel.cameraData[sn][2]
    # oriImg 原始图片数据
    oriImg = cameraModel.cameraData[sn][0]
    # 当前预测的图片
    img_name = cameraModel.cameraData[sn][1]
    # ai的返回结果
    returnAiData = detectionModel.aiInfer(oriImg, img, img_name)


def test_wool_single():
    # 加载配置文件
    config_path = ''
    model_config = load_config(config_path)

    # tritonserver init
    tritonserverModel = tritonserver(model_config)
    # 杀掉可能已经启动的tritonserver模块
    tritonserverModel.kill_tritonserver()
    # 启动算法服务模块
    connect_flag = tritonserverModel.start_tritonserver()
    if connect_flag:
        print("Triton_server is ready")
    else:
        print("aimodelInit error Triton_server is not ready")
        sys.exit(0)

    # 检测模型初始化
    detectionModel = model_detection_wool_single(model_config)

    # camera init
    cameraModel = camera_model(model_config)
    cameraModel.cameraInit()
    # take pic  savePicName  ==> []
    savePicName = cameraModel.takePic()
    # save pic
    pic_dir = ''
    picData = cameraModel.savePic(pic_dir)

    # aiInfer cameraData  ==>  {sn: [imgdata, saveName, img_data_process]}
    sn = ''
    # 处理后的图片
    img = cameraModel.cameraData[sn][2]
    # oriImg 原始图片数据
    oriImg = cameraModel.cameraData[sn][0]
    # 当前预测的图片
    img_name = cameraModel.cameraData[sn][1]
    # ai的返回结果
    returnAiData = detectionModel.aiInfer(oriImg, img, img_name)


def test_fluorescence():
    # 加载配置文件
    config_path = ''
    model_config = load_config(config_path)
    # 荧光模型初始化
    fl_model = fluorescence_model
    # camera init
    cameraModel = camera_model(model_config)
    cameraModel.cameraInit()
    # take pic  savePicName  ==> []
    savePicName = cameraModel.takePic()
    # save pic
    pic_dir = ''
    picData = cameraModel.savePic(pic_dir)

    # aiInfer cameraData  ==>  {sn: [imgdata, saveName, img_data_process]}
    sn = ''
    # 处理后的图片
    img = cameraModel.cameraData[sn][2]
    # oriImg 原始图片数据
    oriImg = cameraModel.cameraData[sn][0]
    # 当前预测的图片
    img_name = cameraModel.cameraData[sn][1]
    # ai的返回结果
    returnAiData = fl_model.detect(oriImg, img_name)



if __name__ == '__main__':
    # main()
    test_wool_double()