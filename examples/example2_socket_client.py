import socket
import json

SOCKET_HOST = "localhost"
SOCKET_PORT = 65432

if __name__ == "__main__":
    """Client program for socket communication"""
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.connect((SOCKET_HOST, SOCKET_PORT))

    while True:
        data = socket.recv(8192).decode("utf-8")
        data = json.loads(data)
        print(data)
