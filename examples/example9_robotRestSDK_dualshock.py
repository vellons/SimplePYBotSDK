import logging
import time
import threading
import math

#get simplebybotsdk form local
import sys
sys.path.insert(0, '../')
import simplepybotsdk

from pyPS4Controller.controller import Controller

logging.basicConfig(level=logging.WARNING, filename='log.log', format='%(asctime)s %(levelname)s %(name)s: %(message)s')

joyX = 0
joyY = 0

class MyController(Controller):

    def __init__(self, **kwargs):
        Controller.__init__(self, **kwargs)

    def connect():
        print("Connected")

    def disconnect():
        print("Disconnected")

    def on_R3_left(self, value):    
        print("R3_left")
        global joyX
        joyX = value

    def on_R3_right(self, value):
        print("R3_right")
        global joyX
        joyX = value

    def on_R3_up(self, value):
        print("R3_up")
        global joyY
        joyY = value

    def on_R3_down(self, value):
        print("R3_down")
        global joyY
        joyY = value

    def on_R3_x_at_rest(self):
        print("R3_x_at_rest")
        global joyX
        joyX = 0
    
    def on_R3_y_at_rest(self):
        print("R3_y_at_rest")
        global joyY
        joyY = 0

def translate(value):
    leftSpan = 32767 - -32767
    rightSpan = 1 - -1

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - -32767) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return -1 + (valueScaled * rightSpan)

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

        controller = MyController(interface="/dev/input/js0", connecting_using_ds4drv=False)
        #controller.listen()
        # Start controller thread
        threading.Thread(target=controller.listen, args=(), daemon=True).start()

    def robot_handler(self):
        time.sleep(3)
        #controller.listen()
        while True:
            #print(self.get_robot_dict_status())
            #print("Twist: {}".format(self.twist))
            self.twist.linear.x = translate(joyX)
            self.twist.linear.y = translate(joyY)
            #time.sleep(3)
            if self.twist is not None:  # ROS like twist object to angular direction and velocity
                #print("Twist: {}".format(self.twist))
                x = self.twist.linear.x
                y = self.twist.linear.y
                theta_rad = math.atan2(y, x)
                theta_deg = (theta_rad / math.pi * 180) - 90
                p = math.sqrt((0 - y) ** 2 + (0 - x) ** 2)  # Pythagorean theorem
                # print("Angle:{:04} - Speed:{:.2f}".format(int(theta_deg), p))


if __name__ == "__main__":
    print("simplepybotsdk version is", simplepybotsdk.__version__)
    robot = RobotExample()
    print("Poses {}".format(robot.poses))

    k = "ciao"
    while k != "stop":
        k = input("Type 'stop' to stop: ")
