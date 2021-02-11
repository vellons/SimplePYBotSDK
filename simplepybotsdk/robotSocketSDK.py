import logging
import threading
import json
import time
import socket
import simplepybotsdk.configurations as configurations
from simplepybotsdk.robotSDK import RobotSDK as RobotSDK

logger = logging.getLogger(__name__)


class RobotSocketSDK(RobotSDK):
    """RobotSDK + Socket layer for read only current state of robot's component."""

    def __init__(self, config_path: str, socket_host: str, socket_port: int, robot_speed: float = 1.0,
                 motors_check_per_second: int = None, socket_send_per_second: int = None):
        """
        :param config_path: SimplePYBotSDK json configuration file path.
        :param socket_host: socket host to listen.
        :param socket_port: socket port to listen.
        :param robot_speed: robot speed. Use this to make robot move slower or faster. Default is 1.
        :param motors_check_per_second: numbers of motor's check per second. Set to 0 to disable dedicated thread.
        :param socket_send_per_second: numbers of dump send to the socket client in 1 second.
        """
        super().__init__(config_path, robot_speed, motors_check_per_second)
        self._socket_host = socket_host
        self._socket_port = socket_port
        self._socket_send_per_second = socket_send_per_second
        self._threaded_connection = []
        if self._socket_send_per_second is None:
            self._socket_send_per_second = configurations.SOCKET_SEND_PER_SECOND
        logger.debug("RobotSocketSDK initialization")

        self._thread_socket = threading.Thread(target=self._socket_thread_handler, args=())
        self._thread_socket.daemon = True
        self._thread_socket.start()

    def _socket_thread_handler(self):
        """
        Thread method to accept incoming socket connections.
        This thread create a new thread for every single connection request.
        """
        logger.debug(
            "[socket_thread]: start listening for connections on {}".format((self._socket_host, self._socket_port)))
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((self._socket_host, self._socket_port))
        self._socket.listen(5)
        print("[socket_thread]: listening for connections on {}".format((self._socket_host, self._socket_port)))

        while True:
            c, addr = self._socket.accept()
            thread = threading.Thread(target=self._socket_thread_connection_handler, args=(c, addr,))
            thread.daemon = True
            thread.start()
            self._threaded_connection.append(thread)

    def _socket_thread_connection_handler(self, conn, addr):
        """
        Dedicated thread to handle a single connection.
        This thread send to the client a JSON dump of current state of the robot.
        :param conn: socket connection instance.
        :param addr: tuple with ip and socket of the client connected.
        """
        try:
            logger.info("[socket_thread]: got connection from: {}".format(addr))
            last_time = time.time()
            while True:
                if (time.time() - last_time) > (1 / self._socket_send_per_second):
                    last_time = time.time()
                    conn.send(json.dumps(self.get_robot_dict_status()).encode())
        except Exception as e:
            logger.info("[socket_thread]: connection with {} closed. {}".format(addr, e))
        finally:
            conn.close()
