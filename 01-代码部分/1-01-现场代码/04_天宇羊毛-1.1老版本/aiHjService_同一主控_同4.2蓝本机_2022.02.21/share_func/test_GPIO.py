import RPi.GPIO as GPIO
import time
import sys


led_pin = 12  # BOARD pin 12
# but_pin = 18  # BOARD pin 18

def main():
    GPIO.cleanup()
    prev_value = None

    # Pin Setup:
    GPIO.setmode(GPIO.BOARD)  # BOARD pin-numbering scheme
    GPIO.setup(led_pin, GPIO.OUT)  # LED pin set as output
    # GPIO.setup(but_pin, GPIO.IN)  # Button pin set as input

    # Initial state for LEDs:
    GPIO.output(led_pin, GPIO.LOW)
    print("Starting demo now! Press CTRL+C to exit")

    time.sleep(5)

    print('On')
    GPIO.output(led_pin, GPIO.HIGH)

    time.sleep(10)
    print('Off')
    GPIO.output(led_pin, GPIO.LOW)
    GPIO.cleanup()

def exchange_light():
    test_choose = 11  # 0:仅白色，1：仅紫外  大于1：交替
    get_mess1 = sys.argv
    if len(get_mess1) == 2:
        if int(get_mess1[1]) < 10:  # 输入个位整数，开启白光
            print("测试白光")
            test_choose = 0
        else:                      # 输入> 10 的整数，开启紫光
            print("测试紫光")
            test_choose = 1
    else:                          # 不输入，交替
        print("交替测试")
        test_choose = 11
    White_light = 12   # 白光引脚号
    UV_light = 13      # 紫光引脚号
    on_time = 2        # 高电平维持时间
    off_time = 5       # 低电平维持时间

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(White_light, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(UV_light, GPIO.OUT, initial=GPIO.LOW)
    print("GPIO 初始化---低电平")
    time.sleep(5)
    try:
        for i in range(90000):
            if test_choose != 1:
                GPIO.output(White_light, GPIO.HIGH)
                print("白色光源-高电平")
                time.sleep(on_time)
                GPIO.output(White_light, GPIO.LOW)
                print("白色光源-低电平")
                time.sleep(off_time)
            if test_choose != 0:
                GPIO.output(UV_light, GPIO.HIGH)
                print("UV光源-高电平")
                time.sleep(on_time)
                GPIO.output(UV_light, GPIO.LOW)
                print("UV光源-低电平")
                time.sleep(off_time)
            pass

    finally:
        # GPIO.cleanup()
        GPIO.output(White_light, GPIO.LOW)
        GPIO.output(UV_light, GPIO.LOW)



def main_func1():
    exchange_light()



if __name__ == '__main__':
    main_func1()