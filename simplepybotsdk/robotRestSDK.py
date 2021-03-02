import logging
import threading
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.events import NewRequest
from wsgiref.simple_server import make_server
import simplepybotsdk.configurations as configurations
from simplepybotsdk.robotWebSocketSDK import RobotWebSocketSDK as RobotWebSocketSDK

logger = logging.getLogger(__name__)


class RobotRESTSDK(RobotWebSocketSDK):
    """RobotSDK + RobotWebSocketSDK + REST robot's component control with Pyramid."""

    def __init__(self, config_path: str, socket_host: str, socket_port: int, rest_host: str, rest_port: int,
                 robot_speed: float = 1.0, motors_check_per_second: int = None, socket_send_per_second: int = None):
        """
        :param config_path: SimplePYBotSDK json configuration file path.
        :param socket_host: socket host to listen.
        :param socket_port: socket port to listen.
        :param rest_host: web server host to listen.
        :param rest_port: web server port to listen.
        :param robot_speed: robot speed. Use this to make robot move slower or faster. Default is 1.
        :param motors_check_per_second: numbers of motor's check per second. Set to 0 to disable dedicated thread.
        :param socket_send_per_second: numbers of dump send to the socket client in 1 second.
        """
        super().__init__(config_path, socket_host, socket_port, robot_speed, motors_check_per_second,
                         socket_send_per_second)
        logger.debug("RobotRESTSDK initialization")
        self.rest_base_url = "/api/v1/robot"
        self.rest_enable_cors = True
        self._rest_host = rest_host
        self._rest_port = rest_port
        self._thread_rest = None
        self._server = None

    def rest_configure(self):
        """
        Method to configure web services routes and views.
        """
        with Configurator() as config:
            config.add_route("hello_world", self.rest_base_url + "/")
            config.add_view(self._rest_hello_world, route_name="hello_world")
            config.add_route("robot_configuration", self.rest_base_url + "/configuration/", request_method="GET")
            config.add_view(self._rest_robot_configuration, route_name="robot_configuration")
            config.add_route("robot_status", self.rest_base_url + "/status/", request_method="GET")
            config.add_view(self._rest_robot_status, route_name="robot_status")
            config.add_route("robot_status_abs", self.rest_base_url + "/status/absolute/", request_method="GET")
            config.add_view(self._rest_robot_status_absolute, route_name="robot_status_abs")
            config.add_route("robot_sdk_info", self.rest_base_url + "/sdk/", request_method="GET")
            config.add_view(self._rest_robot_sdk_info, route_name="robot_sdk_info")
            config.add_route("robot_sdk_patch", self.rest_base_url + "/sdk/", request_method=["PATCH", "OPTIONS"])
            config.add_view(self._rest_robot_sdk_patch, route_name="robot_sdk_patch")
            config.add_route("robot_motors", self.rest_base_url + "/motors/", request_method="GET")
            config.add_view(self._rest_robot_motors, route_name="robot_motors")
            config.add_route("robot_motor_by_key", self.rest_base_url + "/motors/{key}/", request_method="GET")
            config.add_view(self._rest_robot_motor_detail_by_key, route_name="robot_motor_by_key")
            config.add_route("robot_motor_patch_by_key", self.rest_base_url + "/motors/{key}/",
                             request_method=["PATCH", "OPTIONS"])
            config.add_view(self._rest_robot_motor_patch_by_key, route_name="robot_motor_patch_by_key")
            if self.rest_enable_cors:
                config.add_subscriber(add_cors_headers_response_callback, NewRequest)
        app = config.make_wsgi_app()
        self._server = make_server(self._rest_host, self._rest_port, app)

    def rest_serve_forever(self):
        """
        Method to start web services thread.
        """
        self._thread_rest = threading.Thread(name="rest_thread", target=self._rest_thread_handler, args=())
        self._thread_rest.daemon = True
        self._thread_rest.start()

    def _rest_thread_handler(self):
        logger.debug("[rest_thread]: start serving on {}".format((self._rest_host, self._rest_port)))
        if self._rest_host == "0.0.0.0":
            print("[rest_thread]: start serving at:\n\t- Local:   http://localhost:{}{}/\n\t- Network: http://{}:{}{}/"
                  .format(self._rest_port, self.rest_base_url, get_my_ip(), self._rest_port, self.rest_base_url))
        else:
            print("[rest_thread]: start serving at: http://{}:{}{}/"
                  .format(self._rest_host, self._rest_port, self.rest_base_url))
        self._server.serve_forever()

    def get_sdk_infos(self) -> dict:
        """
        :return: dict of sdk infos.
        """
        return {
            "robot_speed": self.robot_speed,
            "motors_check_per_second": self._motors_check_per_second,
            "robot_ip": get_my_ip(),
            "rest_base_url": self.rest_base_url,
            "rest_enable_cors": self.rest_enable_cors,
            "socket_port": self._web_socket_port,
            "socket_send_per_second": self._web_socket_send_per_second
        }

    def _rest_hello_world(self, root, request):
        detail = "Hello World! These are web services for robot name: '{}'".format(self.configuration["name"])
        return Response(json_body={"detail": detail})

    def _rest_robot_configuration(self, root, request):
        return Response(json_body=self.configuration)

    def _rest_robot_status(self, root, request):
        return Response(json_body=self.get_robot_dict_status())

    def _rest_robot_status_absolute(self, root, request):
        return Response(json_body=self.get_robot_dict_status(absolute=True))

    def _rest_robot_sdk_info(self, root, request):
        return Response(json_body=self.get_sdk_infos())

    def _rest_robot_sdk_patch(self, root, request):
        if request.method == "OPTIONS":
            return Response(json_body={})
        try:
            self.robot_speed = round(request.json_body["robot_speed"], 2)
            return Response(json_body=self.get_sdk_infos())
        except Exception as e:
            logger.error("[rest_thread]: robot_sdk_patch: {}".format(e))
            return Response(json_body={"detail": "Bad request. Use robot_speed field"}, status=400)

    def _rest_robot_motors(self, root, request):
        motors = []
        for m in self.motors:
            motors.append(dict(m))
        return Response(json_body=motors)

    def _rest_robot_motor_detail_by_key(self, root, request):
        m = self.get_motor(request.matchdict["key"])
        if m is None:
            return Response(json_body={"detail": "Not found."}, status=404)
        return Response(json_body=dict(m))

    def _rest_robot_motor_patch_by_key(self, root, request):
        if request.method == "OPTIONS":
            return Response(json_body={})
        m = self.get_motor(request.matchdict["key"])
        if m is None:
            return Response(json_body={"detail": "Not found."}, status=404)
        try:
            m.set_goal_angle(int(request.json_body["goal_angle"]))
            return Response(json_body=dict(m))
        except Exception as e:
            logger.error("[rest_thread]: robot_motor_patch_by_key: {}".format(e))
            return Response(json_body={"detail": "Bad request. Use goal_angle key"}, status=400)


def add_cors_headers_response_callback(event):
    def cors_headers(request, response):
        response.headers.update({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PATCH,OPTIONS",
            "Access-Control-Allow-Headers": "Origin, Content-Type, Accept",
            "Access-Control-Max-Age": "600",
            "SimplePYBotSDK": configurations.VERSION
        })

    event.request.add_response_callback(cors_headers)


def get_my_ip():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("1.1.1.1", 80))
        my_ip = s.getsockname()[0]
        s.close()
        return my_ip
    except:
        return "localhost"
