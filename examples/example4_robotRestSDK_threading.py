import logging
import time
import threading

import simplepybotsdk

logging.basicConfig(level=logging.WARNING, filename='log.log', format='%(asctime)s %(levelname)s %(name)s: %(message)s')

SOCKET_HOST = "localhost"  # Use "0.0.0.0" for external connection
SOCKET_PORT = 65432
REST_HOST = "localhost"  # Use "0.0.0.0" for external connection
REST_PORT = 8000

robot = None
thread_communications = None


def communication_handler():
    time.sleep(5)
    while True:
        print(robot.get_robot_dict_status())
        time.sleep(3)


if __name__ == "__main__":
    print("simplepybotsdk version is", simplepybotsdk.__version__)
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

    # Start communication thread
    thread_communications = threading.Thread(target=communication_handler, args=())
    thread_communications.daemon = True
    thread_communications.start()

    print("Waiting for commands...")

    k = "ciao"
    while k != "stop":
        k = input("Type 'stop' to stop: ")
