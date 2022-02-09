import logging
import time

today = time.localtime()

# 创建Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 创建Handler

# 终端Handler
# consoleHandler = logging.StreamHandler()
# consoleHandler.setLevel(logging.INFO)

# 文件Handler
fileHandler = logging.FileHandler(
    '/mnt/data/opt/logs/ai-product-haijiang/Colordetection/log_' + str(today.tm_year) + '_' + str(
        today.tm_mon) + '_' + str(today.tm_mday) + '.log', mode='a', encoding='UTF-8')
fileHandler.setLevel(logging.NOTSET)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# consoleHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

# 添加到Logger中
# logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)
