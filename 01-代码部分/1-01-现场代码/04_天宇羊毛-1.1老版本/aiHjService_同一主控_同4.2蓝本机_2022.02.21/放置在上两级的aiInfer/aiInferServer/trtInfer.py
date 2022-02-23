import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit
from torchvision import transforms
import numpy as np
from PIL import Image
import time
import argparse
import cv2

def loadEngine2TensorRT(filepath):
    G_LOGGER = trt.Logger(trt.Logger.WARNING)
    # 反序列化引擎
    with open(filepath, "rb") as f, trt.Runtime(G_LOGGER) as runtime:
        engine = runtime.deserialize_cuda_engine(f.read())
        return engine


# def Compared_infer(ref_infer_data_path, img, ):



def do_inference(context, batch_size, input, output_shape):
    start = time.time()
    # context = engine.create_execution_context()
    # print("context time: ", time.time() - start)
    output = np.empty(output_shape, dtype=np.float32)

    # 分配内存
    d_input = cuda.mem_alloc(1 * input.size * input.dtype.itemsize)
    d_output = cuda.mem_alloc(1 * output.size * output.dtype.itemsize)
    bindings = [int(d_input), int(d_output)]

    # pycuda操作缓冲区
    stream = cuda.Stream()
    # 将输入数据放入device
    cuda.memcpy_htod_async(d_input, input, stream)
    start2 = time.time()

    # 执行模型
    context.execute_async(batch_size, bindings, stream.handle, None)
    # 将预测结果从从缓冲区取出
    cuda.memcpy_dtoh_async(output, d_output, stream)
    end = time.time()
    # print("infer time: ", end-start2)

    # 线程同步
    stream.synchronize()

    #
    # print("output:", type(output))
    # print("output:", output)
    # print("time cost:", end - start)
    return output

def get_shape(engine):
    for binding in engine:
        if engine.binding_is_input(binding):
            input_shape = engine.get_binding_shape(binding)
        else:
            output_shape = engine.get_binding_shape(binding)
    return input_shape, output_shape


