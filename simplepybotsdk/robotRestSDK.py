import logging
import threading
import json
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config
from wsgiref.simple_server import make_server
from simplepybotsdk.robotSocketSDK import RobotSocketSDK as RobotSocketSDK

logger = logging.getLogger(__name__)


class RobotRESTSDK(RobotSocketSDK):
    """RobotSDK + RobotSocketSDK + REST robot"s component control with Pyramid."""

    def __init__(self, config_path: str, socket_host: str, socket_port: int, ws_host: str, ws_port: int,
                 robot_speed: float = 1.0, motors_check_per_second: int = None, socket_send_per_second: int = None):
        """
        :param config_path: SimplePYBotSDK json configuration file path.
        :param socket_host: socket host to listen.
        :param socket_port: socket port to listen.
        :param robot_speed: robot speed. Use this to make robot move slower or faster. Default is 1.
        :param motors_check_per_second: numbers of motor"s check per second.
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
            config.add_route("hello_world", "/")
            config.add_view(self.hello_world, route_name="hello_world")
            config.add_route("robot_configuration", "/api/v1/robot/configuration/", request_method="GET")
            config.add_view(self.robot_configuration, route_name="robot_configuration")
            config.add_route("robot_status", "/api/v1/robot/status/", request_method="GET")
            config.add_view(self.robot_status, route_name="robot_status")
            config.add_route("robot_motors", "/api/v1/robot/motors/", request_method="GET")
            config.add_view(self.robot_motors, route_name="robot_motors")
            config.add_route("robot_motor_detail_by_key", "/api/v1/robot/motors/{key}/", request_method="GET")
            config.add_view(self.robot_motor_detail_by_key, route_name="robot_motor_detail_by_key")
            config.add_route("robot_motor_patch_by_key", "/api/v1/robot/motors/{key}/", request_method="PATCH")
            config.add_view(self.robot_motor_patch_by_key, route_name="robot_motor_patch_by_key")
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
        print("[ws_thread]: start serving on http://{}:{}/".format(self._ws_host, self._ws_port))
        self._server.serve_forever()

    def hello_world(self, root, request):
        detail = "Hello World! These are web services for robot name: '{}'".format(self.configuration["name"])
        return Response(json_body={"detail": detail})

    def robot_configuration(self, root, request):
        return Response(json_body=self.configuration)

    def robot_status(self, root, request):
        return Response(json_body=self.get_robot_dict_status())

    def robot_motors(self, root, request):
        motors = []
        for m in self.motors:
            motors.append(m.__dict__)
        return Response(json_body=motors)

    def robot_motor_detail_by_key(self, root, request):
        m = self.get_motor(request.matchdict["key"])
        if m is None:
            return Response(json_body={"detail": "Not found."}, status=404)
        return Response(json_body=m.__dict__)

    def robot_motor_patch_by_key(self, root, request):
        m = self.get_motor(request.matchdict["key"])
        if m is None:
            return Response(json_body={"detail": "Not found."}, status=404)
        try:
            m.set_goal_angle(int(request.json_body["abs_goal_angle"]))
            return Response(json_body=m.__dict__)
        except Exception as e:
            logger.error("[ws_thread]: robot_motor_patch_by_key: {}".format(e))
            return Response(json_body={"detail": "Bad request. Use abs_goal_angle key"}, status=400)
