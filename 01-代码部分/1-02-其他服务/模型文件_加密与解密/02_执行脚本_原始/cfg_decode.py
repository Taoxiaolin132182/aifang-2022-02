# coding=utf-8
''' 对加密模型解密的配置，路径等'''
choose_code = 1  # 1:解密  / 2:加密 /3: 转化执行文件

if_need_remove_old = False  # 加密时是否需要删除原始模型 True：要删除，False：保留

model_name = "cotton"  # 模型种类 wool / cotton
model_count = 1   # 加载模型数量

# path_job = "/mnt/data/data/aimodel/wool_double_model_20210812/"   # 羊毛双模型
path_job = "/mnt/data/data/aimodel/wxmf_sansimian_20211129/"  # 三丝棉 clean 模型
# path_job = "/mnt/data/data/aimodel/20211113_yangrong_model/"  # 羊绒 模型
# path_job = "/mnt/data/data/aimodel/"  # 老模型

# path_model = ""   # 老模型
path_model = "trt_model/model_atss_detection/1/"   # 三丝棉 || 羊绒 模型
# path_model = "trt_model/model_detection_core/1/"   # 羊毛双模型 -1
path_model_add = "trt_model/model_detection_add/1/"  # 羊毛双模型 -2

# model_last_name = ["cotton_yixian_4.des3", "cotton_yixian_4.pb"]  # 老模型
model_last_name = ["model.des3", "model.plan"]  # 三丝棉 模型 || 羊绒模型
# model_last_name = ["model_a.des3", "model.plan"]  # 羊毛双模型 -1
model_last_name_add = ["model_b.des3", "model.plan"]  # 羊毛双模型 -2

path_ori_file = "/mnt/data/data/2test_remove/d_decode/decode_model.py"  # 脚本的完整路径
path_com_file = "/mnt/data/data/2test_remove/try_decode"  # 设定执行文件的所在路径
tar_name = "/mnt/data/data/2test_remove/try_decode_1029.tar.gz"  # 设定通用打包文件名-需要完整路径