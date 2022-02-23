import tritonclient.grpc
import time

class TritonClientNew():
    def __init__(self, model_name, input_names, output_names, model_version='1', url='localhost:8001'):
        self.model_name = model_name
        self.model_version = model_version
        self.url = url
        self.input_names = input_names
        self.output_names = output_names
        self.outputs = []
        [self.outputs.append(tritonclient.grpc.InferRequestedOutput(a, class_count=0)) for a in output_names]
        self.triton_client = tritonclient.grpc.InferenceServerClient(url=url, verbose=0)

    def inference(self, img):
        reData = {}
        # t = time.time()
        inputs = []
        # inputs.append(tritonclient.grpc.InferInput('input_data:0', imgArr.shape, 'FP32'))
        # inputs[0].set_data_from_numpy(imgArr)
        inputs.append(tritonclient.grpc.InferInput(self.input_names, img.shape, 'FP32'))
        inputs[0].set_data_from_numpy(img)
        # print("input data time: ", time.time() - t)

        # t = time.time()
        result = self.triton_client.infer(self.model_name, inputs,
                                             request_id=str(1),
                                             model_version=self.model_version,
                                             outputs=self.outputs)
        # print("infer time: ", time.time() - t)
        for out_name in self.output_names:
            reData[out_name] = result.as_numpy(out_name)

        return reData
    # 将数据set_data_from_numpy移到拍照里
    def inferenceNew(self, inputs):
        reData = {}
        # t = time.time()
        # print(self.model_name)
        # print(inputs)
        # print(self.model_version)
        # print(self.outputs)
        result = self.triton_client.infer(self.model_name, inputs,
                                          request_id=str(1),
                                          model_version=self.model_version,
                                          outputs=self.outputs)
        # print("infer time: ", time.time() - t)
        for out_name in self.output_names:
            reData[out_name] = result.as_numpy(out_name)

        return reData


'''
对输入数据进行数据处理
'''
def inputDataProcess(img, input_names):
    inputs = []
    # inputs.append(tritonclient.grpc.InferInput('input_data:0', imgArr.shape, 'FP32'))
    # inputs[0].set_data_from_numpy(imgArr)
    inputs.append(tritonclient.grpc.InferInput(input_names, img.shape, 'FP32'))
    inputs[0].set_data_from_numpy(img)

    return inputs
