import logging
import simplepybotsdk
from time import sleep

logging.basicConfig(level=logging.WARNING, filename='log.log', format='%(asctime)s %(levelname)s %(name)s: %(message)s')

SOCKET_HOST = "localhost"  # Use "0.0.0.0" for external connection
SOCKET_PORT = 65432
REST_HOST = "localhost"  # Use "0.0.0.0" for external connection
REST_PORT = 8000


class RobotSocketPointToPoint(simplepybotsdk.RobotRESTSDK):
    def __init__(self):
        super().__init__(
            config_path="example_webots_khr2hv.json",
            socket_host=SOCKET_HOST,
            socket_port=SOCKET_PORT,
            rest_host=REST_HOST,
            rest_port=REST_PORT,
            robot_speed=1
        )
        self.rest_configure()
        self.rest_serve_forever()
        print("{} ready.".format(self.configuration["name"]))
        self.counter = 0
        self.is_recording = False
        self.is_play_animation = False
        self.animation = []

    def web_socket_recv_callback(self, message: dict, addr: tuple):  # Override
        if self.is_play_animation:
            return
        message = dict(message)
        if "ptp" in message:
            ptp = eval(message["ptp"])
            self.counter += 1
            if len(ptp) > 0 and self.counter % 3 == 0:  # Handle only some message
                self.move_point_to_point(ptp, 0)
            if len(ptp) > 0 and self.counter % 10 == 0:  # Print only some message
                print("REC " + str(ptp) if self.is_recording else str(ptp))

    def start_recording(self):
        if self.is_recording:
            return
        self.is_recording = True
        self.point_to_point_start_recording()
        print("Start recording")

    def stop_recording(self):
        self.is_recording = False
        self.animation = robot.point_to_point_stop_recording()
        print("Stop recording: {}".format(len(self.animation)))

    def play_last_recorder(self):
        if self.is_recording:
            return
        self.is_play_animation = True
        print("Start play recorded animation of length: {}".format(len(self.animation)))
        if len(self.animation) > 0:
            print("Animation duration: {} seconds".format(self.animation[-1][2]))
        self.point_to_point_play_recorded(self.animation)
        print("Stop play recorded animation")
        self.is_play_animation = False


if __name__ == "__main__":
    print("simplepybotsdk version is", simplepybotsdk.__version__)
    robot = RobotSocketPointToPoint()

    sleep(3)
    k = "ciao"
    while k != "stop":
        commands = "Commands:\n" \
                   " - 'stop' to stop the program\n" \
                   " - 'r' to record point to point\n" \
                   " - 's' to stop recording\n" \
                   " - 'p' to play last animation\n"
        print(commands)
        k = input("> ")
        if k in ['r', 'R']:
            robot.start_recording()
        elif k in ['s', 'S']:
            robot.stop_recording()
        elif k in ['p', 'P']:
            robot.play_last_recorder()
