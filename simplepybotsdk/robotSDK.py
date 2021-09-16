import logging
import threading
import json
import time
from datetime import datetime
import simplepybotsdk.configurations as configurations
from simplepybotsdk import Sensor, Motor

logger = logging.getLogger(__name__)


class RobotSDK:
    """Base RobotSDK class."""

    def __init__(self, config_path: str, robot_speed: float = 1.0, motors_check_per_second: int = None,
                 motors_point_to_point_check_per_second: int = None):
        """
        :param config_path: SimplePYBotSDK json configuration file path.
        :param robot_speed: robot speed. Use this to make robot move slower or faster. Default is 1.
        :param motors_check_per_second: numbers of motor's check per second. Set to 0 to disable dedicated thread.
        :param motors_point_to_point_check_per_second: numbers of motor's movement in a second during point to point.
        """
        logger.info("RobotSDK version {} initialization".format(configurations.VERSION))
        self.config_path = None
        self.configuration = None
        self.sensors = []
        self.motors = []
        self.robot_speed = robot_speed
        self._motors_check_per_second = motors_check_per_second
        self._motors_point_to_point_check_per_second = motors_point_to_point_check_per_second
        self._thread_motors = None
        self.show_log_message = True
        self._record_point_to_point = None  # If not None will be the start of recording
        self._point_to_point_session = []  # Used to record point to point
        self.sleep_avoid_cpu_waste = configurations.SLEEP_AVOID_CPU_WASTE  # Max value is 1

        if self._motors_check_per_second is None:
            self._motors_check_per_second = configurations.MOTORS_CHECK_PER_SECOND
        if self._motors_point_to_point_check_per_second is None:
            self._motors_point_to_point_check_per_second = configurations.MOTORS_POINT_TO_POINT_CHECK_PER_SECOND

        self._init_robot(config_path)

    def _init_robot(self, config_path):
        """
        Read the JSON file configuration from path.
        Then starts robot's component initialization.
        :param config_path: SimplePYBotSDK json configuration file path.
        """
        logger.debug("Initialization with file: {}".format(config_path))
        self.config_path = config_path
        try:
            with open(self.config_path) as f:
                self.configuration = json.load(f)
        except Exception as e:
            logger.error("Initialization configuration error: exception: {}".format(e))
            print("Initialization configuration error: exception: {}".format(e))
            exit(-1)

        logger.debug("Robot configuration: {}".format(self.configuration))
        if ("id" in self.configuration) and ("version" in self.configuration) and ("name" in self.configuration):
            self._init_sensors()
            self._init_motors()
        else:
            logger.error("Initialization configuration error: id, version and name are required in configuration file")
            print("Initialization configuration error: id, version and name are required in configuration file")
            exit(-1)

    def _init_motors(self):
        """Initialize motors from JSON configuration and start thread."""
        if "motors" not in self.configuration:
            logger.error("Initialization configuration error: no motors found in the configuration file")
            print("Initialization configuration error: no motors found in the configuration file")
            exit(-1)
        if "motors_type" not in self.configuration:
            logger.error("Initialization configuration error: no motors_type found in the configuration file")
            print("Initialization configuration error: no motors_type found in the configuration file")
            exit(-1)
        for key, m in self.configuration["motors"].items():
            self.motors.append(Motor(
                identifier=m["id"],
                key=key,
                offset=m["offset"],
                angle_limit=m["angle_limit"],
                orientation=m["orientation"],
                motor_type=m["type"],
                instant_mode=self._motors_check_per_second <= 0
            ))
        logger.debug("Motors initialization completed. Total motors: {} {}".format(len(self.motors), self.motors))
        if self._motors_check_per_second > 0:
            self._thread_motors = threading.Thread(name="motors_thread", target=self._motors_thread_handler, args=())
            self._thread_motors.daemon = True
            self._thread_motors.start()
        else:
            logger.debug("[motors_thread]: thread to control motors disabled by motors_check_per_second parameter")

    def _motors_thread_handler(self):
        """
        Dedicated thread to move motors to the goal angle position, based on motor angle/sec speed.
        If motor abs_goal_angle is different from abs_current_angle the motor will be moved based on its angle_speed.
        """
        logger.debug("[motors_thread]: start handling {} motors".format(len(self.motors)))
        if self.show_log_message:
            print("[motors_thread]: start handling {} motors".format(len(self.motors)))
        last_time = 0
        motors_conf = self.configuration["motors_type"]
        while True:
            if (time.time() - last_time) > ((1 / self._motors_check_per_second) / self.robot_speed):
                last_time = time.time()
                try:
                    for m in self.motors:  # Watching all motors
                        if m.abs_goal_angle != m.abs_current_angle:  # Check if is not in goal position
                            speed = motors_conf[m.motor_type]["angle_speed"]  # Get degree/sec
                            max_step = speed / self._motors_check_per_second  # Get max step for this iteration
                            step = m.abs_goal_angle - m.abs_current_angle
                            if step > max_step:
                                step = max_step
                            elif step < -max_step:
                                step = -max_step

                            logger.debug("[motors_thread]: {}: {:.2f} -> {:.2f} [{:.2f}]".format(m.key,
                                                                                                 m.abs_current_angle,
                                                                                                 m.abs_goal_angle,
                                                                                                 step))
                            m.abs_current_angle = m.abs_current_angle + step
                except Exception as e:
                    logger.error("[motors_thread]: exception: {}".format(e))
                    print("[motors_thread]: exception: {}".format(e))
                    pass
                # Avoid wasting CPU time
                time.sleep((self.sleep_avoid_cpu_waste / self._motors_check_per_second) / self.robot_speed)

    def _init_sensors(self):
        """Initialize sensors from JSON configuration."""
        if "sensors" not in self.configuration:
            logger.debug("No sensors found in the configuration file")
            return
        for key, s in self.configuration["sensors"].items():
            self.sensors.append(Sensor(
                identifier=s["id"],
                key=key,
                offset=s["offset"]
            ))
        logger.debug("Sensors initialization completed. Total sensors: {} {}".format(len(self.sensors), self.sensors))

    def get_motor(self, key: str) -> Motor:
        """
        :param key: key to use to find the motor.
        :return: motor if found or None.
        """
        found = [m for m in self.motors if m.key == key]
        return found[0] if len(found) == 1 else None

    def get_motor_by_id(self, identifier: str) -> Motor:
        """
        :param identifier: id to use to find the motor.
        :return: motor if found or None.
        """
        found = [m for m in self.motors if m.id == identifier]
        return found[0] if len(found) == 1 else None

    def get_sensor(self, key: str) -> Sensor:
        """
        :param key: key to use to find the sensor.
        :return: sensor if found or None.
        """
        found = [s for s in self.sensors if s.key == key]
        return found[0] if len(found) == 1 else None

    def get_sensor_by_id(self, identifier: str) -> Sensor:
        """
        :param identifier: id to use to find the sensor.
        :return: sensor if found or None.
        """
        found = [s for s in self.sensors if s.id == identifier]
        return found[0] if len(found) == 1 else None

    def go_to_pose(self, pose_name: str, seconds: float = 0, blocking: bool = False):
        """
        Method to move the robot in a specific pose defined in the configuration file.
        :param pose_name: name of the pose.
        :param seconds: duration in seconds of the simultaneous movement.
        :param blocking: if False start a dedicated thread to handle the movements.
        """
        if "poses" in self.configuration:
            if pose_name in self.configuration["poses"]:
                pose = self.configuration["poses"][pose_name]
                logger.info("go_to_pose: {}".format(pose_name))
                if seconds == 0:
                    blocking = True  # Avoid starting the thread
                self.move_point_to_point(pose, seconds, blocking)
                return True
            else:
                logger.error("go_to_pose: pose '{}' not found".format(pose_name))
        else:
            logger.error("go_to_pose: no poses found in current configuration")
        return False

    def move_point_to_point(self, motors_goal: dict, seconds: float, blocking: bool = False):
        """
        Method to move several motors simultaneously towards the goal angle position.
        This method calc the future positions of the motors and then use _exec_point_to_point().
        :param motors_goal: dict of {"key": goal_angle, "key": goal_angle}.
        :param seconds: duration in seconds of the simultaneous movement.
        :param blocking: if False start a dedicated thread to handle the movements.
        """
        logger.info("move_point_to_point: {} in {} sec".format(motors_goal, seconds))
        point_to_point = []
        for item in motors_goal:
            m = self.get_motor(item)
            if m is None:
                logger.warning("move_point_to_point: motor with key '{}' not found".format(item))
                continue

            goal = motors_goal[item]
            current = m.get_goal_angle()
            difference = goal - current
            point_to_point.append({
                "key": item,
                "start": current,
                "step": difference / ((seconds * self._motors_point_to_point_check_per_second) if seconds != 0 else 1)
            })

        if self._record_point_to_point is not None:  # If recording save method input
            self._point_to_point_session.append(
                (motors_goal, seconds, round(time.time() - self._record_point_to_point, 3)))

        number_of_steps = self._motors_point_to_point_check_per_second * seconds if seconds != 0 else 1
        if blocking:
            logger.debug("_exec_point_to_point with {} steps: {}".format(number_of_steps, point_to_point))
            self._exec_point_to_point(point_to_point, number_of_steps)
        else:
            logger.debug("_exec_point_to_point thread with {} steps: {}".format(number_of_steps, point_to_point))
            threading.Thread(target=self._exec_point_to_point, args=(point_to_point, number_of_steps,)).start()

    def _exec_point_to_point(self, point_to_point: list, number_of_steps: int):
        """
        Auxiliary method to handle the movement of several motors simultaneously.
        :param point_to_point: list of {"key": key, "start": start, "step": step}.
        :param number_of_steps: duration in seconds of the simultaneous movement.
        """
        step = 0
        last_time = 0
        while step < number_of_steps:
            if (time.time() - last_time) > (1 / self._motors_point_to_point_check_per_second) / self.robot_speed:
                last_time = time.time()
                step = step + 1
                for move in point_to_point:
                    self.get_motor(move["key"]).set_goal_angle(move["start"] + move["step"] * step)
                # Avoid wasting CPU time
                time.sleep(
                    (self.sleep_avoid_cpu_waste / self._motors_point_to_point_check_per_second) / self.robot_speed)

    def point_to_point_start_recording(self):
        """
        Start to save all point to point position received by the method move_point_to_point() or go_to_pose()
        """
        logger.debug("point_to_point_start_recording: start recording")
        self._point_to_point_session = []
        self._record_point_to_point = time.time()

    def point_to_point_stop_recording(self) -> list:
        """
        Stop recording point to point position and return the list.
        The list is composed by (motors_goal, duration in second, time_since_start).
        :return: list of motors with absolute angle, id and key.
        """
        logger.debug("point_to_point_stop_recording: Total step recorded: {}".format(len(self._point_to_point_session)))
        self._record_point_to_point = None
        return self._point_to_point_session

    def point_to_point_play_recorded(self, animation: list, blocking=True):
        """
        Start to save all point to point position received by the method move_point_to_point()
        :param animation: list of (motors_goal, duration in second, time_since_start).
        :param blocking: if False start a dedicated thread to handle each point to point movement.
        """
        if self._record_point_to_point is not None:
            logger.error("point_to_point_reward_recorded: you need to stop recording first")
            return

        previous_time = 0
        for (motors_goal, seconds, time_since_start) in animation:
            time.sleep(time_since_start - previous_time)
            self.move_point_to_point(motors_goal, seconds, blocking=blocking)
            previous_time = seconds + time_since_start

    def get_motors_list_abs_angles(self) -> list:
        """
        :return: list of motors with absolute angle, id and key.
        """
        motors = []
        for m in self.motors:
            motors.append({
                "id": m.id,
                "key": m.key,
                "abs_goal_angle": round(m.abs_goal_angle, 1),
                "abs_current_angle": round(m.abs_current_angle, 1)
            })
        return motors

    def get_motors_list_relative_angles(self) -> list:
        """
        :return: list of motors with relative angle, id and key.
        """
        motors = []
        for m in self.motors:
            motors.append({
                "id": m.id,
                "key": m.key,
                "goal_angle": round(m.to_relative_angle(m.abs_goal_angle), 1),
                "current_angle": round(m.to_relative_angle(m.abs_current_angle), 1)
            })
        return motors

    def get_sensors_list(self) -> list:
        """
        :return: list of sensors with their value.
        """
        sensors = []
        for s in self.sensors:
            sensors.append({
                "id": s.id,
                "key": s.key,
                "value": s.get_value()
            })
        return sensors

    def get_sdk_infos(self) -> dict:
        """
        :return: dict of sdk infos.
        """
        return {
            "robot_speed": self.robot_speed,
            "motors_check_per_second": self._motors_check_per_second
        }

    @staticmethod
    def get_system_infos() -> dict:
        """
        :return: dict of system infos.
        """
        return {
            "timestamp": datetime.now().isoformat()
        }

    def get_robot_dict_status(self, absolute=False) -> dict:
        """
        :param absolute: angle absolute or relative.
        :return: dict dump of current state of the robot.
        """
        dict_robot = {
            "motors": self.get_motors_list_abs_angles() if absolute else self.get_motors_list_relative_angles(),
            "sensors": self.get_sensors_list(),
            "format": "absolute" if absolute else "relative",
            "sdk": self.get_sdk_infos(),
            "system": self.get_system_infos()
        }
        return dict_robot

    def __str__(self):
        return "<RobotSDK {} with configuration: {}>".format(self.configuration["id"], self.configuration)

    def __repr__(self):
        return self.__str__()
