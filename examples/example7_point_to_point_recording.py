import logging
import time
import simplepybotsdk

logging.basicConfig(level=logging.WARNING, filename='log.log', format='%(asctime)s %(levelname)s %(name)s: %(message)s')

SOCKET_HOST = "localhost"  # Use "0.0.0.0" for external connection
SOCKET_PORT = 65432
REST_HOST = "localhost"  # Use "0.0.0.0" for external connection
REST_PORT = 8000

if __name__ == "__main__":
    print("Example7: Beginning test")
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

    print("Start moving and recording")
    start_time = time.time()
    robot.point_to_point_start_recording()  # Start recording
    robot.go_to_pose("standby")
    robot.move_point_to_point({"head_z": -40}, 2, blocking=True)

    ptp0 = {
        "l_shoulder_x": -90,
        "r_shoulder_x": -90,
        "l_shoulder_y": 90,
        "r_shoulder_y": 90,
        "l_elbow_y": 0,
        "r_elbow_y": 0
    }
    robot.move_point_to_point(ptp0, 4, blocking=True)

    time.sleep(5)

    ptp1 = {
        "head_z": 45,
        "l_shoulder_y": 90,
        "r_shoulder_y": 135,
        "l_elbow_y": 0,
        "r_elbow_y": 110
    }

    ptp2 = {
        "head_z": -45,
        "l_shoulder_y": 135,
        "r_shoulder_y": 90,
        "l_elbow_y": 110,
        "r_elbow_y": 0
    }

    robot.move_point_to_point(ptp1, 3, blocking=True)
    robot.move_point_to_point(ptp2, 3, blocking=True)
    robot.move_point_to_point(ptp1, 3, blocking=True)
    robot.move_point_to_point(ptp2, 3, blocking=True)
    robot.go_to_pose("standby")

    animation = robot.point_to_point_stop_recording()
    print("Stop recording of {} seconds\n{}".format(time.time() - start_time, animation))
    time.sleep(2)

    print("Start play recorded animation")
    start_time = time.time()
    robot.point_to_point_play_recorded(animation)
    print("Rewind ended in seconds: {}".format(time.time() - start_time))

    time.sleep(10)
