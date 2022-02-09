# coding=utf-8
''' 对加密模型解密的配置，路径等'''
choose_code = 3  # 1:解密  / 2:加密 /3: 转化执行文件

if_need_remove_old = True  # 加密时是否需要删除原始模型 True：要删除，Fasle：保留

model_name = "wool"  # 模型种类 wool / cotton
model_count = 2   # 加载模型数量

path_job = "/mnt/data/data/aimodel/wool_double_model_20210812/"

# path_model = "trt_model/model_detection_core/1/model.plan"
# path_model_add = "trt_model/model_detection_add/1/model.plan"
path_model = "trt_model/model_detection_core/1/"
path_model_add = "trt_model/model_detection_add/1/"

model_last_name = ["model_a.des3", "model.plan"]
model_last_name_add = ["model_b.des3", "model.plan"]

path_ori_file = "/mnt/data/data/2test_remove/d_decode/decode_model.py"  # 脚本的完整路径
path_com_file = "/mnt/data/data/2test_remove/try_decode"  # 设定执行文件的所在路径
tar_name = "/mnt/data/data/2test_remove/try_decode_0908.tar.gz"  # 设定通用打包文件名-需要完整路径