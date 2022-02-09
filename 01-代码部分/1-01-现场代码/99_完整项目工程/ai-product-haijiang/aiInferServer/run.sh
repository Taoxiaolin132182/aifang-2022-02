#!/bin/bash

cd /opt/app/ai-product-injection-mold-inserts-2.0/aiInferServer/

#export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/lib/TensorRT-5.0.2.6

#export PYTHONPATH=$PYTHONPATH:/opt/lib/python3.6-site-packages


export PATH=$PATH:/usr/local/cuda-10.0/bin
echo $PATH

nohup /usr/bin/python3.6 manage.py runserver 0.0.0.0:8000  >/opt/logs/ai-product-injection-mold-inserts-2.0/aiInferServer/log.log 2>&1 &

