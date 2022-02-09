#!/bin/bash

cd /opt/app/ai-product-haijiang/ai-cotton-api-server-release/

ulimit -c unlimited
ulimit -a

./service stop

./service start
