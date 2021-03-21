import asyncio
import websockets

SOCKET_HOST = "localhost"
SOCKET_PORT = 65432
PATH = "/"


async def hello():
    websocket = await websockets.connect("ws://" + SOCKET_HOST + ":" + str(SOCKET_PORT) + PATH)
    # await websocket.send('{"socket": {"format": "absolute"}}'.encode())
    # await websocket.send('{"socket": {"format": "block"}}'.encode())

    while True:
        message = await websocket.recv()
        print(message)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(hello())
