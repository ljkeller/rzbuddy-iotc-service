import time
import pathlib

# To understand this mapping, refer to the hardware documentation
EXPORT_PATH = pathlib.Path('/sys/class/gpio/export')
GPIO_PATH = pathlib.Path('/sys/class/gpio/P15_1/')
GPIO_LOGICAL_NUM = 241

SERVO_DURATION_s = 1
SERVO_COMM_PERIOD_s = 0.02


def set_gpio(value):
    with open(GPIO_PATH/'value', 'w') as gpio_value:
        gpio_value.write(value)


def init_gpio() -> bool:
    """
    Initialize the GPIO pin for the servo motor through the sysfs interface.

    Returns True if successful, False otherwise
    """

    try:
        if not GPIO_PATH.exists():
            with open(EXPORT_PATH, 'w') as export:
                # Writing the logical GPIO pin will give us the P15_1 pin
                # we see in the hardware documentation
                export.write(str(GPIO_LOGICAL_NUM))
            time.sleep(0.1)

        with open(GPIO_PATH/'direction', 'w') as gpio_direction:
            gpio_direction.write('out')

        return True
    except Exception as e:
        (f"Error initializing GPIO: {e}")
        return False


def perform_rotation(rotations=1):
    """
    Perform a number of rotations with the servo motor.

    Default: 1 rotation.
    """
    for _ in range(rotations):
        manual_pwm()


def manual_pwm(pulse_width=0.0009, duration=0.92):
    """
    Primary interface to control the servo motor.

    The default arguments should rotate the servo one rotation (verified
    experimentally).
    """
    end_time = time.time() + duration
    while time.time() < end_time:
        set_gpio('1')
        time.sleep(pulse_width)
        set_gpio('0')
        time.sleep(SERVO_COMM_PERIOD_s - pulse_width)
