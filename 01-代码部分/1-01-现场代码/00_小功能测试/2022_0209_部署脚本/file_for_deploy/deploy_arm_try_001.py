import time, os, copy

'''
部署+ 提示 流程：
    1、cd /mnt/data/ 要把tar文件，和部署脚本 放进该路径下
    @2、检查和创建所需的文件夹，并赋予权限
        
    @3、mac地址 /opt/config/mac   + up 
    @4、mysql -p 
    @5、/etc/rc.local
    @6、sudo crontab -e
    @7、web 打包
    @8、nmtui 设定IP
    9、整个项目文件
    @10、软连接提示 (应该有的软连接，不对的软接连删掉后再连)
    @11、蓝牙中断配置
    @12、快捷指令的设定
    @13、aimodel 放入模型 放入解压config
    @14、U盘拷贝的指令 (要能联网才行)
    15、
    
    
'''
u_m_str1 = "  欢迎使用部署脚本。\n  现在准备部署..."
u_m_str2 = "  确认-需要检查和创建所需的文件夹，并赋予权限"
u_m_str3 = "  不需要  检查和创建所需的文件夹，并赋予权限"
u_m_str4 = "  确认-需要解压 解密模型脚本"
u_m_str5 = "  不需要  解压解密模型脚本"
u_m_str6 = ""
u_m_str7 = ""
use_message_list = [u_m_str1, u_m_str2, u_m_str3, u_m_str4, u_m_str5, u_m_str6, ]

def print_message_001(num1):
    global use_message_list
    print(use_message_list[num1])
    print("\n")
    time.sleep(0.1)

def input_use(word):
    mes_input_back1 = input("第{}步骤 完成 或跳过(y/n):".format(word))
    if mes_input_back1 == "y":
        time.sleep(0.2)
    else:
        time.sleep(1)
'''步骤001---检查和创建所需的文件夹'''
def check_and_create_path():
    print("\n------------------步骤001---检查和创建所需的文件夹-----------")
    mes_inputq1 = input("检查和创建所需的文件夹，并赋予权限 吗？(y/n):")
    if mes_inputq1 == "y":
        print_message_001(1)
        list_path_origin = ["/mnt/data/data/", "/mnt/data/opt/",  "/mnt/data/file_for_deploy/"]
        list_path_part = [[
                "image/", "image/havebox/", "image/nobox/", "image_original/", "upload_image/",
                "aimodel/", "log_txl/", "2test_remove/"], [
                "logs/", "logs/ai-product-haijiang/", "logs/ai-product-haijiang/ai-cotton-api-server-release/",
                "logs/txl01/", "logs/ai-auto-upload-data/", "logs/ai-auto-upload-data/ai-common-upload-file/",
                "logs/ai-auto-upload-data/ai-common-upload-db/"], []]
        count_p = 0
        for path_m in list_path_origin:
            if not os.path.exists(path_m):
                os.makedirs(path_m)
                time.sleep(0.2)
            for path_p in list_path_part[count_p]:
                path_all = path_m + path_p
                print(path_all)
                if not os.path.exists(path_all):
                    os.makedirs(path_all)
                    time.sleep(0.2)
            str_cmd = "chmod -R 777 " + path_m + " &"
            os.system(str_cmd)
            time.sleep(0.2)
            count_p += 1
        print("检查和创建所需的文件夹，并赋予权限  (完成)\n")
    else:
        print_message_001(2)

'''步骤002---aimodel 放入模型'''
def copy_aimodel():
    time.sleep(0.5)
    print("\n------------------步骤002---放入预置的AI 模型(1款羊毛，1款棉花)--------------------------\n")
    mes_input_back1 = input("需要放入预置的AI 模型 吗？(y/n):")
    if mes_input_back1 == "y":
        list_model = ["20211113_yangrong_model/", "wxmf_sansimian_20220203/", "cfg_decode.py"]
        for path_m in list_model:
            time.sleep(0.2)
            path_all = "/mnt/data/data/aimodel/" + path_m
            if os.path.exists(path_all):
                continue

            if ".py" in path_m:
                str_cmd2 = "cp -f /mnt/data/file_for_deploy/" + path_m + " /mnt/data/data/aimodel/"
            else:
                str_cmd2 = "cp -r /mnt/data/file_for_deploy/" + path_m + " /mnt/data/data/aimodel/"
            os.system(str_cmd2)
        print("放置 完成\n")
    else:
        print("暂不进行 aimodel的放入\n")

