import cv2 as cv
import numpy as np
import copy
import configparser
import os
import torch
from torchvision import transforms
import torch.nn as nn
import time
from shenhuangmao_classify_seresnet50.seresnet import se_resnet50, senet154
from shenhuangmao_classify_seresnet50.printlogs import logger
import torch.nn.functional as F
from PIL import Image

TASK_PY_PATH = os.path.split(os.path.realpath(__file__))[0][:-33]
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Classify_model:
    def __init__(self, ):
        conf = configparser.ConfigParser()
        conf.read(os.path.join(TASK_PY_PATH, 'color.cfg'))

        self.model_path = str(conf.get("config_classify", "model_path"))
        self.classes = str(conf.get("config_classify", "classes")).split(',')
        self.input_size = int(conf.get("config_classify", "input_size"))
        self.threshold = float(conf.get("config_classify", "threshold"))
        self.__init_Seresnet50(self.classes, self.model_path)
        self.transform = transforms.Compose([
            transforms.Resize((self.input_size, self.input_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def __init_Seresnet50(self, classes, model_path):
        try:
            self.model = se_resnet50(pretrained=None)
            # self.model = senet154(num_classes=len(classes), pretrained=None)
            if self.input_size == 128:
                self.model.avg_pool = nn.AvgPool2d(4, stride=1)
            elif self.input_size == 320:
                self.model.avg_pool = nn.AvgPool2d(10, stride=1)
            self.model.last_linear = nn.Linear(2048, len(classes))
            self.model.load_state_dict(torch.load(model_path))
            self.model = self.model.to(device)
            self.model.eval()
            logger.info('Classify model init Seresnet50 Success')
        except:
            logger.error('Classify model init Seresnet50 Error')

    def __get_imglist(self,imglist):
        imglistout=[]
        for img in imglist:
            img = Image.fromarray(cv.cvtColor(img, cv.COLOR_BGR2RGB)).convert('RGB')
            # img = self.transform(img).unsqueeze(0).float().to(device)
            img = self.transform(img).unsqueeze(0).to(device)
            imglistout.append(img)
        return imglistout


    def forward(self, imglist,imgnum):
        labellist = []
        scorelist = []
        try:
            imglist = self.__get_imglist(imglist)
            imgbatch = torch.cat(imglist)
            output = self.model(imgbatch)
            output = F.softmax(output, dim=1)
            scores = output.cpu().detach().numpy()[:,1]
            for i in range(imgnum):
                score= scores[i]
                try:
                    index = 1 if score > self.threshold else 0
                    label = self.classes[index]
                except:
                    label = ''
                    score = 0
                labellist.append(label)
                scorelist.append(score)
        except:
            logger.error('Classify model detect Error')
        # print(labellist)
        return labellist, scorelist


Model = Classify_model()
