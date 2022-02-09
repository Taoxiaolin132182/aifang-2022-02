# coding=utf-8
import time
import copy
import cv2
import os
import sys
import ast
import shutil

# 添加包路径
START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(START_PY_PATH)
import read_config as read_cfg


def draw_pic(self, pic_path, data_ai1):
    point_data_ori = data_ai1  # 点数据，原始
    point_box = point_data_ori["boxes"]  # [[a,b,c,d],[e,f,g,h]]
    if len(point_box) > 0:
        # print("开始画图:{}".format(pic_path))
        image_ori = pic_path  # 图片路径
        path_ = image_ori.split("/")[-1]
        img = cv2.imread(image_ori)  # 读出图片
        point_score = point_data_ori[
            "scores"]  # [0.7993741035461426, 0.6471705436706543, 0.4785524904727936, 0.4358397126197815]
        point_label = point_data_ori[
            "labels"]  # ['kongqiangmao', 'kongqiangmao', 'shenhuangmao', 'kongqiangmao']
        for j in range(len(point_box)):
            label_, score_, x_min, y_min, x_max, y_max = point_label[j], point_score[j], \
                                                         point_box[j][0], point_box[j][1], \
                                                         point_box[j][2], point_box[j][3]
            self.plot_one_box(img, [x_min, y_min, x_max, y_max], label=str(label_) + "|" + str(score_))
        cv2.imwrite(os.path.join(self.havebox_path, path_), img)
        print("havebox:{}".format(os.path.join(self.havebox_path, path_)))


def plot_one_box(img, coord, label=None, color=None, line_thickness=None):
    '''
    coord: [x_min, y_min, x_max, y_max] format coordinates.
    img: img to plot on.
    label: str. The label name.
    color: int. color index.
    line_thickness: int. rectangle line thickness.
    '''
    tl = line_thickness or int(round(0.002 * max(img.shape[0:2])))  # line thickness
    # color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(coord[0]), int(coord[1])), (int(coord[2]), int(coord[3]))
    cv2.rectangle(img, c1, c2, color, thickness=3)  # thickness=tl 画框
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=float(tl) / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        # cv2.rectangle(img, c1, c2, color, -1)  # filled
        # cv2.rectangle(img, c1, c2, color ,thickness=0)  # filled#label的框
        # cv2.putText(img, label, (c1[0], c1[1] - 2), 0, float(tl) / 3, color, thickness=tf, lineType=cv2.LINE_AA)
        cv2.putText(img, label, (c1[0], c1[1] - 2), cv2.FONT_HERSHEY_COMPLEX, float(tl) / 3, color, thickness=3,
                    lineType=cv2.LINE_AA)

