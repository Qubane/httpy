"""
The mighty silly webserver written in python for no good reason
"""


import time
import json
import gzip
import socket
import asyncio
import htmlmin
import aiofiles
import threading


# some constants
PACKET_SIZE = 2048
PORT = 13700            # using random port cuz why not


# response status codes
RESPONSE = {
    200: b'OK',
    400: b'Bad Request',
    401: b'Unauthorized',
    403: b'Forbidden',
    404: b'Not Found',
    6969: b'UwU'
}


def get_response(code: int) -> bytes:
    return str(code).encode("ascii") + RESPONSE.get(code, b':(')


def is_alive(sock: socket.socket) -> bool:
    """
    Checks if the socket is still alive
    :param sock: socket
    :return: boolean (true if socket is alive, false otherwise)
    """
    return getattr(sock, '_closed', False)


def decode_request(req: str) -> dict[str, str | list | None]:
    # request dictionary
    request = dict()

    # request type and path
    request["type"] = req[:6].split(" ")[0]
    request["path"] = req[len(request["type"]) + 1:req.find("\r\n")].split(" ")[0]

    # decode other headers
    for line in req.split("\r\n")[1:]:
        if len(split := line.split(":")) == 2:
            key, value = split
            value = value.lstrip(" ")

            # write key value pair
            request[key] = value

    return request


class HTMLServer:
    """
    The very cool webserver
    """

    def __init__(self):
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: list[socket.socket] = []

        # list of allowed paths
        self.allowed_paths: dict[str, dict] = {
            "/":                {"path": "www/index.html",      "encoding": "css/html"},
            "/robots.txt":      {"path": "www/robots.txt",      "encoding": "text"},
            "/favicon.ico":     {"path": "www/favicon.ico",     "encoding": "bin"},
            "/css/styles.css":  {"path": None,                  "encoding": "css/html"},
        }

    def run(self):
        """
        Function that starts the webserver
        """

        # bind the server to port and start listening
        self.sock.bind(('', PORT))
        self.sock.listen()

        # start running thread
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

        # keep alive
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.sock.close()
            print("Closed.")

    def _run(self):
        """
        Run function for threads
        :return:
        """

        asyncio.run(self.server_listener())

    async def server_listener(self):
        """
        Listens for new connections, and handles them
        """

        while True:
            client, address = self.sock.accept()
            self.clients.append(client)
            await self.server_handle(client)

    async def server_handle(self, client: socket.socket):
        """
        Handles the actual connections (clients)
        :param client: connection socket
        """

        # message buffer
        buffer = bytearray()
        while True:
            # try to fetch a message
            # die otherwise
            try:
                message = client.recv(PACKET_SIZE)
            except OSError:
                break
            if message == b'':
                break

            # append packet to buffer
            buffer += message

            # check EoF (2 blank lines)
            if buffer[-4:] == b'\r\n\r\n':
                # text buffer
                text_buffer = buffer.decode("ascii")

                # decode request
                request = decode_request(text_buffer)

                print(f"[{request['type']}] Request from client '{client.getpeername()[0]}'")

                # log that request
                async with aiofiles.open("logs.log", "a") as f:
                    await f.write(
                        json.dumps(
                            {
                                "client": client.getpeername()[0],
                                "request": request
                            },
                            indent=2
                        ) + "\n"
                    )

                # handle the request
                if request["type"] == "GET":
                    await self.handle_get_request(client, request)
                else:
                    await self.handle_other_request(client)

                # clear buffer
                buffer.clear()
        client.close()
        self.clients.remove(client)

    async def handle_get_request(self, client: socket.socket, req: dict[str, str | None]):
        # if it's yandex
        if req.get("from") == "support@search.yandex.ru":
            response = get_response(404)
            data = b'Nothing...'

        # check UwU path
        elif req["path"] == "/UwU" or req["path"] == "/U/w/U":
            response = get_response(6969)
            data = b'<h1>' + b'UwU ' * 2000 + b'</h1>'

        # otherwise check access
        elif req["path"] in self.allowed_paths:
            # get path
            path = self.allowed_paths[req["path"]]["path"]

            # if path is None, return generic filepath
            if path is None:
                path = req["path"][1:]

            # check encoding
            if self.allowed_paths[req["path"]]["encoding"] == "css/html":
                # return text data
                async with aiofiles.open(path, "r") as f:
                    data = htmlmin.minify(await f.read()).encode("ascii")
            else:
                # return binary / text data
                async with aiofiles.open(path, "rb") as f:
                    data = await f.read()
            response = get_response(200)

        # in any other case
        else:
            response = get_response(403)
            data = b'Idk what you are trying to do here :/'

        # make headers
        headers = {}

        # check if compression is supported
        if req.get("Accept-Encoding"):
            encoding_list = [enc.lstrip(" ") for enc in req["Accept-Encoding"].split(",")]

            # check for gzip, and add to headers if present
            if "gzip" in encoding_list:
                headers["Content-Encoding"] = "gzip"

        # send response
        await self.send(client, response, data, headers)
        client.close()

    async def handle_other_request(self, client: socket.socket):
        # just say 'no'
        await self.send(client, get_response(403), b'No. Don\'t do that, that\'s cringe')
        client.close()

    async def send(self, client: socket.socket, response: bytes, data: bytes, headers: dict[str, str] | None = None):
        # construct headers
        formatted_headers = b''
        if headers is not None:
            formatted_headers = "".join([f"{key}: {val}\r\n" for key, val in headers.items()]).encode("ascii")

            # check for compression
            if headers.get("Content-Encoding") == "gzip":
                # compress data
                data = gzip.compress(data)

        # construct message
        if formatted_headers == b'':
            message = b'HTTP/1.1 ' + response + b'\r\n\r\n' + data
        else:
            message = b'HTTP/1.1 ' + response + b'\r\n' + formatted_headers + b'\r\n' + data

        # send message to client
        client.sendall(message)


def main():
    server = HTMLServer()
    server.run()


if __name__ == '__main__':
    main()
