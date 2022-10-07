import logging
from SimpleWebSocketServer import WebSocket

import simplepybotsdk
from simplepybotsdk.parserJSON import ParserJSON

logging.basicConfig(level=logging.WARNING, filename='log.log', format='%(asctime)s %(levelname)s %(name)s: %(message)s')


class PingPongParser(ParserJSON):
    def parse(self, message: dict):
        # All json send to socket or websocket will be parsed by this class
        if "ping" in message:
            print("Ping received!")
            return {"pong": "ciao"}  # Use example3_websocket_client


class RobotExample(simplepybotsdk.RobotRESTSDK):
    def __init__(self):
        super().__init__(
            config_path="example_webots_khr2hv.json",
            socket_host="0.0.0.0",  # Use "0.0.0.0" for external connection,
            socket_port=65432,
            rest_host="0.0.0.0",  # Use "0.0.0.0" for external connection,
            rest_port=8000
        )
        self.message_parsers.append(PingPongParser)  # Add message parser
        self.rest_configure()
        self.rest_serve_forever()
        print("{} ready.".format(self.configuration["name"]))

    def web_socket_recv_callback(self, message: dict, addr: tuple, socket: WebSocket):
        """
        Method called when a message is received. Override this to parse message.
        :param message: json message received.
        :param addr: tuple with ip and socket of the client that send the message.
        :param socket: the socket connection.
        """
        print("Received message: {}".format(message))
        # socket.sendMessage('{"ciao": "hello"}'.encode())  # Better with custom parser


if __name__ == "__main__":
    print("simplepybotsdk version is", simplepybotsdk.__version__)
    robot = RobotExample()

    k = "ciao"
    while k != "stop":
        k = input("Type 'stop' to stop: ")
