import os
import time








def test1():
    t1 = time.time()
    path1 = "/mnt/data/data/aimodel"
    name1 = "Awool_yolov3.pb"
    name2 = "Bwool_yolov3.pb"

    path_file1 = os.path.join(path1, name1)
    path_file2 = os.path.join(path1, name2)
    code1 = "rm -f " + path_file1 + " &"
    code2 = "rm -f " + path_file2 + " &"
    if os.path.exists(path_file1):
        print("1-ok")
        os.system(code1)
    time.sleep(0.5)
    if os.path.exists(path_file2):
        print("2-ok")
        os.system(code2)

    print("speed time:{}".format(round(time.time() - t1, 4)))

if __name__ == "__main__":
    test1()