'''步骤003---解压 解密执行文件'''
def move_and_tar():
    print("\n------------------步骤003---解压 解密执行文件-----------")
    mes_inputq2 = input("需要解压 解密模型脚本 吗？(y/n):")
    if mes_inputq2 == "y":
        print_message_001(3)
        name_tar = "/mnt/data/file_for_deploy/try_decode_1029.tar.gz"
        if os.path.exists(name_tar):
            code41 = "tar -zxPf " + name_tar
            os.system(code41)
            print("解密执行文件---解压完成\n")
        else:
            print("{}--该文件或路径 不存在\n".format(name_tar))
    else:
        print_message_001(4)

'''步骤004---解压 web文件'''
def tar_web():
    time.sleep(0.5)
    print("\n------------------步骤004---解压 web文件--------------------------\n")
    mes_input_back1 = input("需要 解压web文件到对应路径下 吗？(y/n):")
    if mes_input_back1 == "y":
        time.sleep(0.2)
        ori_file = "modify_config_4.4_version.tar.gz"
        ori_path = "/mnt/data/file_for_deploy/modify_config/"
        target_path = "/mnt/data/data/2test_remove/"
        str_cmd2 = "tar -zxf " + ori_file
        os.system(str_cmd2)
        time.sleep(1)
        '''判断是否已经存在'''
        path_all = target_path + "modify_config/"
        if os.path.exists(path_all):
            mes_input_back1 = input("---@@@检查到对应路径下 已有web项目文件 确定覆盖 吗？(y/n):")
            if mes_input_back1 == "y":
                str_cmd_d = "rm -rf " + path_all
                os.system(str_cmd_d)
                str_cmd1 = "mv -f " + ori_path + " " + target_path
                os.system(str_cmd1)
                time.sleep(2)
                print("解压 放置 完成\n")
            else:
                print("放弃 覆盖web项目文件\n")
        else:
            str_cmd1 = "mv -f " + ori_path + " " + target_path
            os.system(str_cmd1)
            time.sleep(2)
            print("解压 放置 完成\n")
    else:
        print("暂不进行 解压web文件\n")

'''步骤005---解压 放入项目工程'''
def copy_project_file():
    time.sleep(0.5)
    print("\n------------------步骤005---解压 放入项目工程--------------------------\n")
    mes_input_back1 = input("需要解压 并放入项目工程 吗？(y/n):")
    if mes_input_back1 == "y":
        path_m = "/opt/app/ai-product-haijiang/"
        path_cf = "lanbenji-for-deploy-aifang-2022-0211.tar.gz"
        if os.path.exists(path_m):  # 先删除原来的
            str_cmd1 = "rm -rf " + path_m
            os.system(str_cmd1)

        str_cmd3 = "tar -zxf " + path_cf
        os.system(str_cmd3)
        time.sleep(3)
        str_cmd2 = "mv -f /mnt/data/file_for_deploy/ai-product-haijiang/ /opt/app/"
        os.system(str_cmd2)
        time.sleep(2)
        str_cmd4 = "chmod -R 777 " + path_m + " &"
        os.system(str_cmd4)

        print("解压 放入项目工程 完成\n")
    else:
        print("暂不进行 解压放入项目工程\n")

'''步骤006---快捷指令的设定'''
def quick_instructions():
    str_IP_1 = "\n------------------步骤006---(快捷指令的设定)---------------------------------\n" \
               "  先查看文件是否符合 cat ~/.bash_aliases\n" \
               "     看看是不是最新的快捷指令\n" \
               "---------------------------------------------------------------------"
    print(str_IP_1)
    time.sleep(2)
    mes_input_back1 = input("需要进行快捷指令的设定 吗？(y/n):")
    if mes_input_back1 == "y":
        time.sleep(0.2)
        str_cmd2 = "cp /mnt/data/file_for_deploy/.bash_aliases ~/"
        os.system(str_cmd2)
        print("配置完成，请进行如下操作 cd ~  然后 source .bashrc\n")
        time.sleep(1.5)
    else:
        print("跳过 快捷指令的设定\n")

