import logging

logger = logging.getLogger(__name__)


class Sensor:
    """Base sensor class."""

    def __init__(self, identifier: str, key: str, offset: float = 0.0):
        """
        :param identifier: unique identifier for the sensor.
        :param key: sensor key. Different robot may have the same key for the same sensor.
        :param offset: initial offset.
        """
        self.id = identifier
        self.key = key
        self.offset = offset
        logger.debug("{}: initialization".format(self.key))
        self.abs_value = 0.0

    def get_value(self) -> float:
        return self.abs_value + self.offset

    def set_value(self, value: float):
        self.abs_value = value - self.offset

    def set_abs_value(self, value: float):
        self.abs_value = value

    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)
        yield "value", self.get_value()

    def __str__(self):
        return "<{} value: {:.2f}>".format(self.key, self.get_value())

    def __repr__(self):
        return self.__str__()
