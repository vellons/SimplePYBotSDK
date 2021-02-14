import logging
import simplepybotsdk
from time import sleep

logging.basicConfig(level=logging.DEBUG, filename='log.log', format='%(asctime)s %(levelname)s %(name)s: %(message)s')

SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 65432
WS_HOST = "127.0.0.1"
WS_PORT = 8080

if __name__ == "__main__":
    print("Example3: Beginning test")
    print("simplepybotsdk version is", simplepybotsdk.__version__)
    robot = simplepybotsdk.RobotRESTSDK(
        config_path="example_webots_khr2hv.json",
        socket_host=SOCKET_HOST,
        socket_port=SOCKET_PORT,
        ws_host=WS_HOST,
        ws_port=WS_PORT,
        robot_speed=1
    )
    robot.ws_configure()
    robot.ws_serve_forever()
    mot = robot.get_motor("head_z")  # Get motor

    sleep(10)
    robot.robot_speed = 0.1  # Make robot's motors move 10x slower
    print("Start position:", mot.get_goal_angle())
    mot.set_goal_angle(34.7)
    print("End position:", mot.get_goal_angle())

    print("Example3: end")
    while True:
        pass
