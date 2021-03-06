import logging
import simplepybotsdk
from time import sleep

logging.basicConfig(level=logging.DEBUG, filename='log.log', format='%(asctime)s %(levelname)s %(name)s: %(message)s')

SOCKET_HOST = "localhost"
SOCKET_PORT = 65432

if __name__ == "__main__":
    print("Example2: Beginning test")
    print("Run also 'example2_socket_client.py' to establish a socket communication to receive updates in real-time")
    robot = simplepybotsdk.RobotSocketSDK(
        config_path="example_webots_khr2hv.json",
        socket_host=SOCKET_HOST,
        socket_port=SOCKET_PORT
    )
    mot = robot.get_motor("head_z")  # Get motor

    sleep(5)
    print("Start position:", mot.get_goal_angle())
    mot.set_goal_angle(74.7)
    print("End position:", mot.get_goal_angle())

    print("Example2: end")
    while True:
        pass
