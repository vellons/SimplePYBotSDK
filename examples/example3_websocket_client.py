import asyncio
import websockets

SOCKET_HOST = "localhost"
SOCKET_PORT = 65432
PATH = "/"
#PATH = "/absolute/"


async def hello():
    websocket = await websockets.connect("ws://" + SOCKET_HOST + ":" + str(SOCKET_PORT) + PATH)

    while True:
        message = await websocket.recv()
        print("{}".format(message))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(hello())
