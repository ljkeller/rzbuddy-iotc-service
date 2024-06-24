import time
import pathlib

EXPORT_PATH = pathlib.Path('/sys/class/gpio/export')
GPIO_PATH = pathlib.Path('/sys/class/gpio/P15_1/')
GPIO_LOGICAL_NUM = 241

def set_gpio(value):
    global GPIO_PATH
    with open(GPIO_PATH/'value', 'w') as gpio_value:
        gpio_value.write(value)

def init_gpio():
    global GPIO_PATH, GPIO_LOGICAL_NUM, EXPORT_PATH
    if not GPIO_PATH.exists():
        with open(EXPORT_PATH, 'w') as export:
            # Writing the logical GPIO pin will give us the P15_1 pin we see in the
            # hardware documentation
            export.write(str(GPIO_LOGICAL_NUM))
        time.sleep(0.1)

    with open(GPIO_PATH/'direction', 'w') as gpio_direction:
        gpio_direction.write('out')

def manual_pwm(high_time, low_time, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        set_gpio('1')
        time.sleep(high_time)
        set_gpio('0')
        time.sleep(low_time)

def main():
    try: 
        init_gpio()
        manual_pwm(0.02, 0.018, 1)
    except KeyboardInterrupt:
        print('Exiting...')
        set_gpio('0')
    finally:
        print('Optionally, unexport GPIO here...')

if __name__ == '__main__':
    main()