'''步骤007---蓝牙中断配置'''
def bluetooth_setting():
    str_IP_1 = "\n------------------步骤007---(蓝牙中断配置)---------------------------------\n" \
               "  先查看文件是否符合 cat /etc/modprobe.d/blacklist.conf\n" \
               "     按到最下面，看时候有  install bluedroid_pm /bin/false\n" \
               "---------------------------------------------------------------------"
    print(str_IP_1)
    time.sleep(2)
    mes_input_back1 = input("需要进行蓝牙中断配置 吗？(y/n):")
    if mes_input_back1 == "y":
        file_p1 = ["/etc/modprobe.d/blacklist.conf", "/mnt/data/file_for_deploy/blacklist.conf"]
        str_cmd1 = "chmod 777 " + file_p1[0] + " &"
        os.system(str_cmd1)
        time.sleep(0.2)
        str_cmd2 = "cp " + file_p1[1] + " /etc/modprobe.d/"
        os.system(str_cmd2)
        print("配置完成，重启后生效！！！\n")
    else:
        print("跳过 蓝牙中断配置\n")

'''步骤008---软连接 提示'''
def tips_soft_links():
    str_IP_1 = "\n------------------步骤008---(软连接 提示)---------------------------------\n" \
               "  先 cd /opt/  再  ll\n" \
               "     看一下，是否有如下 2个软连接：\n" \
               "        data -> /mnt/data/data/ \n" \
               "        logs -> /mnt/data/opt/logs/\n" \
               "     若是没有，或是链接的不对(不对就先删掉 sudo rm -rf data)\n" \
               "         创建软连接:  sudo ln -s /mnt/data/data data\n" \
               "                      sudo ln -s /mnt/data/opt/logs logs\n" \
               "---------------------------------------------------------------------"
    print(str_IP_1)
    input_use("008")

'''步骤009---/opt/config/ 中的配置'''
def opt_config_setting():
    str_IP_1 = "\n------------------步骤009---(/opt/config/ 中的配置说明)---------------------------------\n" \
               "  首先 到工程目录下 的 share_func/ 目录下：\n" \
               "        先 af-path 再 cd share_func/\n" \
               "        然后 sudo python3 choose_arm.py\n" \
               "  得到本机的macID ,填写入笔记本对应工厂设备 配置文件中\n\n" \
               "  填入配置文件中  cd /opt/config/  再 vim mac_addr.conf\n" \
               "  再后台管理页面，菜单栏-配置-远程配置-VPN连接控制配置表-新增 中\n" \
               "  填入相同的macID 和机器名称：一般格式(艾纺---试生产1.1B_Second_ARM1)\n" \
               "      @@注意，要是该macID 以00开头，则另想一个其他的字符串(否则VPN连接失败)\n\n" \
               "  查看一下上传配置  cat uploadConfig.json\n" \
               "      一般要确认的是，该设备用于羊毛 还是棉花：\n" \
               "      羊毛：  wool   棉花： wxmfc\n" \
               "---------------------------------------------------------------------"
    print(str_IP_1)
    input_use("009")

'''步骤010---mysql检查'''
def check_mysql():
    str_IP_1 = "\n------------------步骤010---(mysql检查 说明)---------------------------------\n" \
               "  首先 确认一下 mysql 的数据表对不对：\n" \
               "        输入：mysql -p   密码： kt#H@s3AA&qcezJK\n" \
               "        先查看库(有空格和;)： show databases;\n" \
               "        再进入对应的表中： USE `db_cotton_local`;\n" \
               "        查看表结构： show tables;\n" \
               "        现有的table应该有8个，如下：\n" \
               "            tUploadConfig  t_batch  t_err_record  t_file_tracker\n" \
               "            t_image_record  t_point_record  t_supplier  t_take_photo_record\n" \
               "  若是需要重刷的话：需要 cat /mnt/data/file_for_deploy/wuxi_add_color_db_cotton_local.sql\n" \
               "---------------------------------------------------------------------"
    print(str_IP_1)
    input_use("010")

'''步骤011---确认一下 定时任务的内容'''
def check_crontab():
    str_IP_1 = "\n------------------步骤011---(定时任务文件 设定说明)---------------------------------\n" \
               "  首先 确认一下 linux 的编辑模式： sudo select-editor\n" \
               "  然后 进入crontab： sudo crontab -e\n" \
               "  看是否符合标准，标准如下：\n" \
               "        @reboot ( sleep 5 ;/usr/bin/jetson_clocks)\n" \
               "        * */3 * * *  find /mnt/data/data/image_original/ -name '*' -mtime +3 -exec rm -rf {} \;\n" \
               "        * */3 * * *  find /mnt/data/data/image/havebox/ -name '*' -mtime +3 -exec rm -rf {} \;\n" \
               "        * */3 * * *  find /mnt/data/data/image/nobox/ -name '*' -mtime +3 -exec rm -rf {} \;\n" \
               "        * */3 * * *  find /mnt/data/data/upload_image/ -name '*' -mtime +3 -exec rm -rf {} \;\n" \
               "        */1 * * * *  /opt/app/ai-vpn-connect/run.sh > /opt/logs/vpn.log\n" \
               "---------------------------------------------------------------------"
    print(str_IP_1)
    input_use("011")

