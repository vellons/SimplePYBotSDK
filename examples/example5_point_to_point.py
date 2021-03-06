import logging
import time
import simplepybotsdk

logging.basicConfig(level=logging.DEBUG, filename='log.log', format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logging.getLogger('websockets.protocol').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.getLogger('asyncio.coroutines').setLevel(logging.ERROR)
logging.getLogger('websockets.server').setLevel(logging.ERROR)

SOCKET_HOST = "localhost"  # Use "0.0.0.0" for external connection
SOCKET_PORT = 65432
REST_HOST = "localhost"  # Use "0.0.0.0" for external connection
REST_PORT = 8000

if __name__ == "__main__":
    print("Example5: Beginning test")
    print("simplepybotsdk version is", simplepybotsdk.__version__)
    robot = simplepybotsdk.RobotRESTSDK(
        config_path="example_webots_khr2hv.json",
        socket_host=SOCKET_HOST,
        socket_port=SOCKET_PORT,
        rest_host=REST_HOST,
        rest_port=REST_PORT,
        robot_speed=1,
        motors_point_to_point_check_per_second=10
    )
    robot.rest_configure()
    robot.rest_serve_forever()

    time.sleep(5)

    print("Start moving")
    robot.move_point_to_point([{"key": "head_z", "goal_angle": -25}], 3, blocking=True)
    robot.move_point_to_point([{"key": "head_z", "goal_angle": 0}], 4)

    ptp0 = [
        {"key": "l_shoulder_x", "goal_angle": -90},
        {"key": "r_shoulder_x", "goal_angle": -90},
        {"key": "l_shoulder_y", "goal_angle": 90},
        {"key": "r_shoulder_y", "goal_angle": 90},
        {"key": "l_elbow_y", "goal_angle": 0},
        {"key": "r_elbow_y", "goal_angle": 0}
    ]
    robot.move_point_to_point(ptp0, 8, blocking=True)

    ptp1 = [
        {"key": "head_z", "goal_angle": 45},
        {"key": "l_shoulder_y", "goal_angle": 90},
        {"key": "r_shoulder_y", "goal_angle": 135},
        {"key": "l_elbow_y", "goal_angle": 0},
        {"key": "r_elbow_y", "goal_angle": 110}
    ]

    ptp2 = [
        {"key": "head_z", "goal_angle": -45},
        {"key": "l_shoulder_y", "goal_angle": 135},
        {"key": "r_shoulder_y", "goal_angle": 90},
        {"key": "l_elbow_y", "goal_angle": 110},
        {"key": "r_elbow_y", "goal_angle": 0}
    ]

    print("Start loop")
    while True:
        start_time = time.time()
        robot.move_point_to_point(ptp1, 3, blocking=True)
        robot.move_point_to_point(ptp2, 3, blocking=True)
        print("Executed in {}".format(time.time() - start_time))
        pass
