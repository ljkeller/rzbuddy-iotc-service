# Quick and dirty hardware testing that's validated and performed manually

import unittest
import time

import servo_controller.servo_manager as servo_manager


class TestServo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert (servo_manager.init_gpio())
        assert ("[none]" in servo_manager.get_gpio_state().lower())

    def setUp(self):
        # Just to make visual inspection easier
        time.sleep(0.5)

    def test_perform_full_rotations_1(self):
        assert ("[none]" in servo_manager.get_gpio_state().lower())
        servo_manager.perform_full_rotations(1)
        assert ("[none]" in servo_manager.get_gpio_state().lower())

    def test_perform_full_rotations_2(self):
        assert ("[none]" in servo_manager.get_gpio_state().lower())
        servo_manager.perform_full_rotations(2)
        assert ("[none]" in servo_manager.get_gpio_state().lower())


if __name__ == '__main__':
    unittest.main()
