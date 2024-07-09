# Quick and dirty hardware testing that's validated and performed manually

import unittest
import time

import servo_controller.servo_manager as servo_manager


class TestServo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert (servo_manager.init_gpio())

    def setUp(self):
        # Just to make visual inspection easier
        time.sleep(0.5)

    def test_perform_full_rotations_1(self):
        servo_manager.perform_full_rotations(1)

    def test_perform_full_rotations_2(self):
        servo_manager.perform_full_rotations(2)

    # TODO: Test partial rotations
    # TODO: Add and test cleanup


if __name__ == '__main__':
    unittest.main()
