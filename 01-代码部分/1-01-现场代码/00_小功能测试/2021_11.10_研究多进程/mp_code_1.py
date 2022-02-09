import time
from multiprocessing import Process

def run(name):
    print('%s runing' % name)
    while True:
        print('%s -------' % name)
        time.sleep(2)
    # print('%s running end' % name)


def run2(name):
    print('%s runing' % name)
    while True:
        print('%s -------' % name)
        time.sleep(2)
    # print('%s 2---running end' % name)


if __name__ == "__main__":
    p1 = Process(target=run,args=('ttanne',))  # 必须加,号
    p2 = Process(target=run2,args=('alice',))
    # p3 = Process(target=run,args=('biantai',))
    # p4 = Process(target=run2,args=('haha',))

    p1.start()
    p2.start()
    # p3.start()
    # p4.start()
    print('主线程')