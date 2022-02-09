import RPi.GPIO as GPIO
import time


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
    White_light = 12
    UV_light = 13

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(White_light, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(UV_light, GPIO.OUT, initial=GPIO.LOW)
    print("GPIO 初始化---低电平")
    time.sleep(5)
    try:
        for i in range(1000):
            if test_choose != 1:
                GPIO.output(White_light, GPIO.HIGH)
                print("白色光源-高电平")
                time.sleep(0.1)
                GPIO.output(White_light, GPIO.LOW)
                print("白色光源-低电平")
                time.sleep(0.7)
            if test_choose != 0:
                GPIO.output(UV_light, GPIO.HIGH)
                print("UV光源-高电平")
                time.sleep(0.1)
                GPIO.output(UV_light, GPIO.LOW)
                print("UV光源-低电平")
                time.sleep(0.7)
            pass

    finally:
        # GPIO.cleanup()
        GPIO.output(White_light, GPIO.LOW)
        GPIO.output(UV_light, GPIO.LOW)



def main_func1():
    exchange_light()



if __name__ == '__main__':
    main_func1()