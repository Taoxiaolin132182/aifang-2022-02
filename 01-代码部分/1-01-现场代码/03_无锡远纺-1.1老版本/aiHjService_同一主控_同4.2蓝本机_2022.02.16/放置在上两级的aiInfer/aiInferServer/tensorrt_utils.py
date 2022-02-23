import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit
import cv2
from torchvision import transforms
from PIL import Image
import numpy as np


class TensorrtClient():
    def __init__(self, enginePath, itemSize=4):
        """
            enginePath: The path of tensorrt model.
            itemSize: The number of bytes of a single element.
            Default numpy is 4.
        """
        self.cfx = cuda.Device(0).make_context()
        self.V = eval(trt.__version__.split(".")[0])
        self.engine = self.__loadEngine(enginePath)
        self.itemSize = itemSize
        self.inputs, self.outputs, self.bindings = \
            self.__parseConfigCudaMemAlloc()
        self.context = self.engine.create_execution_context()
        # Synchronize the stream
        self.stream = cuda.Stream()
        self.cfx.pop()

    def __loadEngine(self, enginePath):
        TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
        with open(enginePath, "rb") as f, trt.Runtime(TRT_LOGGER) as runtime:
            engine = runtime.deserialize_cuda_engine(f.read())

        return engine

    def __parseConfigCudaMemAlloc(self):
        inputs, outputs, bindings = dict(), dict(), list()
        for binding in self.engine:
            size = trt.volume(self.engine.get_binding_shape(binding))
            dims = self.engine.get_binding_shape(binding)
            dtype = trt.nptype(self.engine.get_binding_dtype(binding))

            # Create empty page locked.
            hArr = cuda.pagelocked_empty(trt.volume(dims), dtype=np.float32)
            dArr = cuda.mem_alloc(hArr.nbytes)

            if self.engine.binding_is_input(binding):
                inputs[binding] = {'name': binding, 'size': size, 'dim': dims,
                                   'dtype': dtype, 'hArr': hArr, 'dArr': dArr}
            else:
                outputs[binding] = {'name': binding, 'size': size, 'dim': dims,
                                    'dtype': dtype, 'hArr': hArr, 'dArr': dArr}

            # Create a stream in which to copy inputs/outputs and run inference.
            bindings.append(int(dArr))

        return inputs, outputs, bindings

    def __transferInputToGPU(self, dInput, data, stream):
        assert eval(f"np.{data.dtype}") == dInput['dtype'], \
            f"Get dtype {eval(f'np.{data.dtype}')} but current {dInput['dtype']}."
        cuda.memcpy_htod_async(
            dInput['dArr'], np.ascontiguousarray(data), stream)

    def __memcpyDtohAsync(self, hOutput, dOutput, stream):
        cuda.memcpy_dtoh_async(hOutput, dOutput, stream)

    def inference(self, imageData):
        """
            imageData: Image to infer. Single ndarrary or a list(tuple, dict)
            ndarray if your model is multi input, ndarray format (n, C, H, W) or
            (n, H, W, C).
        """
        # Transfer input data to the GPU.
        self.cfx.push()
        if isinstance(imageData, (list, tuple, dict)):
            if isinstance(imageData, dict):
                for k, d in imageData.items():
                    assert k in self.inputs.keys(), f"No such output : {k}"
                    self.__transferInputToGPU(
                        self.inputs[k], d, self.stream)
            else:
                for i, data in imageData:
                    self.__transferInputToGPU(
                        list(self.inputs.values())[i], data, self.stream)
        else:
            self.__transferInputToGPU(
                list(self.inputs.values())[0], imageData, self.stream)

        # Run inference.
        if self.V >= 7:
            self.context.execute_async_v2(
                bindings=self.bindings, stream_handle=self.stream.handle)
        else:
            self.context.execute_async(
                bindings=self.bindings, stream_handle=self.stream.handle)

        # Transfer predictions back from the GPU.
        for k, out in self.outputs.items():
            self.__memcpyDtohAsync(out['hArr'], out['dArr'], self.stream)

        # Synchronize the stream
        self.stream.synchronize()
        self.cfx.pop()

        return {o: v['hArr'].reshape(v['dim']) for o, v in self.outputs.items()}


def softmax(x):
    x_exp = np.exp(x)
    x_exp_row_sum = x_exp.sum(axis=-1).reshape(list(x.shape)[:-1] + [1])
    softmax = x_exp / x_exp_row_sum
    return softmax


class TensorrtClientAdd:
    def __init__(self, trt_path, input_size, batch_size, class_name):
        self.tensorrtClientModel = TensorrtClient(trt_path)
        self.class_name = class_name
        self.input_size = input_size
        self.batch_size = batch_size

    def dataProcess(self, img):
        img = cv2.resize(img, (self.input_size, self.input_size), cv2.INTER_NEAREST)
        new_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert('RGB')

        # dataProcess
        mean = [0.5, 0.5, 0.5]
        std = [0.5, 0.5, 0.5]
        transform = transforms.Compose([
            # transforms.Resize([input_shape[1], input_shape[2]]),  # [h,w]
            # transforms.Normalize(mean, std),
            transforms.ToTensor(),
            transforms.Normalize(mean, std)
        ])
        img = transform(new_img).unsqueeze(0)
        img = img.numpy()
        return img

    def inference(self, img):
        imgData = self.dataProcess(img)
        output = self.tensorrtClientModel.inference(imgData)["class_result:0"]
        index = int(np.argmax(softmax(output)))
        return self.class_name[index]


"""
You can inference any tensorrt model with this script. 
The following demo.
if __name__ == "__main__":
    '''
    enginePath: The tensorrt model path.
    img: Image to infer. Single ndarrary or a list(tuple) ndarray 
    if multi input, ndarray format (n, C, H, W) or (n, H, W, C).
    Other args look from the class.
    '''
    tensorrtClient = TensorrtClient(enginePath)
    output = tensorrtClient.inference(img)

"""

import os
import time

if __name__ == "__main__":
    trt_path = '/mnt/data/zzb/pytorch/cotton/20210913/classfy/trt/cotton_yixian_4.pb'
    class_name = ["red", "blue", "black", "other"]
    input_size = 128
    batch_size = 1
    start = time.time()
    yixian_classfy = TensorrtClientAdd(trt_path, input_size, batch_size, class_name)
    # yixian_classfy = TensorrtClient(trt_path)
    print("context time: ", time.time() - start)

    img_path = 'test_pic'

    img_list = os.listdir(img_path)
    for img_name in img_list:
        print(img_name)
        tt = time.time()
        each_path = os.path.join(img_path, img_name)
        img = cv2.imread(each_path)
        out_label = yixian_classfy.inference(img)
        print(out_label)
        print("infer time: ", time.time() - tt)