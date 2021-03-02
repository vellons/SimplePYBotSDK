import logging
from time import sleep

logger = logging.getLogger(__name__)


class Motor:
    """Base Motor class."""

    def __init__(self, identifier: str, key: str, offset: int, angle_limit: tuple, orientation: str, motor_type: str,
                 instant_mode: bool = False):
        """
        :param identifier: unique identifier for the motor.
        :param key: motor key. Different robot may have the same key for a motor that do the same movement.
        :param offset: initial offset.
        :param angle_limit: movement range. Example: [-90, 90]. (Relative angles)
        :param orientation: "direct" or "indirect".
        :param motor_type: motor string type. Used to know it angle/sec speed.
        :param instant_mode: True if you want abs_goal_angle and abs_current_angle to be equal when use set_goal_angle.
            If False motors thread will be activated in RobotSDK to move motors base on angle_speed.
        """
        self.id = identifier
        self.key = key
        self.offset = offset
        self.angle_limit = angle_limit
        self.orientation = 1 if orientation == "indirect" else 0
        self.motor_type = motor_type
        self.abs_goal_angle = 0.0
        self.abs_current_angle = 0.0
        logger.debug("{}: initialization".format(self.key))
        self.instant_mode = True
        self.set_goal_angle(0)
        self.instant_mode = instant_mode

    def get_current_angle(self) -> float:
        """
        :return: relative current angle position of the motor.
        """
        return self.to_relative_angle(self.abs_current_angle)

    def get_goal_angle(self) -> float:
        """
        :return: relative goal angle position for the motor.
        """
        return self.to_relative_angle(self.abs_goal_angle)

    def set_goal_angle(self, angle: float) -> float:
        """
        :param angle: new relative goal angle position to set.
        :return: the new relative goal position.
        """
        if self.angle_limit[0] <= angle <= self.angle_limit[1]:
            future_angle = angle + self.offset
            self.abs_goal_angle = future_angle if self.orientation == 0 else -future_angle
            logger.info("{}: set_goal_angle: {:.2f} [{:.2f}]".format(self.key, angle, self.abs_goal_angle))

        elif self.angle_limit[0] > angle:
            future_angle = self.angle_limit[0] + self.offset
            self.abs_goal_angle = future_angle if self.orientation == 0 else -future_angle
            logger.warning("{}: set_goal_angle: {:.2f} -> {:.2f} [{:.2f}]".format(self.key, angle, self.angle_limit[0],
                                                                                  self.abs_goal_angle))
        elif self.angle_limit[1] < angle:
            future_angle = self.angle_limit[1] + self.offset
            self.abs_goal_angle = future_angle if self.orientation == 0 else -future_angle
            logger.warning("{}: set_goal_angle: {:.2f} -> {:.2f} [{:.2f}]".format(self.key, angle, self.angle_limit[1],
                                                                                  self.abs_goal_angle))
        if self.instant_mode is True:
            self.abs_current_angle = self.abs_goal_angle
        return self.get_goal_angle()

    def go_to_goal_angle(self, angle: float) -> float:
        """
        set_goal_angle() but wait until the motor is in the goal position.
        :param angle: new relative goal angle position to set.
        :return: the new relative goal position.
        """
        self.set_goal_angle(angle)
        while self.get_current_angle() != angle:
            sleep(0.0166)
        return self.get_goal_angle()

    def to_relative_angle(self, angle: float) -> float:
        """
        :param angle: absolute angle to convert
        :return: relative angle
        """
        if self.orientation == 1:
            return - angle - self.offset
        else:
            return angle - self.offset

    def to_abs_angle(self, angle: float) -> float:
        """
        :param angle: relative angle to convert
        :return: absolute angle
        """
        if self.orientation == 1:
            return - angle + self.offset
        else:
            return angle + self.offset

    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)
        yield "goal_angle", self.to_relative_angle(self.abs_goal_angle)
        yield "current_angle", self.to_relative_angle(self.abs_current_angle)

    def __str__(self):
        return "<{} angle: {:.2f} - {}>".format(self.key, self.get_goal_angle(), self.orientation)

    def __repr__(self):
        return self.__str__()
