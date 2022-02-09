#!/bin/bash

cd /opt/data/2test_remove/modify_config/

export PATH=$PATH:/usr/local/cuda-10.0/bin
echo $PATH

nohup /usr/bin/python3.6 manage.py runserver 0.0.0.0:8686  >/opt/logs/txl01/modify.log 2>&1 &

