import logging
import threading
import json
import time
import socket
from select import select
import simplepybotsdk.configurations as configurations
from simplepybotsdk.robotSDK import RobotSDK as RobotSDK

logger = logging.getLogger(__name__)


class RobotSocketSDK(RobotSDK):
    """RobotSDK + Socket layer for read only current state of robot's component."""

    def __init__(self, config_path: str, socket_host: str, socket_port: int, robot_speed: float = 1.0,
                 motors_check_per_second: int = None, motors_point_to_point_check_per_second: int = None,
                 socket_send_per_second: int = None):
        """
        :param config_path: SimplePYBotSDK json configuration file path.
        :param socket_host: socket host to listen.
        :param socket_port: socket port to listen.
        :param robot_speed: robot speed. Use this to make robot move slower or faster. Default is 1.
        :param motors_check_per_second: numbers of motor's check per second. Set to 0 to disable dedicated thread.
        :param motors_point_to_point_check_per_second: numbers of motor's movement in a second during point to point.
        :param socket_send_per_second: numbers of dump send to the socket client in 1 second.
        """
        super().__init__(config_path, robot_speed, motors_check_per_second, motors_point_to_point_check_per_second)
        self._socket_host = socket_host
        self._socket_port = socket_port
        self._socket_send_per_second = socket_send_per_second
        self._socket_threaded_connection = []
        if self._socket_send_per_second is None:
            self._socket_send_per_second = configurations.SOCKET_SEND_PER_SECOND
        logger.debug("RobotSocketSDK initialization")

        self._thread_socket = threading.Thread(name="socket_thread", target=self._socket_thread_handler, args=())
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
        self._socket.listen(configurations.SOCKET_INCOMING_LIMIT - 1)
        print("[socket_thread]: listening for connections on {}".format((self._socket_host, self._socket_port)))

        while True:
            c, addr = self._socket.accept()
            thread = threading.Thread(target=self._socket_thread_connection_handler, args=(c, addr,))
            thread.name = "socket_thread_client_handler_{}".format(addr[1])
            thread.daemon = True
            thread.start()
            self._socket_threaded_connection.append(thread)

    def _socket_thread_connection_handler(self, conn, addr):
        """
        Dedicated thread to handle a single connection.
        This thread send to the client a JSON dump of current state of the robot.
        :param conn: socket connection instance.
        :param addr: tuple with ip and socket of the client connected.
        """
        thread_name = threading.current_thread().name
        try:
            logger.info("[{}]: got connection from: {}".format(thread_name, addr))
            last_time = time.time()
            absolute = False
            while True:
                if (time.time() - last_time) > (1 / self._socket_send_per_second):
                    last_time = time.time()
                    got_message, message = self._socket_connect_return_json_if_received(conn, addr)
                    if got_message:
                        if "socket" in message and "format" in message["socket"]:
                            f = message["socket"]["format"]
                            if f == "absolute":
                                logger.debug("[{}]: connection: {} now use format: {}".format(thread_name, addr, f))
                                absolute = True
                            if f == "relative":
                                logger.debug("[{}]: connection: {} now use format: {}".format(thread_name, addr, f))
                                absolute = False
                        self.socket_recv_callback(message, addr)
                    conn.send(json.dumps(self.get_robot_dict_status(absolute=absolute)).encode("utf-8"))
        except Exception as e:
            logger.info("[{}]: connection with {} closed. {}".format(thread_name, addr, e))
        finally:
            conn.close()

    @staticmethod
    def _socket_connect_return_json_if_received(conn, addr) -> (bool, dict):
        """
        Method to check if data is coming from the client. Only JSON data will be accepted and returned.
        :param conn: socket connection instance.
        :param addr: tuple with ip and socket of the client connected.
        """
        thread_name = threading.current_thread().name
        read_sockets, _, _ = select([conn], [], [], 0)
        for s in read_sockets:
            if s == conn:
                data = s.recv(8196).decode("utf-8")
                if len(data) > 0:
                    if data.startswith("GET"):
                        logger.debug("[{}]: got HTTP/GET from: {}".format(thread_name, addr))
                        return True, {}
                    logger.debug("[{}]: got message from: {}: {}".format(thread_name, addr, data))
                    try:
                        j = json.loads(data)
                        return True, j
                    except Exception as e:
                        logger.error("[{}]: fail to decode message from: {}: {}. {}".format(thread_name, addr, data, e))
                        print("[{}]: fail to decode message from: {}: {}. {}".format(thread_name, addr, data, e))
        return False, None

    def socket_recv_callback(self, message, addr):
        """
        Method called when a message is received. Override this to parse message.
        :param message: json message received.
        :param addr: tuple with ip and socket of the client that send the message.
        """
        pass
