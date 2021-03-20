import logging
import threading
import json
import time
import asyncio
import websockets
import simplepybotsdk.configurations as configurations
from simplepybotsdk.robotSDK import RobotSDK as RobotSDK

logger = logging.getLogger(__name__)


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
        self._web_socket_threaded_connection = set()
        if self._web_socket_send_per_second is None:
            self._web_socket_send_per_second = configurations.WEB_SOCKET_SEND_PER_SECOND
        logger.debug("RobotWebSocketSDK initialization")

        self._web_socket_asyncio_loop = asyncio.get_event_loop()
        self._web_socket_server = websockets.serve(
            self._web_socket_incoming_handler, self._web_socket_host, self._web_socket_port
        )

        self._thread_web_socket = threading.Thread(target=self._web_socket_thread_handler, args=())
        self._thread_web_socket.daemon = True
        self._thread_web_socket.start()

        # self._thread_web_socket_sender = threading.Thread(target=self._web_socket_thread_sender, args=())
        # self._thread_web_socket_sender.daemon = True
        # self._thread_web_socket_sender.start()
        logger.debug("RobotWebSocketSDK threads started")

    def _web_socket_thread_handler(self):
        """
        Thread method used to start WebSocket server in a dedicated thread.
        """
        logger.debug("[websocket_thread]: start listening for connections on {}"
                     .format((self._web_socket_host, self._web_socket_port)))
        if self.show_startup_message:
            print("[websocket_thread]: listening for connections on {}"
                  .format((self._web_socket_host, self._web_socket_port)))

        self._web_socket_asyncio_loop.run_until_complete(self._web_socket_server)
        self._web_socket_asyncio_loop.run_forever()

    async def _web_socket_incoming_handler(self, websocket, path):
        """
        This method take incoming WebSocket connection and add to the list until end of connection.
        """
        ip = websocket.remote_address[0]
        if len(self._web_socket_threaded_connection) < configurations.SOCKET_INCOMING_LIMIT:
            logger.info("[websocket_thread]: got connection from: {} with path: {}".format(ip, path))
            self._web_socket_threaded_connection.add(websocket)

            thread = threading.Thread(target=self._web_socket_client_sender, args=(websocket, path))
            thread.daemon = True
            thread.start()
            try:
                await websocket.recv()
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                logger.info("[websocket_thread]: connection with {} closed.".format(ip))
                self._web_socket_threaded_connection.remove(websocket)
        else:
            logger.info("[websocket_thread]: connection refused from: {} with path: {}".format(ip, path))

    def _web_socket_client_sender(self, websocket, path):
        """
        Thread method used to send infos to active WebSocket connection
        """
        last_time = time.time()
        try:
            while True:
                if (time.time() - last_time) > (1 / self._web_socket_send_per_second):
                    last_time = time.time()
                    if path == "/absolute/":
                        c = websocket.send(json.dumps(self.get_robot_dict_status(absolute=True)).encode("utf-8"))
                    else:
                        c = websocket.send(json.dumps(self.get_robot_dict_status(absolute=False)).encode("utf-8"))
                    asyncio.run_coroutine_threadsafe(c, self._web_socket_asyncio_loop)
        except Exception as e:
            ip = websocket.remote_address[0]
            logger.info("[websocket_thread]: connection with {} closed with error. {}".format(ip, e))

    # def _web_socket_thread_sender(self):
    #     """
    #     Thread method used to send infos to active WebSocket connection
    #     """
    #     last_time = time.time()
    #     while True:
    #         if (time.time() - last_time) > (1 / self._web_socket_send_per_second):
    #             last_time = time.time()
    #             print("Checking", len(self._web_socket_threaded_connection))
    #             for websocket in self._web_socket_threaded_connection.copy():
    #                 try:
    #                     c = websocket.send(json.dumps(self.get_robot_dict_status(absolute=True)).encode("utf-8"))
    #                     asyncio.run_coroutine_threadsafe(c, self._web_socket_asyncio_loop)
    #                 except Exception as e:
    #                     ip = websocket.remote_address[0]
    #                     logger.info("[websocket_thread]: connection with {} closed with error. {}".format(ip, e))
    #                     self._web_socket_threaded_connection.remove(websocket)

    # def web_socket_recv_callback(self, message, addr):
    #     """
    #     Method called when a message is received. Override this to parse message.
    #     :param message: json message received.
    #     :param addr: tuple with ip and socket of the client that send the message.
    #     """
    #     pass
