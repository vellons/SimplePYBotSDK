import logging
import simplepybotsdk
from time import sleep

logging.basicConfig(level=logging.WARNING, filename='log.log', format='%(asctime)s %(levelname)s %(name)s: %(message)s')

SOCKET_HOST = "localhost"  # Use "0.0.0.0" for external connection
SOCKET_PORT = 65432
REST_HOST = "localhost"  # Use "0.0.0.0" for external connection
REST_PORT = 8000

if __name__ == "__main__":
    print("Example4: Beginning test")
    print("simplepybotsdk version is", simplepybotsdk.__version__)
    # Set SOCKET_AS_WEB_SOCKET environment var to False to use standard socket
    robot = simplepybotsdk.RobotRESTSDK(
        config_path="example_webots_khr2hv.json",
        socket_host=SOCKET_HOST,
        socket_port=SOCKET_PORT,
        rest_host=REST_HOST,
        rest_port=REST_PORT,
        robot_speed=1
    )
    robot.rest_configure()
    robot.rest_serve_forever()

    sleep(10)
    robot.robot_speed = 0.2  # Make robot's motors move 5x slower
    print("goto t")
    robot.go_to_pose("t")
    sleep(7)
    print("goto standby")
    robot.go_to_pose("standby", 10, blocking=True)

    print("Example4: end")
    while True:
        pass