'''步骤012---确认一下 开机启动文件的内容'''
def check_rclocal():
    str_IP_1 = "\n------------------步骤012---(开机启动文件 设定说明)---------------------------------\n" \
               "  首先 打印一下该文件： cat /etc/rc.local\n" \
               "  看是否符合标准，标准如下：\n" \
               "        /opt/app/ai-common-upload/run.sh &\n" \
               "        mkdir -p /opt/logs/ai-product-haijiang/ai-cotton-api-server-release/\n" \
               "        /opt/app/ai-product-haijiang/ai-cotton-api-server-release/autorun.sh &\n" \
               "        sleep 5s\n" \
               "        cd /opt/app/ai-product-haijiang/ai-hj-service/aiHjService/\n" \
               "        #sudo HOME=/home/appuser nohup python3 daemon.py > /mnt/data/opt/logs/txl01/daemon.log 2>&1 &\n" \
               "---------------------------------------------------------------------"
    print(str_IP_1)
    input_use("012")

'''步骤013---U盘拷贝的指令'''
def copy_Udisk():
    time.sleep(0.5)
    print("\n------------------步骤013---U盘拷贝的指令--------------------------\n")
    mes_input_back1 = input("需要进行U盘拷贝的设定(需要能上网) 吗？(y/n):")
    if mes_input_back1 == "y":
        time.sleep(0.2)
        str_cmd2 = "apt-get install exfat-utils"
        os.system(str_cmd2)
        print("配置完成\n")
    else:
        print("暂不进行 U盘拷贝的设定\n")

'''步骤014---手动IP设定'''
def manual_ip_setting():
    str_IP_1 = "\n------------------步骤014---(手动IP设定说明)---------------------------------\n" \
               "  首先 进入root用户(不然激活和更改没权限)\n  输入：sudo su  (exit退出)\n\n" \
               "  接着 进入可视化配置网口IP 界面\n  输入：nmtui  (按q键或Esc退出)\n\n" \
               "  然后 先在Activate a connection中，查看一下eth0,-4各自对应的连接号\n\n" \
               "  在Edit a connection 选择对应的连接\n\n" \
               "  对于相机连接网口的IP 要在ETHERNET - <SHOW> - MTU 设为 9000\n" \
               "        在IPv4 CONFIGURATION 中选择 Manual\n" \
               "        在Addresses - add 中 输入 172.16.101.1/24\n" \
               "        确保最下面2个[x]都有(按空格进行切换)，最后选择 OK\n\n" \
               "  对于上网通讯的网口IP 还要在 Gateway(网关)和 DNS servers-add 这2处填上路由IP\n" \
               "        一般艾纺设备的路由IP为 192.168.1.11\n" \
               "---------------------------------------------------------------------"
    print(str_IP_1)
    input_use("014")

def process_all():
    print_message_001(0)
    ''' 001 检查和创建所需的文件夹，并赋予权限'''
    check_and_create_path()
    ''' 002 放入预置的AI 模型(1款羊毛，1款棉花)'''
    copy_aimodel()
    ''' 003 解压 解密模型脚本'''
    move_and_tar()
    ''' 004 解压 web文件'''
    tar_web()
    ''' 005 解压 放入项目工程'''
    copy_project_file()
    ''' 006 快捷指令的设定'''
    quick_instructions()
    ''' 007 蓝牙中断配置'''
    bluetooth_setting()
    ''' 008 软连接 提示'''
    tips_soft_links()
    ''' 009 /opt/config/ 中的配置'''
    opt_config_setting()
    ''' 010 mysql检查'''
    check_mysql()
    ''' 011 确认一下 定时任务的内容'''
    check_crontab()
    ''' 012 确认一下 开机启动文件的内容'''
    check_rclocal()
    ''' 013 U盘拷贝的指令'''
    copy_Udisk()
    ''' 014 手动IP设定'''
    manual_ip_setting()

    print("\n\n--------------辅助部署功能-结束------------")



def main_func1():
    process_all()
    # manual_ip_setting()
    # check_rclocal()
    # check_crontab()

if __name__ == "__main__":
    main_func1()