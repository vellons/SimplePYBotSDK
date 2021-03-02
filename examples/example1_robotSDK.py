import logging
import simplepybotsdk
from time import sleep

logging.basicConfig(level=logging.DEBUG, filename='log.log', format='%(asctime)s %(levelname)s %(name)s: %(message)s')

if __name__ == "__main__":
    print("Example1: Beginning test")
    robot = simplepybotsdk.RobotSDK(config_path="example_webots_khr2hv.json")
    mot = robot.get_motor("head_z")  # Get motor

    sleep(0.5)
    print("Start position:", mot.get_goal_angle())
    mot.set_goal_angle(34.7)
    print("End position:", mot.get_goal_angle())
    sleep(0.1)
    print("Current position:", mot.get_current_angle())

    # In the meantime, the thread dedicated to the management of the motors will move the servomotor
    # from the current position to the goal position, based on motor angle/sec speed.
    # Take a look at the logs to understand more.

    sleep(7)
    print("Start position:", mot.get_current_angle())
    mot.go_to_goal_angle(2)  # This will wait the motor
    print("Current position:", mot.get_current_angle())

    print("Example1: end")
