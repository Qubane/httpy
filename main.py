"""
The mighty silly webserver written in python for no good reason
"""


import ssl
import gzip
import socket
import brotli
import signal
import asyncio
import aiofiles
from src import APIv1
from src.socks import *
from src.request import Request
from src.minimizer import minimize_html


# path mapping
PATH_MAP = {
    "/":
        {"path": "www/index.html",
         "compress": True},
    "/index.html":
        {"path": "www/index.html",
         "compress": True},
    "/robots.txt":
        {"path": "www/robots.txt",
         "compress": False},
    "/favicon.ico":
        {"path": "www/favicon.ico",
         "compress": False},
    "/css/styles.css":
        {"path": "css/styles.css",
         "compress": True},
    "/about":
        {"path": "www/about.html",
         "compress": True},
    "/test":
        {"path": "www/test.html",
         "compress": True},
}

# API
API_VERSIONS = {
    "APIv1"
}

# internal path map
I_PATH_MAP = {
    "/err/response.html":       {"path": "www/err/response.html"}
}


def get_response_code(code: int) -> bytes:
    match code:
        case 200:
            return b'200 OK'
        case 400:
            return b'400 Bad Request'
        case 401:
            return b'401 Unauthorized'
        case 403:
            return b'403 Forbidden'
        case 404:
            return b'404 Not Found'
        case 6969:
            return b'6969 UwU'
        case _:  # in any other case return bad request response
            return get_response_code(400)


