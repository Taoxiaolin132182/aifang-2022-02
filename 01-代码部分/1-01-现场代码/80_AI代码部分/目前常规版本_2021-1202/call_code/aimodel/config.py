import json


'''
加载配置文件
'''


def load_config(configPath):
    with open(configPath, encoding='utf-8-sig') as f:
        config = json.load(f)
    config["class_names"] = list(config["class_name_score_factors"].keys())
    return config