def read_config():
    # [0]:num_label,
    # [1]:num_label--第一次出现的标记
    # [2]:单张图片中，存在符合条件的点：1，否则：0
    # [3]:单张图中符合条件的点的总数
    num_all = [0, 0, 0, 0]
    now_label_list, now_score_list = read_choose_label()
    pic_path1 = read_cfg.Show_path  # 用来搜索的文件夹路径
    print("将读取的文件夹路径：{}".format(pic_path1))
    if not os.path.exists(pic_path1):
        print("该文件夹不存在，请重新配置及确认")
        os.makedirs(pic_path1)
        print("创建对应路径(文件夹)")
        time.sleep(5)
        sys.exit(0)
    else:
        now_copy_path1 = create_copy_path(pic_path1)
        list_txt_copy1 = []
        # get_config_time()
        # change_to_strtime(time.time())
        '''获取限制时间'''
        t_start, t_end = get_config_time()

        list_file = os.listdir(pic_path1)
        for name_file in list_file:
            # print("name_file:{}".format(name_file))
            if "txt" in name_file:
                name_file_path1 = os.path.join(pic_path1, name_file)

                t_file_now = get_c_time_of_file(name_file_path1)
                if t_file_now is not None:
                    if t_file_now >= t_start and t_file_now <= t_end:
                        list_txt_copy1.append(name_file)
        if 0 in read_cfg.Choose_code_model:
            print("图片数量:[{}], 在<{} {}---{} {}>".format(len(list_txt_copy1), read_cfg.Show_start_date,
                                       read_cfg.Show_start_time, read_cfg.Show_end_date, read_cfg.Show_end_date))
            # print("符合时间限制的文件：数量有：{}， 分别是：{}".format(len(list_txt_copy1), list_txt_copy1))
        t0 = time.time()
        if 1 in read_cfg.Choose_code_model:
            for name_file1 in list_txt_copy1:  # 分每张图
                num_all[3] = 0
                t1 = time.time()
                image1 = None


                txt_path = os.path.join(pic_path1, name_file1)  # .txt路径
                if 2 in read_cfg.Choose_code_model:
                    if read_cfg.System_message[read_cfg.System_choose_number] == "Windows":

                        pic_real_path = txt_path.replace("txt", "jpg")
                        pic_real_path1 = f"{pic_real_path}"
                        if os.path.exists(pic_real_path1):
                            print("路径存在")
                        else:
                            print("路径不存在")
                            continue
                        image1 = cv2.imread(pic_real_path1)  # 读取图片
                        # str1 = 'Camera{}'.format(name_file1.replace(".txt", ""))
                        # cv2.namedWindow(str1, cv2.WINDOW_NORMAL)
                        # cv2.resizeWindow(str1, 717, 600)
                        # cv2.moveWindow(str1, 20, 20)
                        # cv2.imshow("test1", image1)
                        # cv2.waitKey(0)
                        # cv2.destroyAllWindows()
                        # time.sleep(1)
                        # print("图片地址：{}".format(pic_real_path1))
                        # data = np.fromfile(txt_path.replace("txt", "jpg"), dtype=np.uint8)  # 先用numpy把图片文件存入内存：data，把图片数据看做是纯字节数据
                        # image1 = cv2.imdecode(data, cv2.IMREAD_COLOR)  # 从内存数据读入图片
                    else:

                        pic_real_path1 = txt_path.replace("txt", "jpg")
                        if os.path.exists(pic_real_path1):
                            print("路径存在")
                        else:
                            print("路径不存在")
                            continue
                        # pic_real_path1 = "./img_2021_06_18_a/" + name_file1.replace("txt", "jpg")  # 这行要改
                        # print("图片地址：{}".format(pic_real_path1))
                        image1 = cv2.imread(pic_real_path1)  # 读取图片
                    # print("读取图片耗时：{}".format(time.time() - t1))
                with open(txt_path, "r") as f:
                    try:
                        message_txt1 = f.read().replace("[", "").replace("]", "")  #[{},{}]
                        # print("message_txt1:{}".format(message_txt1))
                        list_point_str1 = message_txt1.split("}}, ")  # 排除{前的空格
                        # print("point_str1:{}".format(list_point_str1))
                        num_all[1] = 0
                        for point_str2 in list_point_str1:  # 分成每个点
                            num_all[2] = 0
                            if "}}" not in point_str2:
                                point_str2 += "}} "
                            dict_message1 = ast.literal_eval(point_str2)
                            # print("字典类型：{}---：{}".format(type(dict_message1), dict_message1))
                            # 判断label
                            bool_is_label = dict_message1["labelType"] in now_label_list  # lable 符合条件
                            bool_is_score = dict_message1["labelMap"]["score"] > now_score_list[dict_message1["labelType"]]
                            if bool_is_label and bool_is_score:
                                if num_all[1] == 0:
                                    num_all[0] += 1
                                    num_all[1] += 1
                                num_all[2] = 1
                                # print("此点符合条件：{}".format(dict_message1))
                                num_all[3] += 1
                            if num_all[2] == 1:
                                draw_and_show_message(dict_message1, image1)  # 画框-写信息
                        if num_all[1] > 0:  # 当1张图中 存在 有效点时
                            # image2 = copy.deepcopy(image1)
                            # show_pic(name_file1, image1)  # 显示图像
                            name_file2 = name_file1 + "__point_" + str(num_all[3])
                            # show_pic(name_file2, image1)  # 显示图像
                            #复制图像及.txt文件
                            if read_cfg.Copy_model == 2:

                                copy_file(txt_path, now_copy_path1)   # txt_path绝对全路径，now_copy_path1目标路径
                                pic_path_copy = txt_path.replace("txt", "jpg")
                                copy_file(pic_path_copy, now_copy_path1)
                            if read_cfg.Copy_model == 1:
                                save_pic_namepath = os.path.join(now_copy_path1, name_file1.replace("txt", "jpg"))
                                print("save_pic_namepath:{}".format(save_pic_namepath))
                                cv2.imwrite(save_pic_namepath, image1)
                    except Exception as e:
                        print(f"read_txt_message err: {e}")
                        print("error -- {}".format(txt_path))

            print("符合条件[时间,类别,阈值]--共有{}张图".format(num_all[0]))
            print("总计用时：{}".format(round(time.time() - t0, 3)))
