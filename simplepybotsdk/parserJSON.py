from abc import ABC, abstractmethod

from simplepybotsdk import RobotSDK


class ParserJSON(ABC):

    def __init__(self, robot_instance: RobotSDK):
        self.robot = robot_instance
        # One-time configuration and initialization.
        pass

    def __call__(self, message):
        # Code to be executed for each request/response before the action is performed.
        response = self.parse(message)
        # Code to be executed for each request/response after the action is performed.
        return response

    @abstractmethod
    def parse(self, message: dict):
        return None
