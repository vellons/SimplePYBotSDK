import logging

from simplepybotsdk.parserJSON import ParserJSON
from simplepybotsdk.twist import TwistVector

logger = logging.getLogger(__name__)


class ParserJSONCommands(ParserJSON):
    """
    This parser can handle Client to robot message and make response
    """
    
    def __int__(self):
        logger.debug("ParserJSONCommands initialized")
    
    def parse(self, message: dict):
        # All json send to socket or websocket will be parsed by this class

        # Client to robot message
        if "type" in message and message["type"] == "C2R" and "data" in message and "area" in message["data"]:
            data = message["data"]

            # Get robot config
            if data["area"] == "config" and "action" in data and data["action"] == "get_configuration":
                return {
                    "type": "R2C",
                    "data": {
                        "area": "config",
                        "action": "get_configuration",
                        "value": self.robot.configuration
                    }
                }

            # Get robot motion config
            if data["area"] == "config" and "action" in data and data["action"] == "get_configuration_motion":
                return {
                    "type": "R2C",
                    "data": {
                        "area": "config",
                        "action": "get_configuration_motion",
                        "value": self.robot.motion_configuration
                    }
                }

            # Get robot status
            if data["area"] == "status" and "action" in data and data["action"] == "live_status":
                is_absolute = True if "format" in data and data["format"] == "absolute" else False
                return {
                    "type": "R2C",
                    "data": {
                        "area": "status",
                        "action": "live_status",
                        "value": self.robot.get_robot_dict_status(absolute=is_absolute)
                    }
                }

            # Move one or more motors
            if data["area"] == "motors" and "commands" in data and type(data["commands"]):
                try:
                    for c in data["commands"]:
                        m = self.robot.get_motor(c["key"])
                        if m is None:
                            logger.warning("motor with key '{}' not found".format(c["key"]))
                            continue
                        if c["action"] == "set_goal_angle":
                            m.set_goal_angle(c["goal_angle"])
                except Exception as e:
                    logger.warning("Error parsing the C2R motors message {} {}".format(message, e))
                return None

            # Move twist
            if data["area"] == "twist" and "go" in data:
                go = data["go"]
                try:
                    self.robot.set_twist(
                        linear=TwistVector(x=go["linear"]["x"], y=go["linear"]["y"], z=go["linear"]["z"]),
                        angular=TwistVector(x=go["angular"]["x"], y=go["angular"]["y"], z=go["angular"]["z"])
                    )
                except Exception as e:
                    logger.warning("Error parsing the C2R twist message {} {}".format(message, e))
                return None

            logger.warning("Failed to interpret the C2R message {}".format(message))
        return None