def test_1():
    fun1 = read_cfg.Copy_self_path1
    fun2 = read_cfg.Copy_to_path1
    print("fun1",fun1)
    print("fun2", fun2)
    code1 = "copy " + fun1 + " " + fun2
    os.system(code1)

def test_2():
    path1 = read_cfg.Show_path
    file1_path = os.path.join(path1, "A_09_12_87.jpg")
    print("复制源：{}".format(file1_path))
    copy_path1 = os.path.join(path1, "..", "copy_path11")
    print("复制目标：{}".format(copy_path1))
    shutil.copy(file1_path, copy_path1)



def create_file_name():
    pass


#  copy C:\001chengxu\A_11_17_455.txt C:\001chengxu\01\
# {'leftTopX': 1416.4453125, 'leftTopY': 966.25, 'rightBottomX': 1477.8046875,
# 'rightBottomY': 1128.416748046875, 'labelType': 'yixian', 'labelMap': {'level': 'havebox', 'score': 0.51433}}

'''复制图片+.txt文件'''
def copy_file(path_copy_will, path_need):
    if read_cfg.Bool_copy:
        # if read_cfg.System_message[read_cfg.System_choose_number] == "Windows":
        if path_need is not None:
            # path_need = "\复制1\copy_path11"
            # print("图像源:{}---目标:{}".format(path_copy_will, path_need))
            if read_cfg.Copy_or_cut == 0:
                shutil.copy(path_copy_will, path_need)
            elif read_cfg.Copy_or_cut == 1:
                shutil.move(path_copy_will, path_need)
            elif read_cfg.Copy_or_cut == 2:
                os.remove(path_copy_will)
            else:
                pass

'''创建需要复制的路径'''
def create_copy_path(main_path):
    if read_cfg.Bool_copy:
        if read_cfg.System_message[read_cfg.System_choose_number] == "Windows":
            # path1 = os.path.join(main_path, "..", read_cfg.Copy_to_path1)  # ".."可行
            path1 = read_cfg.Copy_to_path1  # ".."可行
            print("字符串-创建文件夹：{}".format(path1))
            if os.path.exists(path1):
                print("该路径已存在，跳过创建")
            else:

                code1 = "mkdir " + path1  # 多层创建
                # os.makedirs(path1)  # 也能创建目录--多层创建
                os.system(code1)  # 指令创建目录
                print("创建拷贝路径成功：{}".format(code1))
            return path1
        else:
            date_path1 = time.strftime("%Y_%m%d", time.localtime())
            path1 = "/mnt/data/data/need_copy_PIC/" + read_cfg.Copy_to_path1 + "_" + date_path1
            # code1 = "mkdir -p /mnt/data/data/need_copy_PIC/" + read_cfg.Copy_to_path1 + "_" + date_path1
            code1 = "mkdir -p " + path1
            os.system(code1)
            code2 = "chmod -R 777 /mnt/data/data/need_copy_PIC/"
            os.system(code2)
            return path1
    else:
        return None




'''读取要选取的种类'''
def read_choose_label():
    list_label_return1 = []
    # list_score_return1 = []
    list_label1 = read_cfg.Choose_label
    list_score1 = read_cfg.Choose_score
    num_label1 = read_cfg.Num_label
    for num1 in num_label1:
        list_label_return1.append(list_label1[num1])
    if not read_cfg.Bool_score:
        for key1, value1 in list_score1.items():
            list_score1[key1] = 0

    print("读取要选取的种类:{}".format(list_label_return1))
    print("读取要选取的种类对应的分数:{}".format(list_score1))
    return list_label_return1, list_score1
