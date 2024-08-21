"""
The mighty silly webserver written in python for no good reason
"""


import ssl
import gzip
import time
import socket
import signal
import asyncio
import aiofiles
from src.request import Request


# path mapping
PATH_MAP = {
    "/":                        {"path": "www/index.html"},
    "/index.html":              {"path": "www/index.html"},
    "/robots.txt":              {"path": "www/robots.txt"},
    "/favicon.ico":             {"path": "www/favicon.ico"},
    "/css/styles.css":          {"path": "css/styles.css"},
    "/about":                   {"path": "www/about.html"},
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
                client = (await self._accept(self.socket))[0]

            # if socket was closed -> break
            except OSError:
                print("Closed.")
                break

            # else append to client list and create new task
            self.clients.append(client)
            await loop.create_task(self.client_handle(client))

    async def client_handle(self, client: ssl.SSLSocket):
        """
        Handles client's connection
        """

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
        :param client: client
        :param request: client's request
        """

        # get available compression methods
        compressions = [x.strip() for x in getattr(request, "Accept-Encoding", "").split(",")]

        # check if request path is in the PATH_MAP
        if request.path in PATH_MAP:
            # if it is -> return file from that path
            async with aiofiles.open(PATH_MAP[request.path]["path"], "rb") as f:
                data = await f.read()

            # add gzip compression header (if supported)
            headers = {}
            if "gzip" in compressions:
                headers["Content-Encoding"] = "gzip"

            # send 200 response with the file to the client
            await HTTPServer._send(client, 200, data, headers)
        else:
            # in case of error, return error page
            async with aiofiles.open(I_PATH_MAP["/err/response.html"]["path"], "r") as f:
                data = await f.read()

            # status code
            status_code = 404

            # format error response
            data = data.format(status_code=get_response_code(status_code).decode("ascii"))

            # send 404 response to the client
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
        if headers.get("Content-Encoding") == "gzip":
            # if present -> compress data
            data = gzip.compress(data)

        # format headers
        byte_header = bytearray()
        for key, value in headers.items():
            byte_header += f"{key}: {value}\r\n".encode("ascii")

        # send response to the client
        await HTTPServer._sendall(
            client,
            b'HTTP/1.1 ' +
            get_response_code(response) +
            b'\r\n' +
            byte_header +  # if empty, we'll just get b'\r\n\r\n'
            b'\r\n' +
            data
        )

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
                message = await self._recv(client, self.packet_size)
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

    @staticmethod
    async def _accept(sock: ssl.SSLSocket) -> tuple[ssl.SSLSocket, str]:
        while True:
            try:
                return sock.accept()
            except BlockingIOError:
                time.sleep(1.e-3)

    @staticmethod
    async def _recv(sock: ssl.SSLSocket, buflen: int = 1024):
        while (msg := sock.recv(buflen)) == b'':
            time.sleep(1.e-3)
        return msg

    @staticmethod
    async def _sendall(sock: ssl.SSLSocket, data: bytes):
        sock.sendall(data)


def main():
    server = HTTPServer(port=13700)
    server.start()


if __name__ == '__main__':
    main()
