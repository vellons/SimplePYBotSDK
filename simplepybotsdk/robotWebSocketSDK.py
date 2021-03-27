import logging
import threading
import json
import time
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import simplepybotsdk.configurations as configurations
from simplepybotsdk.robotSDK import RobotSDK as RobotSDK

logger = logging.getLogger(__name__)
robot_instance = None


class RobotWebSocketSDK(RobotSDK):
    """RobotSDK + WebSocket layer for read only current state of robot's component."""

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
        self._web_socket_host = socket_host
        self._web_socket_port = socket_port
        self._web_socket_send_per_second = socket_send_per_second
        self.web_socket_threaded_connection = set()
        if self._web_socket_send_per_second is None:
            self._web_socket_send_per_second = configurations.WEB_SOCKET_SEND_PER_SECOND

        if self._web_socket_send_per_second <= 0:
            logger.debug("RobotWebSocketSDK disabled")
            return
        logger.debug("RobotWebSocketSDK initialization")

        self._thread_web_socket_send_data = None
        self._thread_web_socket = threading.Thread(target=self._web_socket_thread_handler, args=())
        self._thread_web_socket.name = "websocket_thread"
        self._thread_web_socket.daemon = True
        self._thread_web_socket.start()

    def _web_socket_thread_handler(self):
        """
        Thread method used to start WebSocket server in a dedicated thread.
        """
        logger.debug("[websocket_thread]: start listening for connections on {}"
                     .format((self._web_socket_host, self._web_socket_port)))
        global robot_instance
        robot_instance = self
        server = SimpleWebSocketServer(self._web_socket_host, self._web_socket_port, self.SimpleConnectionHandler)
        if self.show_log_message:
            print("[websocket_thread]: listening for connections on {}"
                  .format((self._web_socket_host, self._web_socket_port)))
        server.serveforever()

    def start_web_socket_send_data(self):
        """
        This method create a new thread when the first client connects.
        """
        if self._thread_web_socket_send_data is None:
            logger.info("[websocket_thread]: start_web_socket_send_data thread starting")
            self._thread_web_socket_send_data = threading.Thread(target=self._web_socket_send_data_handler, args=())
            self._thread_web_socket_send_data.name = "websocket_thread"
            self._thread_web_socket_send_data.daemon = True
            self._thread_web_socket_send_data.start()

    def _web_socket_send_data_handler(self):
        """
        Thread dedicated of sending realtime date to client, in the correct format.
        This thread send to the client a JSON dump of current state of the robot.
        """
        last_time = 0
        j_relative = None
        j_absolute = None
        if self._web_socket_send_per_second <= 0:
            self._thread_web_socket_send_data = None
            return
        try:
            while len(self.web_socket_threaded_connection) > 0:
                if (time.time() - last_time) > (1 / self._web_socket_send_per_second):
                    last_time = time.time()
                    for client in self.web_socket_threaded_connection:
                        if client.message_format == "relative":
                            if j_relative is None:
                                j_relative = json.dumps(self.get_robot_dict_status(absolute=False)).encode("utf-8")
                            client.sendMessage(j_relative)
                        elif client.message_format == "absolute":
                            if j_absolute is None:
                                j_absolute = json.dumps(self.get_robot_dict_status(absolute=True)).encode("utf-8")
                            client.sendMessage(j_absolute)
                    j_relative = None
                    j_absolute = None
                    time.sleep(self.sleep_avoid_cpu_waste / self._web_socket_send_per_second)  # Avoid wasting CPU time
            logger.info("[websocket_thread_send_data]: stopped due to inactivity")
            self._thread_web_socket_send_data = None
        except Exception as e:
            logger.error("[websocket_thread_send_data]: _web_socket_send_data_handler crashed: {}".format(e))
            self._thread_web_socket_send_data = None

    def web_socket_handle_incoming_message(self, socket, message, addr):
        """
        Method to decode the data coming from the client. Only JSON data will be accepted.
        :param socket: socket connection instance.
        :param message: the message to decode.
        :param addr: tuple with ip and socket of the client connected.
        """
        if type(message) == bytearray:
            data = message.decode("utf-8")
        elif type(message) == str:
            data = message
        else:
            logger.error("[websocket_thread]: fail understand message from: {}: {}".format(addr, message))
            return
        if len(data) > 0:
            logger.debug("[websocket_thread]: got message from: {}: {}".format(addr, data))
            try:
                j = json.loads(data)
                if "socket" in j and "format" in j["socket"]:
                    f = j["socket"]["format"]
                    logger.debug("[websocket_thread]: connection: {} now use format: {}".format(addr, f))
                    socket.message_format = f
                self.web_socket_recv_callback(j, addr)
            except Exception as e:
                logger.error("[websocket_thread]: fail to decode message from: {}: {}. {}".format(addr, data, e))
                if self.show_log_message:
                    print("[websocket_thread]: fail to decode message from: {}: {}. {}".format(addr, data, e))

    def web_socket_recv_callback(self, message: dict, addr: tuple):
        """
        Method called when a message is received. Override this to parse message.
        :param message: json message received.
        :param addr: tuple with ip and socket of the client that send the message.
        """
        pass

    class SimpleConnectionHandler(WebSocket):
        """A simple class to handle websocket communication."""

        def __init__(self, server, sock, address):
            super().__init__(server, sock, address)
            global robot_instance
            self.robot = robot_instance
            self.message_format = "relative"
            if self.robot is None:
                logger.error("[websocket_thread]: SimpleConnectionHandler: robot instance is None")

        def handleMessage(self):
            self.robot.web_socket_handle_incoming_message(self, self.data, self.address)

        def handleConnected(self):
            if len(self.robot.web_socket_threaded_connection) >= configurations.SOCKET_INCOMING_LIMIT:
                logger.warning("[websocket_thread]: connection refused to {}".format(self.address))
                if self.robot.show_log_message:
                    print("[websocket_thread]: connection refused to {}".format(self.address))
                self.handleClose()
                return
            logger.info("[websocket_thread]: got connection from: {}".format(self.address))
            if self.robot.show_log_message:
                print("[websocket_thread]: got connection from {}".format(self.address))
            self.robot.web_socket_threaded_connection.add(self)
            self.robot.start_web_socket_send_data()

        def handleClose(self):
            logger.info("[websocket_thread]: connection closed with {}".format(self.address))
            if self.robot.show_log_message:
                print("[websocket_thread]: connection closed with {}".format(self.address))
            self.robot.web_socket_threaded_connection.remove(self)
