import logging

logger = logging.getLogger(__name__)


class Motor:
    """Base Motor class."""

    def __init__(self, identifier: str, key: str, offset: int, motor_type: str, angle_limit: tuple, orientation: str):
        """
        :param identifier: unique identifier for the motor.
        :param key: motor key. Different robot may have the same key for a motor that do the same movement.
        :param offset: initial offset.
        :param motor_type: motor string type. Used to know it angle/sec speed.
        :param angle_limit: movement range. Example: [-90, 90].
        :param orientation: "direct" or "indirect".
        """
        self.id = identifier
        self.key = key
        self.offset = offset
        self.motor_type = motor_type
        self.angle_limit = angle_limit
        self.orientation = 1 if orientation == "indirect" else 0
        self.abs_goal_angle = 0
        self.abs_current_angle = 0
        logger.debug("{}: initialization".format(self.key))
        self.set_goal_angle(0)

    def get_goal_angle(self) -> float:
        """
        :return: goal angle position for the motor.
        """
        if self.orientation == 1:
            return self.abs_goal_angle + self.offset
        else:
            return self.abs_goal_angle - self.offset

    def set_goal_angle(self, angle: float) -> float:
        """
        :param angle: new goal angle position to set.
        :return: the new goal position.
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
        return self.get_goal_angle()

    def __str__(self):
        return "<{} angle: {:.2f} - {}>".format(self.key, self.get_goal_angle(), self.orientation)

    def __repr__(self):
        return self.__str__()