def letterbox_image(image, size):
    '''resize image with unchanged aspect ratio using padding'''
    iw, ih = image.size
    w, h = size
    scale = min(w/iw, h/ih)
    nw = int(iw*scale)
    nh = int(ih*scale)

    image = image.resize((nw,nh), Image.BICUBIC)
    new_image = Image.new('RGB', size, (128,128,128))
    new_image.paste(image, ((w-nw)//2, (h-nh)//2))
    shift = [(w-nw)//2, (h-nh)//2]
    return new_image, scale, shift


#############  针对batch_size>1  ###########
class HostDeviceMem(object):
    def __init__(self, host_mem, device_mem):
        """Within this context, host_mom means the cpu memory and device means the GPU memory
        """
        self.host = host_mem
        self.device = device_mem

    def __str__(self):
        return "Host:\n" + str(self.host) + "\nDevice:\n" + str(self.device)

    def __repr__(self):
        return self.__str__()

def allocate_buffers(engine):
    inputs = []
    outputs = []
    bindings = []
    stream = cuda.Stream()
    for binding in engine:
        size = trt.volume(engine.get_binding_shape(binding)) * engine.max_batch_size
        dtype = trt.nptype(engine.get_binding_dtype(binding))
        # Allocate host and device buffers
        host_mem = cuda.pagelocked_empty(size, dtype)
        device_mem = cuda.mem_alloc(host_mem.nbytes)
        # Append the device buffer to device bindings.
        bindings.append(int(device_mem))
        # Append to the appropriate list.
        if engine.binding_is_input(binding):
            inputs.append(HostDeviceMem(host_mem, device_mem))
        else:
            outputs.append(HostDeviceMem(host_mem, device_mem))
    return inputs, outputs, bindings, stream

def inference_batch(context, bindings, inputs, outputs, stream, batch_size=1):
    # Transfer data from CPU to the GPU.
    [cuda.memcpy_htod_async(inp.device, inp.host, stream) for inp in inputs]
    # Run inference.
    context.execute_async(batch_size=batch_size, bindings=bindings, stream_handle=stream.handle)
    # Transfer predictions back from the GPU.
    [cuda.memcpy_dtoh_async(out.host, out.device, stream) for out in outputs]
    # Synchronize the stream
    stream.synchronize()
    # Return only the host outputs.
    return [out.host for out in outputs]

def postprocess_the_outputs(h_outputs, shape_of_output):
    h_outputs = h_outputs.reshape(*shape_of_output)
    return h_outputs


# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description = "TensorRT do inference")
#     parser.add_argument("--batch_size", type=int, default=10, help='batch_size')
#     # parser.add_argument("--img_path", type=str, default='test.jpg', help='cache_file')
#     parser.add_argument("--img_path", type=str, default='test/test/39_h/10.jpg', help='cache_file')
#     parser.add_argument("--engine_file_path", type=str, default='tensorrt/1019-svam-1000-hue-192_1-4_fp16_b10_1103.pb', help='engine_file_path')
#     args = parser.parse_args()
#
#     engine_path = args.engine_file_path
#     engine = loadEngine2TensorRT(engine_path)
#     context = engine.create_execution_context()
#
#     # Allocate buffers for input and output
#     inputs, outputs, bindings, stream = allocate_buffers(engine)  # input, output: host # bindings
#
#     img = Image.open(args.img_path)
#
#     input_shape, output_shape = get_shape(engine)
#
#     new_img, _, _ = letterbox_image(img, (input_shape[1], input_shape[2]))
#     mean = [0.5, 0.5, 0.5]
#     std = [0.5, 0.5, 0.5]
#     transform = transforms.Compose([
#         # transforms.Resize([input_shape[1], input_shape[2]]),  # [h,w]
#         # transforms.Normalize(mean, std),
#         transforms.ToTensor(),
#         transforms.Normalize(mean, std)
#         ])
#     img = transform(new_img).unsqueeze(0)
#     img = img.numpy()
#
#     img_concat = np.concatenate((img, img), axis=0)
#     for i in range(3):
#         img_concat = np.concatenate((img_concat, img), axis=0)
#     # img_concat = []
#     # for i in range(10):
#     #     img_concat.append(img)
#
#     # Load data to the buffer
#     inputs[0].host = img_concat.reshape(-1)
#     start_time = time.time()
#
#     trt_outputs = inference_batch(context, bindings=bindings, inputs=inputs, outputs=outputs, stream=stream,
#                                   batch_size=5)  # numpy data
#     print("infer time: ", time.time()-start_time)
#
#     shape_of_output = (10, output_shape[0])
#     output = postprocess_the_outputs(trt_outputs[0], shape_of_output)
#     print(output)


def softmax(x):
    x_exp = np.exp(x)
    x_exp_row_sum = x_exp.sum(axis=-1).reshape(list(x.shape)[:-1] + [1])
    softmax = x_exp / x_exp_row_sum
    return softmax


class TensorrtClient():
    def __init__(self, trt_path, input_size, batch_size, class_name):
        self.engine = loadEngine2TensorRT(trt_path)
        self.context = self.engine.create_execution_context()
        self.input_shape, self.output_shape = get_shape(self.engine)
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
        output = do_inference(self.context, self.batch_size, imgData, self.output_shape)
        index = int(np.argmax(softmax(output)))
        return self.class_name[index]

import os

if __name__ == "__main__":
    trt_path = '/mnt/data/zzb/pytorch/cotton/20210913/classfy/trt/cotton_yixian_4.pb'
    class_name = ["red", "blue", "black", "other"]
    input_size = 128
    batch_size = 1
    start = time.time()
    yixian_classfy = TensorrtClient(trt_path, input_size, batch_size, class_name)
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




# if __name__ == "__main__":
#     trt_path = '/mnt/data/zzb/pytorch/cotton/20210913/classfy/trt/cotton_yixian_4.pb'
#     start = time.time()
#     engine = loadEngine2TensorRT(trt_path)
#     context = engine.create_execution_context()
#     print("context time: ", time.time() - start)
#
#     input_shape, output_shape = get_shape(engine)
#
#     img_path = 'test_pic'
#     class_name = ["red", "blue", "black", "other"]
#     input_size = 128
#     batch_size = 1
#     img_list = os.listdir(img_path)
#     for img_name in img_list:
#         print(img_name)
#         tt = time.time()
#         each_path = os.path.join(img_path, img_name)
#         img = cv2.imread(each_path)
#         img = cv2.resize(img, (input_size, input_size), cv2.INTER_NEAREST)
#         new_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert('RGB')
#
#         # dataProcess
#         mean = [0.5, 0.5, 0.5]
#         std = [0.5, 0.5, 0.5]
#         transform = transforms.Compose([
#             # transforms.Resize([input_shape[1], input_shape[2]]),  # [h,w]
#             # transforms.Normalize(mean, std),
#             transforms.ToTensor(),
#             transforms.Normalize(mean, std)
#         ])
#         img = transform(new_img).unsqueeze(0)
#         img = img.numpy()
#         print("img process time: ", time.time() - tt)
#         t1 = time.time()
#         output = do_inference(context, batch_size, img, output_shape)
#         print("infer time: ", time.time() - t1)
#         index = int(np.argmax(softmax(output)))
#         print("class name: ", class_name[index])
