__author__ = 'youjiang'

# coding=utf-8
import sys
import os
import time
import shutil
import subprocess
import requests
from requests import exceptions
import logging

max_process = 1
min_process = 1
sudo_pwd = 'Welcome!@#'
log = logging.getLogger()
logging.basicConfig(format='%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def start():
    global max_process
    # 获取当前路径
    path = os.getcwd()
    path = path.strip()
    log.info("the work directory is %s" % path)
    run("ai_hj_run_service.py", "/opt/logs/txl01/ctrl.log")


def check_process_exist(process_key):
    log.info("check the process if exist %s" % process_key)
    child = subprocess.Popen(["pgrep", "-f", process_key], stdout=subprocess.PIPE, shell=False)
    pid = child.communicate()[0]
    if not pid or len(pid) == 0:
        log.info("the [%s] process is not exist" % process_key)
        return None
    pid_str = str(pid, encoding="utf-8").strip()  # bytes to string
    if pid_str.find('\n') > 0:
        pids = pid_str.split('\n')
        pid = pids[-1]
    log.info("the process ID: {}".format(pid_str))
    return pid


def check_init_status(init_file):
    try:
        f = open(init_file, "r")
        line = f.readline()
        if line and len(line) > 0:
            if line.strip() == "success":
                return True
        f.close()
    except:
        log.info("read init info error")
        return False


def run(execute_name, output_file):
    info = "%s start at %s" % (execute_name, time.strftime('%H:%M:%S', time.localtime(time.time())))
    log.info(info)
    # os.system('cd %s & start visa.bat' % pid)
    # sudo nohup python3 ai_hj_run_service.py > /opt/logs/txl01/ctrl.log 2>&1 &
    cmd_str = "echo %s|sudo -S nohup python3 %s > %s 2>&1 &" % (sudo_pwd, execute_name, output_file)
    result = os.system(cmd_str)
    if result == 0:
        log.info("start the process [%s] successfully" % execute_name)


def stop(pid):
    info = "%s stop at %s" % (pid, time.strftime('%H:%M:%S', time.localtime(time.time())))
    log.info(info)
    cmd_str = "echo %s|sudo -S kill -9 %s" % (sudo_pwd, pid)
    result = os.system(cmd_str)
    if result == 0:
        log.info("stop the process [%s] successfully" % pid)


def daemon():
    log.info("daemon start")
    # upload_agent_info("daemon")
    global min_process
    while True:
        pid = check_process_exist("python3 ai_hj_run_service.py")
        if pid is None:
            log.info("the service is not running")
            start()
            time.sleep(20)
        else:
            init_ok = check_init_status("init.txt")
            if init_ok:
                log.info("the service process is ok")
                time.sleep(10)
            else:
                log.info("ready to stop the service process [%s]" % pid)
                stop(pid)
                time.sleep(3)
                log.info("ready to restart the service process")
                start()
                time.sleep(20)


def deploy(file):
    # 获取当前路径
    path = os.popen('cd').readlines()[0]
    path = path.strip()
    source_file_path = "%s\\%s" % (path, file)
    for i in range(1, 10):
        e_path = "%s\\hw%d" % (path, i)
        file_path = "%s\\%s" % (e_path, file)
        if os.path.exists(file_path):
            os.remove(file_path)
        shutil.copy(source_file_path, file_path)
        time.sleep(2)
    os.remove(source_file_path)


def get_time():
    time_a = time.time()
    time_url = "http://www.vmall.com/serverTime.jsp"
    try:
        response = requests.get(time_url, timeout=3)
        source = response.content
        source = source.strip()
        source = source.strip(";")
        if source.find("=") > 0:
            st = source.split("=")[1]
            time_a = int(st) / 1000.0
    except (exceptions.ConnectionError, exceptions.SSLError, exceptions.ReadTimeout, exceptions.Timeout) as err:
        log.error("connection to website %s error %s" % (err.request, err.message))
    time_s = time.strftime('%H:%M:%S', time.localtime(time_a))
    time_f = time_s.split(':')
    seconds = 60 * int(time_f[1]) + int(time_f[2])
    return int(time_f[0]), seconds


def upload_agent_info(version):
    try:
        f = open("version2.txt")
        line = f.readline()
        if line and len(line) > 0:
            version = "%s_%s" % (version, line.strip())
        f.close()
    except:
        log.info("load version info error")
    url = "http://121.41.83.55:9800/hw/version/%s/" % version
    try:
        response = requests.get(url)
        log.info(response.text)
    except (exceptions.ConnectionError, exceptions.SSLError, exceptions.Timeout) as err:
        log.error("connection to website %s error %s" % (err.request, err.message))


reg_flag = True
if reg_flag:
    try:
        fun = sys.argv[1]
    except:
        fun = 'daemon'
    if fun == 'start':
        start()
    elif fun == 'daemon':
        daemon()
    elif fun == 'deploy':
        if len(sys.argv) < 2:
            sys.exit(0)
        deploy(sys.argv[2])
else:
    time.sleep(10)
