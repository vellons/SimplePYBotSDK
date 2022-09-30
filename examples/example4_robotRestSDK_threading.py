import logging
import time
import threading
import math

import simplepybotsdk

logging.basicConfig(level=logging.WARNING, filename='log.log', format='%(asctime)s %(levelname)s %(name)s: %(message)s')


class RobotExample(simplepybotsdk.RobotRESTSDK):
    def __init__(self):
        super().__init__(
            config_path="example_webots_khr2hv.json",
            socket_host="0.0.0.0",  # Use "0.0.0.0" for external connection,
            socket_port=65432,
            rest_host="0.0.0.0",  # Use "0.0.0.0" for external connection,
            rest_port=8000
        )
        self.rest_configure()
        self.rest_serve_forever()
        print("{} ready.".format(self.configuration["name"]))

        # Start robot handler thread
        threading.Thread(target=self.robot_handler, args=(), daemon=True).start()

    def robot_handler(self):
        time.sleep(3)
        while True:
            print(self.get_robot_dict_status())
            time.sleep(.3)
            if self.get_twist() is not None:  # ROS like twist object to angular direction and velocity
                x = self.twist.linear.x
                y = self.twist.linear.y
                theta_rad = math.atan2(y, x)
                theta_deg = (theta_rad / math.pi * 180) - 90
                p = math.sqrt((0 - y) ** 2 + (0 - x) ** 2)  # Pythagorean theorem
                print("Angle:{:04} - Speed:{:.2f}".format(int(theta_deg), p))


if __name__ == "__main__":
    print("simplepybotsdk version is", simplepybotsdk.__version__)
    robot = RobotExample()

    k = "ciao"
    while k != "stop":
        k = input("Type 'stop' to stop: ")
