import time
import pathlib

# TODO: swap to controlling servo via LED proxy. Setting red LED will rotate servo
COMMON_GPIO_PATH = pathlib.Path('/sys/class/leds/led_red/trigger')

SERVO_DURATION_s = 1
SERVO_COMM_PERIOD_s = 0.02
TIME_BETWEEN_MULTIPLE_ROTATIONS_s = 0.5

SYSFS_GPIO_ON = 'default-on'
SYSFS_GPIO_OFF = 'none'


def write_sysfs_file(fp, value):
    with open(fp, 'w') as sysfs_file:
        sysfs_file.write(value)


def init_gpio() -> bool:
    """
    Initialize the GPIO pin for the servo motor through the sysfs interface.

    Returns True if successful, False otherwise
    """

    try:
        with open(COMMON_GPIO_PATH, 'w') as common_gpio_fp:
            common_gpio_fp.write(SYSFS_GPIO_OFF)

        return True
    except Exception as e:
        print(f"Error initializing GPIO: {e}")
        return False


def perform_full_rotations(rotations=1):
    """
    Perform a number of rotations with the servo motor.

    Default: 1 rotation.
    """
    for _ in range(rotations):
        trigger_rotation()
        time.sleep(SERVO_DURATION_s)


def trigger_rotation():
    """
    Trigger a rotation with the servo motor.
    """
    try:
        write_sysfs_file(COMMON_GPIO_PATH, SYSFS_GPIO_ON)
        # RTOS will detect gpio change and rotate servo once. After that,
        # it can't be rotated again until the gpio is set to off
        time.sleep(0.25)
        write_sysfs_file(COMMON_GPIO_PATH, SYSFS_GPIO_OFF)
        print("Triggered rotation via GPIO toggle.")
    except Exception as e:
        print(f"Error triggering rotation: {e}")


def get_gpio_state():
    """
    Get the current state of the GPIO pin.

    Returns the state as a string.
    """
    with open(COMMON_GPIO_PATH, 'r') as common_gpio_fp:
        return common_gpio_fp.read().strip()
