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
                 robot_speed: float = 1.0, motors_check_per_second: int = None,
                 motors_point_to_point_check_per_second: int = None, socket_send_per_second: int = None):
        """
        :param config_path: SimplePYBotSDK json configuration file path.
        :param socket_host: socket host to listen.
        :param socket_port: socket port to listen.
        :param rest_host: web server host to listen.
        :param rest_port: web server port to listen.
        :param robot_speed: robot speed. Use this to make robot move slower or faster. Default is 1.
        :param motors_check_per_second: numbers of motor's check per second. Set to 0 to disable dedicated thread.
        :param motors_point_to_point_check_per_second: numbers of motor's movement in a second during point to point.
        :param socket_send_per_second: numbers of dump send to the socket client in 1 second.
        """
        super().__init__(config_path, socket_host, socket_port, robot_speed, motors_check_per_second,
                         motors_point_to_point_check_per_second, socket_send_per_second)
        logger.debug("RobotRESTSDK initialization")
        self.rest_base_url = "/api/v1/robot"
        self.rest_enable_cors = True
        self._rest_host = rest_host
        self._rest_port = rest_port
        self._thread_rest = None
        self._server = None
        self._dashboard_link = "https://vellons.github.io/SimplePYBotDashboard"

    def rest_configure(self):
        """
        Method to configure web services routes and views.
        """
        with Configurator() as config:
            config.add_route("hello_world", self.rest_base_url + "/")
            config.add_view(self._rest_hello_world, route_name="hello_world")
            config.add_route("rest_configuration", self.rest_base_url + "/configuration/", request_method="GET")
            config.add_view(self._rest_robot_configuration, route_name="rest_configuration")
            config.add_route("rest_status", self.rest_base_url + "/status/", request_method="GET")
            config.add_view(self._rest_robot_status, route_name="rest_status")
            config.add_route("rest_status_abs", self.rest_base_url + "/status/absolute/", request_method="GET")
            config.add_view(self._rest_robot_status_absolute, route_name="rest_status_abs")
            config.add_route("rest_sdk_info", self.rest_base_url + "/sdk/", request_method="GET")
            config.add_view(self._rest_robot_sdk_info, route_name="rest_sdk_info")
            config.add_route("rest_sdk_patch", self.rest_base_url + "/sdk/", request_method=["PATCH", "OPTIONS"])
            config.add_view(self._rest_robot_sdk_patch, route_name="rest_sdk_patch")
            config.add_route("rest_motors", self.rest_base_url + "/motors/", request_method="GET")
            config.add_view(self._rest_robot_motors, route_name="rest_motors")
            config.add_route("rest_motor_by_key", self.rest_base_url + "/motors/{key}/", request_method="GET")
            config.add_view(self._rest_robot_motor_detail_by_key, route_name="rest_motor_by_key")
            config.add_route("rest_motor_patch_by_key", self.rest_base_url + "/motors/{key}/",
                             request_method=["PATCH", "OPTIONS"])
            config.add_view(self._rest_robot_motor_patch_by_key, route_name="rest_motor_patch_by_key")
            config.add_route("rest_go_to_pose", self.rest_base_url + "/go-to-pose/{key}/",
                             request_method=["POST", "OPTIONS"])
            config.add_view(self._rest_robot_go_to_pose, route_name="rest_go_to_pose")
            config.add_route("rest_move_point_to_point", self.rest_base_url + "/move-point-to-point/",
                             request_method=["POST", "OPTIONS"])
            config.add_view(self._rest_robot_move_point_to_point, route_name="rest_move_point_to_point")
            config.add_route("rest_sensors", self.rest_base_url + "/sensors/", request_method="GET")
            config.add_view(self._rest_robot_sensors, route_name="rest_sensors")
            config.add_route("rest_sensors_by_key", self.rest_base_url + "/sensors/{key}/", request_method="GET")
            config.add_view(self._rest_robot_sensors_detail_by_key, route_name="rest_sensors_by_key")

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
        ip_addr = self._rest_host
        if self._rest_host == "0.0.0.0" and self.show_log_message:
            ip_addr = get_my_ip()
            print("[rest_thread]: start serving at:\n\t- Local:   http://localhost:{}{}/\n\t- Network: http://{}:{}{}/"
                  .format(self._rest_port, self.rest_base_url, ip_addr, self._rest_port, self.rest_base_url))
        elif self.show_log_message:
            print("[rest_thread]: start serving at: http://{}:{}{}/"
                  .format(ip_addr, self._rest_port, self.rest_base_url))
        if self.show_log_message:
            link = self._dashboard_link + "/?webserverurl=http://" + ip_addr + ":" + str(self._rest_port) + \
                   self.rest_base_url + "&websocketurl=ws://" + ip_addr + ":" + str(self._web_socket_port) + \
                   "&autoconnect=1"
            link += " Remember to 'Unblock mixed content' in browser"
            print("[rest_thread]: dashboard link: {}".format(link))
        self._server.serve_forever()

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
            speed = round(request.json_body["robot_speed"], 2)
            self.robot_speed = 0.05 if speed < 0.05 else speed
            logger.debug("set robot_speed to {}".format(self.robot_speed))
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

    def _rest_robot_go_to_pose(self, root, request):
        if request.method == "OPTIONS":
            return Response(json_body={})
        key = request.matchdict["key"]
        seconds = 0
        if request.body and "seconds" in request.json_body:
            seconds = request.json_body["seconds"]
            if type(seconds) is not int and type(seconds) is not float:
                seconds = 0
            seconds = 0 if seconds < 0.5 else seconds
        result = self.go_to_pose(key, seconds, seconds == 0)
        if result:
            return Response(json_body={"detail": "Going to pose {} in {} seconds".format(key, seconds)})
        return Response(
            json_body={"detail": "Something went wrong. See all available pose with /configuration/"}, status=400)

    def _rest_robot_move_point_to_point(self, root, request):
        if request.method == "OPTIONS":
            return Response(json_body={})
        try:
            seconds = 0
            pose = dict(request.json_body)
            if "seconds" in request.json_body:
                seconds = request.json_body["seconds"]
                del pose['seconds']
                if type(seconds) is not int and type(seconds) is not float:
                    seconds = 0
                seconds = 0 if seconds < 0.5 else seconds
            self.move_point_to_point(pose, seconds, seconds == 0)
            return Response(json_body={"detail": "Move point to point in {} seconds".format(seconds)})
        except Exception as e:
            logger.error("[rest_thread]: robot_move_point_to_point: {}".format(e))
            return Response(json_body={"detail": "Bad request. Use: {\"motor_key\": goal_angle}"}, status=400)

    def _rest_robot_sensors(self, root, request):
        sensors = []
        for s in self.sensors:
            sensors.append(dict(s))
        return Response(json_body=sensors)

    def _rest_robot_sensors_detail_by_key(self, root, request):
        s = self.get_sensor(request.matchdict["key"])
        if s is None:
            return Response(json_body={"detail": "Not found."}, status=404)
        return Response(json_body=dict(s))


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
