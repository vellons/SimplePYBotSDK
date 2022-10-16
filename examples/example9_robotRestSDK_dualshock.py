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

class MyController(Controller):

    def __init__(self, robot, **kwargs):
        Controller.__init__(self, **kwargs)
        self.robot = robot
        self.joyX = 0
        self.joyY = 0
        print("Controller initialized")

    def connect():
        print("Connected")

    def disconnect():
        print("Disconnected")

    def on_L1_press(self):
        #print("L1 pressed")
        self.robot.l1IsPressed = True

    def on_L1_release(self):
        #print("L1 released")
        self.robot.l1IsPressed = False

    def on_R1_press(self):
        #print("R1 pressed")
        self.robot.r1IsPressed = True

    def on_R1_release(self):
        #print("R1 released")
        self.robot.r1IsPressed = False

    def on_L3_left(self, value):    
        #print("L3_left")
        self.joyX = value
        self.calc_pose()

    def on_L3_right(self, value):
        #print("L3_right")
        self.joyX = value
        self.calc_pose()

    def on_L3_up(self, value):
        #print("L3_up")
        self.joyY = value
        self.calc_pose()

    def on_L3_down(self, value):
        #print("L3_down")
        self.joyY = value
        self.calc_pose()

    def on_L3_x_at_rest(self):
        #print("L3_x_at_rest")
        self.joyX = 0
        self.calc_pose()
    
    def on_L3_y_at_rest(self):
        #print("L3_y_at_rest")
        self.joyY = 0
        self.calc_pose()

    def on_left_arrow_press(self):
        print("left_arrow")
        mot = self.robot.get_motor("spalla_pan")
        mot.set_goal_angle(mot.get_current_angle() - 5)

    def on_right_arrow_press(self):
        print("right_arrow")
        mot = self.robot.get_motor("spalla_pan")
        mot.set_goal_angle(mot.get_current_angle() + 5)

    def on_playstation_button_press(self):
        print("idle")
        self.robot.go_to_pose("idle", 3, blocking=False)

    def on_square_press(self):
        print("braccio_stabile_1")
        self.robot.go_to_pose("braccio_stabile_1", 3, blocking=False)

    def on_triangle_press(self):
        print("braccio_stabile_2")
        self.robot.go_to_pose("braccio_stabile_2", 3, blocking=False)

    def translate(self, value):
        leftSpan = 32767 - -32767
        rightSpan = 1 - -1

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - -32767) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return -1 + (valueScaled * rightSpan)

    def calc_pose(self):
        x = self.translate(self.joyX)
        y = -self.translate(self.joyY)
        self.robot.twist.linear.x = x
        self.robot.twist.linear.y = y
        return x, y

    def flagsChecker(self):
        while True:
            if self.robot.l1IsPressed and self.robot.r1IsPressed:
                self.robot.twist.angular.z = 0

            if self.robot.r1IsPressed:
                if self.robot.twist.angular.z >= 365:
                    self.robot.twist.angular.z = 0
                    
                self.robot.twist.angular.z += 5
            
            if self.robot.l1IsPressed:
                if self.robot.twist.angular.z <= 0:
                    self.robot.twist.angular.z = 365
                self.robot.twist.angular.z -= 5

            time.sleep(0.1)
        

class RobotExample(simplepybotsdk.RobotRESTSDK):
    def __init__(self):
        super().__init__(
            config_path="lambda_bot.json",
            socket_host="0.0.0.0",  # Use "0.0.0.0" for external connection,
            socket_port=65432,
            rest_host="0.0.0.0",  # Use "0.0.0.0" for external connection,
            rest_port=8000
        )
        self.controller = None
        self.rest_configure()
        self.rest_serve_forever()
        print("{} ready.".format(self.configuration["name"]))

        # Start robot handler thread
        threading.Thread(target=self.robot_handler, args=(), daemon=True).start()


        self.l1IsPressed = False
        self.r1IsPressed = False

        self.controller = MyController(interface="/dev/input/js0", connecting_using_ds4drv=False, robot=self)
        threading.Thread(target=self.controller.listen, args=(), daemon=True).start()

        threading.Thread(target=self.controller.flagsChecker, args=(), daemon=True).start()

    def robot_handler(self):
        time.sleep(3)
        while True:
            #print("Twist: {}".format(self.twist))
            if self.twist is not None:  # ROS like twist object to angular direction and velocity
                x = self.twist.linear.x
                y = self.twist.linear.y
                theta_rad = math.atan2(y, x)
                theta_deg = (theta_rad / math.pi * 180) - 90
                p = math.sqrt((0 - y) ** 2 + (0 - x) ** 2)  # Pythagorean theorem
                print("Angle:{:04} - Speed:{:.2f}".format(int(theta_deg), p))
                time.sleep(0.3)


if __name__ == "__main__":
    print("simplepybotsdk version is", simplepybotsdk.__version__)
    robot = RobotExample()

    k = "ciao"
    while k != "stop":
        k = input("Type 'stop' to stop: ")