'''画框及显示信息'''
def draw_and_show_message(dict_message2, img2):
    if 2 in read_cfg.Choose_code_model:
        c1 = (int(dict_message2['leftTopX']), int(dict_message2['leftTopY']))
        c2 = (int(dict_message2['rightBottomX']), int(dict_message2['rightBottomY']))
        color = (0, 0, 0)
        cv2.rectangle(img2, c1, c2, color, 3)  # thickness=tl 画框
        label = dict_message2['labelType'] + "|" + str(round(dict_message2['labelMap']['score'], 4))
        cv2.putText(img2, label, (c2[0], c2[1] - 15), cv2.FONT_HERSHEY_COMPLEX, 2, color, 2, cv2.LINE_AA)
        if "ff_color" in dict_message2['labelMap'].keys():
            if "ff_type" in dict_message2['labelMap'].keys():
                label2 = dict_message2['labelMap']['ff_color'] + "|" + dict_message2['labelMap']['ff_type']
            else:
                label2 = dict_message2['labelMap']['ff_color']
            cv2.putText(img2, label2, (c2[0], c2[1] + 45), cv2.FONT_HERSHEY_COMPLEX, 2, color, 2, cv2.LINE_AA)
        if read_cfg.Bool_draw_cut:
            dict_c_pic = read_cfg.Cut_list
            c3 = (int(dict_c_pic["w_left"]), int(dict_c_pic["up"]))
            c4 = (int(dict_c_pic["W_right"]), int(dict_c_pic["down"]))
            color3 = (0, 0, 255)
            cv2.rectangle(img2, c3, c4, color3, 2)  # thickness=tl 画框
            c5 = (int(dict_c_pic["left"]), int(dict_c_pic["up"]))
            c6 = (int(dict_c_pic["right"]), int(dict_c_pic["down"]))
            color5 = (0, 255, 0)
            cv2.rectangle(img2, c5, c6, color5, 4)  # thickness=tl 画框
'''显示图像'''
def show_pic(name3, img3):
    if 2 in read_cfg.Choose_code_model:
        str1 = 'Camera{}'.format(name3.replace(".txt", ""))
        cv2.namedWindow(str1, cv2.WINDOW_NORMAL)

        cv2.resizeWindow(str1, 717, 600)
        cv2.moveWindow(str1, 20, 20)
        cv2.imshow(str1, img3)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

'''获取文件夹的时间'''
def get_c_time_of_file(path1):
    if not os.path.exists(path1):
        # print("该文件不存在，请重新配置及确认")
        return None
    else:
        # print("文件大小：{}".format(os.path.getsize(path1)))
        # print("文件大小-类型：{}".format(type(os.path.getsize(path1))))
        if os.path.getsize(path1) < 10:
            return None
        else:
            time_choose1 = read_cfg.Time_pic_choose
            if time_choose1 == 1:
                c_path1_time = os.path.getmtime(path1)  # 文件修改时间
            elif time_choose1 == 2:
                c_path1_time = os.path.getatime(path1)  # 文件访问时间
            else:
                c_path1_time = os.path.getctime(path1)  # 文件创建时间
            format_time_dir = time.ctime(c_path1_time)
            # print("该文件夹-创建时间：{}".format(format_time_dir))
            return c_path1_time

'''获取配置中的限制时间'''
def get_config_time():
    file_start_time = read_cfg.Show_start_date + "." + read_cfg.Show_start_time
    # print("限制开始时间：{}".format(file_start_time))
    satrt_time1 = change_to_timestamp(file_start_time)

    file_end_time = read_cfg.Show_end_date + "." + read_cfg.Show_end_time
    # print("限制结束时间：{}".format(file_end_time))
    end_time1 = change_to_timestamp(file_end_time)

    # print("现在的时间戳：{}".format(time.time()))
    return satrt_time1, end_time1

'''时间格式转换时间戳'''
def change_to_timestamp(str_time):
    timearray2 = time.strptime(str_time, "%Y/%m/%d.%H:%M:%S")  # 输入 和 转换 需要匹配的格式
    time_stamp2 = time.mktime(timearray2)
    # print("时间戳：{}".format(time_stamp2))
    return time_stamp2

'''时间戳转换指定时间格式'''
def change_to_strtime(timestamp1):
    time_array1 = time.localtime(timestamp1)  # 格式化时间戳为本地的时间
    strtime1 = time.strftime("%Y-%m-%d %H:%M:%S", time_array1)
    print("现在的格式时间:{}".format(strtime1))
    return strtime1




'''主函数'''
def function_main1():
    read_config()
    # test_2()
    pass



if __name__ == '__main__':
    function_main1()