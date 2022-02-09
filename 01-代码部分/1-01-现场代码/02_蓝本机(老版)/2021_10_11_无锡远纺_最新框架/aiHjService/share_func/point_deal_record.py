import os
import sys
import time
import threading

START_PY_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(START_PY_PATH, "..", ".."))




class point_record:
    def __init__(self):
        super().__init__()
        #统计-计数 全局
        self.ai_all_point = 0  # 计数 AI 识别总数
        self.ai_all_label = 0  # 计数 AI中 所有符合分类的点
        self.ai_pix_main = 0  # 计数 AI 符合分类、不在边缘处 的点
        self.ai_first_filtrate = 0  # 计数 AI 初步筛选的点

        self.fiber_priority = 0  # 计数 初步筛选 AI-异纤 优先
        self.fiber_seemingly = 0  # 计数 初步筛选 AI-异纤 疑似
        self.other_label = 0  # 计数 初步筛选 AI-其他异常点

        self.real_all_piont_put = 0  # 实际存入队列 点 总数
        self.real_fiber_priority_put = 0  # 实际存入队列 异纤 优先
        self.real_fiber_seemingly_put = 0  # 实际存入队列 异纤 疑似
        self.real_other_label_put = 0  # 实际存入队列 其他异常点

        self.real_fiber_priority_throw = 0  # 异纤 优先 存入时因队列满删掉的点数
        self.real_fiber_seemingly_throw = 0  # 异纤 疑似 存入时因队列满删掉的点数
        self.real_other_label_throw = 0  # 其他异常点 存入时因队列满删掉的点数

        #=============================================
        self.use_1claw_OK = 0  # 抓手1 抓取OK
        self.use_1claw_OK_1 = 0  # 抓手1 抓取OK 异纤 优先
        self.use_1claw_OK_2 = 0  # 抓手1 抓取OK 其他异常点
        self.use_1claw_OK_3 = 0  # 抓手1 抓取OK 异纤 疑似

        self.use_2claw_OK = 0  # 抓手2 抓取OK
        self.use_2claw_OK_1 = 0  # 抓手2 抓取OK 异纤 优先
        self.use_2claw_OK_2 = 0  # 抓手2 抓取OK 其他异常点
        self.use_2claw_OK_3 = 0  # 抓手2 抓取OK 异纤 疑似

        self.use_2claw_OK_assit_all = 0  # 抓手2 抓取OK 从次队列拿到的点
        self.use_2claw_OK_assit_1 = 0  # 抓手2 抓取OK 从次队列拿到的点 异纤 优先
        self.use_2claw_OK_assit_2 = 0  # 抓手2 抓取OK 从次队列拿到的点 其他异常点
        self.use_2claw_OK_assit_3 = 0  # 抓手2 抓取OK 从次队列拿到的点 异纤 疑似

        self.use_3claw_OK = 0  # 抓手3 抓取OK
        self.use_3claw_OK_1 = 0  # 抓手3 抓取OK 异纤 优先
        self.use_3claw_OK_2 = 0  # 抓手3 抓取OK 其他异常点
        self.use_3claw_OK_3 = 0  # 抓手3 抓取OK 异纤 疑似

        self.use_3claw_OK_assit_all = 0  # 抓手3 抓取OK 从3队列拿到的点
        self.use_3claw_OK_assit_1 = 0  # 抓手3 抓取OK 从3队列拿到的点 异纤 优先
        self.use_3claw_OK_assit_2 = 0  # 抓手3 抓取OK 从3队列拿到的点 其他异常点
        self.use_3claw_OK_assit_3 = 0  # 抓手3 抓取OK 从3队列拿到的点 异纤 疑似


        self.use_4claw_OK = 0  # 抓手4 抓取OK
        self.use_4claw_OK_1 = 0  # 抓手4 抓取OK 异纤 优先
        self.use_4claw_OK_2 = 0  # 抓手4 抓取OK 其他异常点
        self.use_4claw_OK_3 = 0  # 抓手4 抓取OK 异纤 疑似

        self.use_4claw_OK_assit_all = 0  # 抓手4 抓取OK 从3队列拿到的点
        self.use_4claw_OK_assit_1 = 0  # 抓手4 抓取OK 从3队列拿到的点 异纤 优先
        self.use_4claw_OK_assit_2 = 0  # 抓手4 抓取OK 从3队列拿到的点 其他异常点
        self.use_4claw_OK_assit_3 = 0  # 抓手4 抓取OK 从3队列拿到的点 异纤 疑似
        # =============================================
        # self.use_1claw_first_NG = 0  # 抓手1 初步舍去 存入次队列-总
        # self.use_1claw_first_NG_1 = 0  # 抓手1 初步舍去 存入次队列-异纤 优先
        # self.use_1claw_first_NG_2 = 0  # 抓手1 初步舍去 存入次队列-其他异常点
        # self.use_1claw_first_NG_3 = 0  # 抓手1 初步舍去 存入次队列-异纤 疑似

        self.use_1claw_check_NG = 0  # 抓手1 舍去 存入次队列-总
        self.use_1claw_check_NG_1 = 0  # 抓手1 舍去 存入次队列-异纤 优先
        self.use_1claw_check_NG_2 = 0  # 抓手1 舍去 存入次队列-其他异常点
        self.use_1claw_check_NG_3 = 0  # 抓手1 舍去 存入次队列-异纤 疑似

        self.use_1claw_check_NG_1_throw = 0  # 抓手1 舍去 存入次队列-异纤 优先 因队列满删掉
        self.use_1claw_check_NG_2_throw = 0  # 抓手1 舍去 存入次队列-其他异常点 因队列满删掉
        self.use_1claw_check_NG_3_throw = 0  # 抓手1 舍去 存入次队列-异纤 疑似 因队列满删掉

        # =============================================
        # self.use_2claw_first_NG = 0  # 抓手2 初步舍去 -总
        # self.use_2claw_first_NG_1 = 0  # 抓手2 初步舍去 -异纤 优先
        # self.use_2claw_first_NG_2 = 0  # 抓手2 初步舍去 -其他异常点
        # self.use_2claw_first_NG_3 = 0  # 抓手2 初步舍去  -异纤 疑似
        #
        # self.use_2claw_first_NG_from_q2 = 0  # 抓手2 初步舍去 -总 -从次队列
        # self.use_2claw_first_NG_1_from_q2 = 0  # 抓手2 初步舍去 -异纤 优先 -从次队列
        # self.use_2claw_first_NG_2_from_q2 = 0  # 抓手2 初步舍去 -其他异常点 -从次队列
        # self.use_2claw_first_NG_3_from_q2 = 0  # 抓手2 初步舍去  -异纤 疑似 -从次队列

        self.use_2claw_check_NG = 0  # 抓手2 舍去 -总
        self.use_2claw_check_NG_1 = 0  # 抓手2 舍去 -异纤 优先
        self.use_2claw_check_NG_2 = 0  # 抓手2 舍去 -其他异常点
        self.use_2claw_check_NG_3 = 0  # 抓手2 舍去 -异纤 疑似

        self.use_2claw_check_NG_1_throw = 0  # 抓手2 舍去 存入3队列-异纤 优先 因队列满删掉
        self.use_2claw_check_NG_2_throw = 0  # 抓手2 舍去 存入3队列-其他异常点 因队列满删掉
        self.use_2claw_check_NG_3_throw = 0  # 抓手2 舍去 存入3队列-异纤 疑似 因队列满删掉

        # =============================================

        self.use_3claw_check_NG = 0    # 抓手3 舍去 -总
        self.use_3claw_check_NG_1 = 0  # 抓手3 舍去 -异纤 优先
        self.use_3claw_check_NG_2 = 0  # 抓手3 舍去 -其他异常点
        self.use_3claw_check_NG_3 = 0  # 抓手3 舍去 -异纤 疑似


        # =============================================

        self.use_4claw_check_NG = 0    # 抓手4 舍去 -总
        self.use_4claw_check_NG_1 = 0  # 抓手4 舍去 -异纤 优先
        self.use_4claw_check_NG_2 = 0  # 抓手4 舍去 -其他异常点
        self.use_4claw_check_NG_3 = 0  # 抓手4 舍去 -异纤 疑似



        # =============================================
        # =============================================
        # 传递信号量
        self.bool_send_PLC1 = False #当相机、光源、AI无故障时，为False,避免频繁写入[88]

        # 抓手回零计数
        self.grab1_gohome_count = 0
        self.grab2_gohome_count = 0
        self.grab3_gohome_count = 0
        self.grab4_gohome_count = 0


        self.supplier_bool = True #True 为 可以录入
        #棉花厂供应商
        self.supplier = [
            ['武城发洋',	'37050', 'WC-FY1'],
            ['武城银海', '37087', 'WC-YH1'],
            ['武城银恒', '37125', 'WC-YH2'],
            ['新疆利华第一棉花加工厂', '65070', 'XJ-LH-DYMH-JGC1'],
            ['沙湾利华第四加工厂', '65111', 'SW-LH-DS-JGC1'],
            ['铁门关利华尉犁塔里木加工厂', '65149', 'TMG-LH-WLTLM-JGC1'],
            ['呼图壁云龙', '65257', 'HTBYL1'],
            ['昌吉利华佃坝', '65267', 'CJ-LH-DB1'],
            ['昌吉下巴湖', '65324', 'CJ-XBH1'],
            ['玛纳斯沣泽', '65343', 'MNS-FZ1'],
            ['铁门关利华尉犁琼库勒分公司', '65348', 'TMG-LH-WLQKL-FGS1'],
            ['新疆利华第三棉花加工厂', '65379', 'XJ-LH-DSMH-JGC1'],
            ['新疆鸿力棉业有限公司海楼乡包孜墩轧花厂', '65397', 'XJ-HLMY-YXGS-HLXBZDZHC1'],
            ['新疆利华第四棉花加工厂', '65427', 'XJ-LH-DSMH-JGC2'],
            ['新疆利华第五棉花加工厂', '65504', 'XJ-LH-DWMH-JGC1'],
            ['沙湾利华第八加工厂', '65550', 'SW-LH-DB-JGC1'],
            ['昌吉利华老龙河', '65572', 'CJ-LH-LLH1'],
            ['沙湾利华第三棉花加工厂', '65590', 'SW-LH-DS-MHJGC1'],
            ['乌苏福兴棉业', '65794', 'WS-FX-MY1'],
            ['胡杨河利华乌苏高泉', '66003', 'HYH-LH-WSGQ1'],
            ['石河子银康棉业', '66017', 'SHZ-YK-MY1'],
            ['哈密银天棉业', '66023', 'HM-YT-MY1'],
            ['阿拉尔鹏越', '66025', 'ALE-PY1'],
            ['阿拉尔市鹏硕棉业', '66033', 'ALES-PY-MY1'],
            ['石河子银耀棉业', '66060', 'SHZ-YY-MY1'],
            ['石河子利华下野地一分厂', '66064', 'SHZ-LH-XYD-YFC1'],
            ['石河子银安棉业', '66065', 'SHZ-YA-MY1'],
            ['新疆屯南圣洁棉麻', '66073', 'XJ-TNSJ-MM1'],
            ['新疆水控国棉科技铁门关乌鲁克轧花一厂', '66077', 'XJ-SKGMKJ-TMG-WLKZHYC1'],
            ['新疆胡杨河利华乌苏科克兰木', '66091', 'XJ-HYH-LH-WSKKLM1'],
            ['新疆锦硕源', '66142', 'XJ-JSY1'],
            ['石河子都邦天云', '66196', 'SHZ-DBTY1'],
            ['农一师棉麻鹏飞棉业', '66208', 'NYS-MM-PFMY1'],
            ['铁门关利华', '66209', 'TMG-LH1'],
            ['石河子宝达棉业', '66217', 'SHZ-BD-MY1'],
            ['石河子利华下野地二分公司', '66220', 'SHZ-LH-XYD-EFC1'],
            ['阿拉尔利华绿园镇分公司', '66234', 'ALE-LH-LYZ-FGS1'],
            ['五家渠永盛棉业', '66253', 'WJQ-YS-MY1'],
            ['六师五家渠国懋棉麻', '66256', 'LS-WJQ-GM-MM1'],
            ['五家渠市龙佰力', '66264', 'WJQS-LBL1'],
            ['石河子银鹏棉业', '66066', 'SHZ-YP-MY1']
        ]



    # end def

