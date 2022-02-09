# coding=utf-8
import os
'''2021-06-25--显示图中信息--配置文件'''


# 系统(影响路径的格式)
System_message = ["Windows", "Linux"]
System_choose_number = 0
# 图片路径
if System_choose_number == 0:
    code_path = os.path.split(os.path.abspath(__file__))[0]
    # Show_path = os.path.join(code_path, "img_2021_06_18")
    Show_path = r"C:\copy_read_pic\duqu_pic\d_have_1215"   # 读取图片路径
else:
    code_path = os.path.split(os.path.abspath(__file__))[0]
    Show_path = "/mnt/data/data/image/havebox/" + "ssc2.0_arm1_2021_0625"


# 执行选择项[0:统计符合时间段要求的图片数量,
#           1:读取.txt信息,
#           2:显示图片及异常点信息,
#           3：
#           4：]
Choose_code_model = [0, 1, 2, 3]

# 是否存图 及存图路径
Bool_copy = True
Copy_or_cut = 0  # 0:copy，1：move，2：delete
# Copy_self_path1 = r"C:\python_used\pic_used\copy_self_0623\img_2021_06_18\A_11_17_455.txt"
Copy_to_path1 = r"C:\copy_read_pic\write_pic\copy_path11"   # 保存图片路径
Copy_model = 1  # 1:带框图片(Windows不支持)，2:原图+.txt
# 筛选图片的时间段
Time_pic_choose = 1  # 0:创建时间，1：修改时间，2：访问时间
Show_start_date = "2021/06/18"
Show_end_date = "2022/07/26"
Show_start_time = "17:05:06"
Show_end_time = "19:05:06"

# 筛选图片中 异常点的种类
Num_label = [0, 1, 2, 3, 4, 5, 6, 7]
# Choose_label = ["yixian", "zangmian", "shenhuangmao", "zhonghuangmao"]
Choose_label = ["yixian", "zangmian", "mpg", "serong", "caogan", "yangshi", "shenhuangmao", "zhonghuangmao"]
# 筛选图片中 异常点的分数(大于该值，会被选择)
Bool_score = True  # True:读取参数， False:强制为0
Choose_score = {"yixian": 0.2,
                "zangmian": 0.1,
                "mpg": 0.1,
                "serong": 0.1,
                "caogan": 0.1,
                "yangshi": 0.1,
                "shenhuangmao": 0.1,
                "zhonghuangmao": 0.1,
                }
Bool_draw_cut = False  # 是否画边界框
Cut_list = {"up": 50,
            "down": 2000,
            "left": 100,
            "right": 2348,
            "w_left": 398,
            "W_right": 2390,
            }