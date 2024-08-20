"""
The mighty silly webserver written in python for no good reason
"""


import ssl
import time
import gzip
import socket
import asyncio
import aiofiles
import threading


# path mapping
PATH_MAP = {
    "/":                        {"path": "www/index.html"},
    "/index.html":              {"path": "www/index.html"},
    "/robots.txt":              {"path": "www/robots.txt"},
    "/favicon.ico":             {"path": "www/favicon.ico"},
    "/css/styles.css":          {"path": "css/styles.css"},
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


class Request:
    """
    Just a request
    """

    def __init__(self):
        self.type: str = ""
        self.path: str = ""

    @staticmethod
    def create(raw_request: bytes):
        """
        Creates self class from raw request
        :param raw_request: bytes
        :return: self
        """

        # new request
        request = Request()

        # fix type and path
        request.type = raw_request[:raw_request.find(b' ')].decode("ascii")
        request.path = raw_request[len(request.type)+1:raw_request.find(b' ', len(request.type)+1)].decode("ascii")

        # decode headers
        for raw_header in raw_request.split(b'\r\n'):
            if len(pair := raw_header.decode("ascii").split(":")) == 2:
                key, val = pair
                val = val.strip()

                # set attribute to key value pair
                setattr(request, key, val)

        # return request
        return request

    def __str__(self):
        return '\n'.join([f"{key}: {val}" for key, val in self.__dict__.items()])


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

        self.clients: list[socket.socket] = []

    def start(self):
        """
        Method to start the web server
        """

        # bind and start listening to port
        self.socket.bind(('', self.bind_port))
        self.socket.listen()

        # start the listening thread
        threading.Thread(target=self._listen_thread, daemon=True).start()

        # keep alive
        try:
            while True:
                # sleep 100 ms, otherwise the while true will 100% one of your cores
                time.sleep(0.1)

        # shutdown on keyboard interrupt
        except KeyboardInterrupt:
            self.socket.close()
            print("Closed.")

    def _listen_thread(self):
        """
        Listening for new connections
        """

        # run the coroutine
        asyncio.run(self._thread_listen_coro())

    async def _thread_listen_coro(self):
        while True:
            # accept new connection, add to client list and start listening to it
            client, _ = self.socket.accept()
            self.clients.append(client)
            await self.client_handle(client)

    async def client_handle(self, client: socket.socket):
        """
        Handles client's connection
        """

        while True:
            # receive request from client
            raw_request = self._recvall(client)

            # decode request
            request: Request = Request.create(raw_request)

            # log request
            async with aiofiles.open("logs.log", "a") as f:
                await f.write(f"IP: {client.getpeername()[0]}\n{request}\n\n")

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
    async def handle_get_request(client: socket.socket, request: Request):
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
            HTTPServer._send(client, 200, data, headers)
        else:
            # send 404 response to the client
            HTTPServer._send(client, 404)

    @staticmethod
    def _send(client: socket.socket, response: int, data: bytes = None, headers: dict[str, str] = None):
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
        client.sendall(
            b'HTTP/1.1 ' +
            get_response_code(response) +
            b'\r\n' +
            byte_header +       # if empty, we'll just get b'\r\n\r\n'
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

    def _recvall(self, client: socket.socket) -> bytes:
        """
        Receive All (just receives the whole message, instead of 1 packet at a time)
        """

        # create message buffer
        buffer: bytearray = bytearray()

        # start fetching the message
        while True:
            try:
                # fetch packet
                message = client.recv(self.packet_size)
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
