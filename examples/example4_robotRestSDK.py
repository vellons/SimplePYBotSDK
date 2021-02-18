import logging
import simplepybotsdk
from time import sleep

logging.basicConfig(level=logging.DEBUG, filename='log.log',
                    format='%(asctime)s %(levelname)s %(name)s %(thread)d: %(message)s')
logging.getLogger('websockets.protocol').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.getLogger('asyncio.coroutines').setLevel(logging.ERROR)
logging.getLogger('websockets.server').setLevel(logging.ERROR)


SOCKET_HOST = "localhost"  # Use "0.0.0.0" for external connection
SOCKET_PORT = 65432
REST_HOST = "localhost"  # Use "0.0.0.0" for external connection
REST_PORT = 8000

if __name__ == "__main__":
    print("Example4: Beginning test")
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
    mot = robot.get_motor("head_z")  # Get motor

    sleep(10)
    robot.robot_speed = 0.1  # Make robot's motors move 10x slower
    print("Start position:", mot.get_goal_angle())
    mot.set_goal_angle(34.7)
    print("End position:", mot.get_goal_angle())

    print("Example4: end")
    while True:
        pass