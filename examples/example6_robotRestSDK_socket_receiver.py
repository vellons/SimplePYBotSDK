import logging
import simplepybotsdk

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

    def web_socket_recv_callback(self, message: dict, addr: tuple):  # Override
        message = dict(message)
        if "ptp" in message:
            ptp = eval(message["ptp"])
            self.counter = (self.counter + 1) % 3
            if len(ptp) > 0 and self.counter == 0:
                self.move_point_to_point(ptp, 0)
                print(ptp)
                return


if __name__ == "__main__":
    print("simplepybotsdk version is", simplepybotsdk.__version__)
    robot = RobotSocketPointToPoint()

    print("Waiting for commands...")

    k = "ciao"
    while k != "stop":
        k = input("Type 'stop' to stop: ")
