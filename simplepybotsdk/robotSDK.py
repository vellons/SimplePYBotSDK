import logging
import threading
import json
import time
from datetime import datetime
import simplepybotsdk.configurations as configurations
from simplepybotsdk.motor import Motor as Motor

logger = logging.getLogger(__name__)


class RobotSDK:
    """Base RobotSDK class."""

    def __init__(self, config_path: str, robot_speed: int = 1, motors_check_per_second: int = None,
                 motors_angle_speed: int = None):
        """
        :param config_path: SimplePYBotSDK json configuration file path.
        :param robot_speed: robot speed. Use this to make robot move slower or faster. Default is 1.
        :param motors_check_per_second: numbers of motor's check per second.
        :param motors_angle_speed: dict with degree/sec for every motor used inside json configuration.
        """
        logger.debug("RobotSDK initialization")
        self.config_path = None
        self.configuration = None
        self.motors = []
        self.robot_speed = robot_speed
        self._motors_check_per_second = motors_check_per_second
        self._motors_angle_speed = motors_angle_speed
        self._thread_motors = None

        if self._motors_check_per_second is None:
            self._motors_check_per_second = configurations.MOTORS_CHECK_PER_SECOND

        if self._motors_angle_speed is None:
            self._motors_angle_speed = configurations.MOTORS_ANGLE_SPEED

        self._init_robot(config_path)

    def _init_robot(self, config_path):
        """
        Read the JSON file configuration from path.
        Then starts robot's component initialization.
        """
        logger.debug("Initialization with file: {}".format(config_path))
        self.config_path = config_path
        try:
            with open(self.config_path) as f:
                self.configuration = json.load(f)
        except Exception as e:
            logger.error(e)
            exit(-1)

        logger.debug("Robot configuration: {}".format(self.configuration))
        self._init_motors()

    def _init_motors(self):
        """Initialize motors from JSON configuration and start thread."""
        for key, m in self.configuration["motors"].items():
            self.motors.append(Motor(
                identifier=m["id"],
                key=key,
                offset=m["offset"],
                motor_type=m["type"],
                angle_limit=m["angle_limit"],
                orientation=m["orientation"]
            ))
        logger.debug("Motors initialization completed. Total motors: {} {}".format(len(self.motors), self.motors))
        self._thread_motors = threading.Thread(target=self._motors_thread_handler, args=())
        self._thread_motors.daemon = True
        self._thread_motors.start()

    def _motors_thread_handler(self):
        """Dedicated thread to move motors to the goal angle position, based on motor angle/sec speed."""
        logger.debug("[motors_thread]: start handling {} motors".format(len(self.motors)))
        last_time = time.time()
        while True:
            if (time.time() - last_time) > ((1 / self._motors_check_per_second) / self.robot_speed):
                last_time = time.time()
                for m in self.motors:  # Watching all motors
                    speed = self._motors_angle_speed[m.motor_type]  # Get motor degree/sec
                    max_step = speed / self._motors_check_per_second
                    if m.abs_goal_angle != m.abs_current_angle:  # Check if is in goal position
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

    def get_motors_list_current_angle(self) -> list:
        """
        :return: list of motors with current absolute angle, id and key.
        """
        motors = []
        for m in self.motors:
            motors.append({"id": m.id, "key": m.key, "angle": round(m.abs_current_angle, 1)})
        return motors

    def get_robot_dict_dump(self) -> dict:
        """
        :return: dict dump of current state of the robot.
        """
        dict_robot = {
            "motors": self.get_motors_list_current_angle(),
            "sensors": {},
            "timestamp": datetime.now().isoformat()
        }
        return dict_robot

    def __str__(self):
        return "<RobotSDK {} with configuration: {}>".format(self.configuration["id"], self.configuration)

    def __repr__(self):
        return self.__str__()