class HTTPServer:
    """
    The mighty HTTP server
    """

    def __init__(self, *, port: int, packet_size: int = 2048):
        # ssl context
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(
            certfile=r"C:\Certbot\live\qubane.ddns.net\fullchain.pem",      # use your own path here
            keyfile=r"C:\Certbot\live\qubane.ddns.net\privkey.pem"          # here too
        )
        self.context.check_hostname = False

        # sockets
        self.socket: ssl.SSLSocket = self.context.wrap_socket(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_side=True)
        self.packet_size: int = packet_size
        self.bind_port: int = port

        # list of connected clients
        self.clients: list[socket.socket] = []

    def interrupt(self, *args, **kwargs):
        """
        Interrupts the web server
        """

        self.socket.close()

    def start(self):
        """
        Method to start the web server
        """

        # setup signaling
        signal.signal(signal.SIGINT, self.interrupt)

        # bind and start listening to port
        self.socket.bind(('', self.bind_port))
        self.socket.listen()
        self.socket.setblocking(False)

        # start listening
        asyncio.run(self._listen_thread())

    async def _listen_thread(self):
        """
        Listening for new connections
        """

        # get event loop
        loop = asyncio.get_event_loop()

        # start listening
        while True:
            # try to accept new connection
            try:
                client = (await ssl_sock_accept(self.socket))[0]

            # if socket was closed -> break
            except OSError as e:
                print(e)
                print("Closed.")
                break

            # else append to client list and create new task
            self.clients.append(client)
            await loop.create_task(self.client_handle(client))

    async def client_handle(self, client: ssl.SSLSocket):
        """
        Handles client's connection
        """

        loop = asyncio.get_event_loop()

        while True:
            # receive request from client
            raw_request = await self._recvall(client)

            # decode request
            request: Request = Request.create(raw_request)

            # # log request
            # async with aiofiles.open("logs.log", "a") as f:
            #     await f.write(f"IP: {client.getpeername()[0]}\n{request}\n\n")

            # handle requests
            try:
                match request.type:
                    case "GET":
                        await self.handle_get_request(client, request)
                    case _:
                        break

            # break on exception
            except Exception as e:
                print(e)
                break

            # break the connection
            break

        # close connection (stop page loading)
        self._close_client(client)

    @staticmethod
    async def handle_get_request(client: ssl.SSLSocket, request: Request):
        """
        Handles user's GET request
        """

        # get available compression methods
        compressions = [x.strip() for x in getattr(request, "Accept-Encoding", "").split(",")]

        # check if request path is in the PATH_MAP
        if request.path in PATH_MAP:
            # if it is -> return file from that path
            async with aiofiles.open(PATH_MAP[request.path]["path"], "rb") as f:
                data = await f.read()

            # pre-compress data for HTML files
            if PATH_MAP[request.path]["path"][-4:] == "html":
                data = minimize_html(data)

            # add brotli compression header (if supported)
            headers = {}
            if "br" in compressions:
                headers["Content-Encoding"] = "br"

            # else add gzip compression (if supported)
            elif "gzip" in compressions:
                headers["Content-Encoding"] = "gzip"

            # send 200 response with the file to the client
            await HTTPServer._send(client, 200, data, headers)

            # return after answer
            return

        # if it's an API request
        elif (api_version := request.path.split("/")[1]) in API_VERSIONS:
            data = b''
            headers = {}
            match api_version:
                case "APIv1":
                    status, data, headers = await APIv1.respond(client, request)
                case _:
                    status = 400

            # if status is not 200 -> send bad response
            if status != 200:
                await HTTPServer._bad_response(client, status)
                return

            # send data if no error
            await HTTPServer._send(client, status, data, headers)

            # return after answer
            return

        # in case of error, return error page
        await HTTPServer._bad_response(client, 404)

    @staticmethod
    async def _bad_response(client: ssl.SSLSocket, status_code: int):
        """
        Sends a bad response page to the client.
        :param client: client
        :param status_code: status code
        """

        async with aiofiles.open(I_PATH_MAP["/err/response.html"]["path"], "r") as f:
            data = await f.read()

        # format error response
        data = data.format(status_code=get_response_code(status_code).decode("ascii"))

        # send response to the client
        await HTTPServer._send(client, status_code, data.encode("ascii"))

    @staticmethod
    async def _send(client: ssl.SSLSocket, response: int, data: bytes = None, headers: dict[str, str] = None):
        """
        Sends client response code + headers + data
        :param client: client
        :param response: response code
        :param data: data
        :param headers: headers to include
        """

        # if data was not given
        if data is None:
            data = bytes()

        # if headers were not given
        if headers is None:
            headers = dict()

        # check for 'content-encoding' header
        if headers.get("Content-Encoding") == "br":
            data = brotli.compress(data)

        elif headers.get("Content-Encoding") == "gzip":
            data = gzip.compress(data)

        # format headers
        byte_header = bytearray()
        for key, value in headers.items():
            byte_header += f"{key}: {value}\r\n".encode("ascii")

        # send response to the client
        await asyncio.get_event_loop().create_task(ssl_sock_sendall(
            client,
            b'HTTP/1.1 ' +
            get_response_code(response) +
            b'\r\n' +
            byte_header +  # if empty, we'll just get b'\r\n\r\n'
            b'\r\n' +
            data
        ))

        # # send response to the client
        # await ssl_sock_sendall(
        #     client,
        #     b'HTTP/1.1 ' +
        #     get_response_code(response) +
        #     b'\r\n' +
        #     byte_header +  # if empty, we'll just get b'\r\n\r\n'
        #     b'\r\n' +
        #     data
        # )

    def _close_client(self, client: socket.socket):
        """
        Closes a client
        """

        client.close()
        if client in self.clients:
            self.clients.remove(client)

    async def _recvall(self, client: ssl.SSLSocket) -> bytes:
        """
        Receive All (just receives the whole message, instead of 1 packet at a time)
        """

        # create message buffer
        buffer: bytearray = bytearray()

        # start fetching the message
        while True:
            try:
                # fetch packet
                message = await ssl_sock_recv(client, self.packet_size)
            except OSError:
                break

            # that happens when user stops loading the page
            if message == b'':
                break

            # append fetched message to the buffer
            buffer += message

            # check for EoF
            if buffer[-4:] == b'\r\n\r\n':
                # return the received message
                return buffer

        # return empty buffer on error
        return b''


def main():
    server = HTTPServer(port=13700)
    server.start()


if __name__ == '__main__':
    main()
