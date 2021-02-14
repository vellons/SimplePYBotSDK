import logging
import threading
import socket
from pyramid.config import Configurator
from pyramid.response import Response
from wsgiref.simple_server import make_server
from simplepybotsdk.robotSocketSDK import RobotSocketSDK as RobotSocketSDK

logger = logging.getLogger(__name__)


class RobotRESTSDK(RobotSocketSDK):
    """RobotSDK + RobotSocketSDK + REST robot's component control with Pyramid."""

    def __init__(self, config_path: str, socket_host: str, socket_port: int, ws_host: str, ws_port: int,
                 robot_speed: float = 1.0, motors_check_per_second: int = None, socket_send_per_second: int = None):
        """
        :param config_path: SimplePYBotSDK json configuration file path.
        :param socket_host: socket host to listen.
        :param socket_port: socket port to listen.
        :param robot_speed: robot speed. Use this to make robot move slower or faster. Default is 1.
        :param motors_check_per_second: numbers of motor's check per second. Set to 0 to disable dedicated thread.
        :param socket_send_per_second: numbers of dump send to the socket client in 1 second.
        """
        super().__init__(config_path, socket_host, socket_port, robot_speed, motors_check_per_second,
                         socket_send_per_second)
        logger.debug("RobotRESTSDK initialization")
        self._ws_host = ws_host
        self._ws_port = ws_port
        self._thread_ws = None
        self._server = None

    def ws_configure(self):
        """
        Method to configure web services routes and views
        """
        with Configurator() as config:
            config.add_route("ws_hello_world", "/")
            config.add_view(self._ws_hello_world, route_name="ws_hello_world")
            config.add_route("ws_robot_configuration", "/api/v1/robot/configuration/", request_method="GET")
            config.add_view(self._ws_robot_configuration, route_name="ws_robot_configuration")
            config.add_route("ws_robot_status", "/api/v1/robot/status/", request_method="GET")
            config.add_view(self._ws_robot_status, route_name="ws_robot_status")
            config.add_route("ws_robot_status_absolute", "/api/v1/robot/status/absolute/", request_method="GET")
            config.add_view(self._ws_robot_status_absolute, route_name="ws_robot_status_absolute")
            config.add_route("ws_robot_motors", "/api/v1/robot/motors/", request_method="GET")
            config.add_view(self._ws_robot_motors, route_name="ws_robot_motors")
            config.add_route("ws_robot_motor_detail_by_key", "/api/v1/robot/motors/{key}/", request_method="GET")
            config.add_view(self._ws_robot_motor_detail_by_key, route_name="ws_robot_motor_detail_by_key")
            config.add_route("ws_robot_motor_patch_by_key", "/api/v1/robot/motors/{key}/", request_method="PATCH")
            config.add_view(self._ws_robot_motor_patch_by_key, route_name="ws_robot_motor_patch_by_key")
        app = config.make_wsgi_app()
        self._server = make_server(self._ws_host, self._ws_port, app)

    def ws_serve_forever(self):
        """
        Method to start web services serve thread
        """
        self._thread_ws = threading.Thread(target=self._ws_thread_handler, args=())
        self._thread_ws.daemon = True
        self._thread_ws.start()

    def _ws_thread_handler(self):
        logger.debug("[ws_thread]: start serving on {}".format((self._ws_host, self._ws_port)))
        if self._ws_host == "0.0.0.0":
            print("[ws_thread]: start serving on:\n\t- http://127.0.0.1:{}/\n\t- http://{}:{}/".format(
                self._ws_port, socket.gethostbyname(socket.gethostname()), self._ws_port))
        else:
            print("[ws_thread]: start serving on: http://{}:{}/".format(self._ws_host, self._ws_port))
        self._server.serve_forever()

    def _ws_hello_world(self, root, request):
        detail = "Hello World! These are web services for robot name: '{}'".format(self.configuration["name"])
        return Response(json_body={"detail": detail})

    def _ws_robot_configuration(self, root, request):
        return Response(json_body=self.configuration)

    def _ws_robot_status(self, root, request):
        return Response(json_body=self.get_robot_dict_status())

    def _ws_robot_status_absolute(self, root, request):
        return Response(json_body=self.get_robot_dict_status(absolute=True))

    def _ws_robot_motors(self, root, request):
        motors = []
        for m in self.motors:
            motors.append(dict(m))
        return Response(json_body=motors)

    def _ws_robot_motor_detail_by_key(self, root, request):
        m = self.get_motor(request.matchdict["key"])
        if m is None:
            return Response(json_body={"detail": "Not found."}, status=404)
        return Response(json_body=dict(m))

    def _ws_robot_motor_patch_by_key(self, root, request):
        m = self.get_motor(request.matchdict["key"])
        if m is None:
            return Response(json_body={"detail": "Not found."}, status=404)
        try:
            m.set_goal_angle(int(request.json_body["goal_angle"]))
            return Response(json_body=dict(m))
        except Exception as e:
            logger.error("[ws_thread]: robot_motor_patch_by_key: {}".format(e))
            return Response(json_body={"detail": "Bad request. Use abs_goal_angle key"}, status=400)
