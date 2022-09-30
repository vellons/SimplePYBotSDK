import logging

logger = logging.getLogger(__name__)


class TwistVector:
    """Vector class (ROS like)."""

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        """
        :param x: x.
        :param y: y.
        :param z: z.
        """
        self.x = x
        self.y = y
        self.z = z

    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)


class Twist:
    """Twist class (ROS like)."""

    def __init__(self, identifier: str, key: str):
        """
        :param identifier: unique identifier for the twist.
        :param key: just a key to identify this object.
        """
        self.id = identifier
        self.key = key
        self.linear = TwistVector()
        self.angular = TwistVector()
        logger.debug("{}: initialization".format(self.key))

    def __iter__(self):
        for key in self.__dict__:
            yield key, dict(getattr(self, key)) if key in ['linear', 'angular'] else getattr(self, key)

    def __str__(self):
        return "<{} linear: {:.2f}, {:.2f}, {:.2f} angular: {:.2f}, {:.2f}, {:.2f}>" \
            .format(self.key, self.linear.x, self.linear.y, self.linear.z,
                    self.angular.x, self.angular.y, self.angular.z, )

    def __repr__(self):
        return self.__str__()
