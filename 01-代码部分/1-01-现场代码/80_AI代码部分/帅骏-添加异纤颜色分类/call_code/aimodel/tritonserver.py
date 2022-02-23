"""
tritonserver class
"""
import subprocess
import os
import time

'''
获取进程id
'''


def get_process_id(name):
    child = subprocess.Popen(["pgrep", "-f", name], stdout=subprocess.PIPE, shell=False)
    response = child.communicate()[0]
    return response


'''
测试Triton_server是否已经初始化完成
'''


def Test_connect_Triton_server(curl, timeInterval, allTime):
    connect_flag = False
    num = int(allTime / timeInterval)
    for i in range(num):
        result = subprocess.getstatusoutput(curl)
        if "OK" in result[1]:
            connect_flag = True
            break
        time.sleep(timeInterval)
    return connect_flag


class tritonserver:
    def __init__(self, model_config):
        self.model_config = model_config

    def kill_tritonserver(self):
        response = get_process_id("tritonserver")
        pid_list = response.decode().split('\n')
        for pid in pid_list:
            if pid == '': continue
            result = os.system("sudo kill -9 " + str(pid))
            if result == 0:
                print("pid %s kill success" % pid)

    def start_tritonserver(self):
        # server_cmd = '/opt/tritonserver/tritonserver/install/bin/tritonserver --model-repository=/mnt/data/zhouzhubin/trt_model --model-control-mode=poll --repository-poll-secs=60 --http-port=9998 --allow-metrics=False --grpc-port=9999'
        server_cmd = '%s --model-repository=%s --http-port=%d --allow-metrics=False --grpc-port=%d' % (
            self.model_config["trtServerModelParam"]["tritonServer"],
            self.model_config["trtServerModelParam"]["serverModelPath"],
            self.model_config["trtServerModelParam"]["http_port"], self.model_config["trtServerModelParam"][
                "grpc_port"])  # 去除模型热更新  --model-control-mode=poll --repository-poll-secs=60
        os.system("nohup " + server_cmd + ' >/dev/null 2>&1 &')  # 不生成nohup.out文件

        # 判断tritonserver是否已经起来
        curl_server = 'curl -v localhost:%d/v2/health/ready' % self.model_config["trtServerModelParam"]["http_port"]
        connect_flag = Test_connect_Triton_server(curl_server,
                                                  self.model_config["trtServerModelParam"]["timeInterval"],
                                                  self.model_config["trtServerModelParam"]["allTime"])
        return connect_flag

