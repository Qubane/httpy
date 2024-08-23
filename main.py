"""
The mighty silly webserver written in python for no good reason
"""


import ssl
import gzip
import time
import socket
import brotli
import signal
import threading
from src import APIv1
from src.request import *
from src.status_code import *
from src.minimizer import minimize_html


# path mapping
PATH_MAP = {
    "/":                    {"path": "www/index.html"},
    "/index.html":          {"path": "www/index.html"},
    "/robots.txt":          {"path": "www/robots.txt"},
    "/favicon.ico":         {"path": "www/favicon.ico"},
    "/css/styles.css":      {"path": "css/styles.css"},
    "/about":               {"path": "www/about.html"},
    "/test":                {"path": "www/test.html"},
}

# API
API_VERSIONS = {
    "APIv1":                {"supported": True}
}

# internal path map
I_PATH_MAP = {
    "/err/response":        {"path": "www/err/response.html"}
}


class HTTPServer:
    """
    The mightier HTTP server!
    Now uses threading
    """

    def __init__(self, *, port: int, packet_size: int = 2048):
        # SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.check_hostname = False
        context.load_cert_chain(
            certfile=r"C:\Certbot\live\qubane.ddns.net\fullchain.pem",  # use your own path here
            keyfile=r"C:\Certbot\live\qubane.ddns.net\privkey.pem")     # here too

        # Sockets
        self.sock: ssl.SSLSocket = context.wrap_socket(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            server_side=True)
        self.buf_len: int = packet_size
        self.port: int = port

        # client thread list and server thread
        self.client_threads: list[threading.Thread] = []

        # add signaling
        self.stop_event = threading.Event()
        signal.signal(signal.SIGINT, self._signal_interrupt)

    def _signal_interrupt(self, *args):
        """
        Checks for CTRL+C keyboard interrupt, to properly stop the HTTP server
        """

        # stop all threads
        self.stop_event.set()
        for thread in self.client_threads:
            thread.join()

    def start(self):
        """
        Method to start the web server
        """

        # bind and start listening to port
        self.sock.bind(('', self.port))
        self.sock.setblocking(False)
        self.sock.listen()

        # listen and respond handler
        while not self.stop_event.is_set():
            # accept new client
            client = self._accept()
            if client is None:
                break

            # create thread for new client and append it to the list
            th = threading.Thread(target=self._client_thread, args=[client])
            self.client_threads.append(th)
            th.start()

        # close server socket
        self.sock.close()

    def _client_thread(self, client: ssl.SSLSocket):
        """
        Handles getting client's requests
        :param client: client ssl socket
        """

        # client.settimeout(5)
        while not self.stop_event.is_set():
            try:
                # get client's request
                request = self._recv_request(client)
                if request is None:
                    break

                threading.Thread(target=self._client_request_handler, args=[client, request], daemon=True).start()
            except TimeoutError:
                print("Client timeout")
                break
            except Exception as e:
                print(e)
                break

        # close the connection once stop even was set or an error occurred
        client.close()

    def _client_request_handler(self, client: ssl.SSLSocket, request: Request):
        """
        Handles responses to client's requests
        :param client: client
        :param request: client's request
        """

        match request.type:
            case "GET" | "HEAD":
                response = self._handle_get(client, request)
            # case "POST":  # Not Implemented
            #     response = self._handle_post(client, request)
            case _:
                with open(I_PATH_MAP["/err/response"]["path"], "r", encoding="ascii") as file:
                    data = file.read().format(status_code=str(STATUS_CODE_NOT_FOUND)).encode("ascii")
                response = Response(data, STATUS_CODE_NOT_FOUND)

        # process header data
        if response.headers.get("Content-Encoding") is None and response.compress:
            supported_compressions = [x.strip() for x in getattr(request, "Accept-Encoding", "").split(",")]
            if "br" in supported_compressions:
                response.headers["Content-Encoding"] = "br"
                response.data = brotli.compress(response.data)
            elif "gzip" in supported_compressions:
                response.headers["Content-Encoding"] = "gzip"
                response.data = gzip.compress(response.data)
        if response.headers.get("Content-Length") is None:
            response.headers["Content-Length"] = len(response.data)
        if response.headers.get("Connection") is None:
            response.headers["Connection"] = "close"

            # generate basic message
        message = b'HTTP/1.1 ' + response.status.__bytes__() + b'\r\n'
        for key, value in response.headers.items():
            message += f"{key}: {value}\r\n".encode("ascii")
        message += b'\r\n' + response.data

        # send message
        client.sendall(message)

    def _handle_get(self, client: ssl.SSLSocket, request: Request) -> Response:
        """
        Handles GET / HEAD requests from a client
        """

        split_path = request.path.split("/", maxsplit=16)[1:]
        if request.path in PATH_MAP:  # assume browser
            filepath = PATH_MAP[request.path]["path"]
            with open(filepath, "rb") as file:
                data = file.read()

            if request.type == "GET":
                return Response(data, STATUS_CODE_OK)
            elif request.type == "HEAD":
                return Response(b'', STATUS_CODE_OK, {"Content-Length": len(data)})
            else:
                raise TypeError("Called GET handler for non-GET request")

        elif len(split_path) >= 2 and split_path[0] in API_VERSIONS:  # assume script
            # unsupported API version
            if not API_VERSIONS[split_path[0]]:
                if request.type == "GET" or request.type == "HEAD":
                    return Response(b'', STATUS_CODE_BAD_REQUEST)
                else:
                    raise TypeError("Called GET handler for non-GET request")

            return APIv1.api_call(client, request)

        else:  # assume browser
            with open(I_PATH_MAP["/err/response"]["path"], "r", encoding="ascii") as file:
                data = file.read()
            data = data.format(status_code=str(STATUS_CODE_NOT_FOUND)).encode("ascii")
            return Response(data, STATUS_CODE_NOT_FOUND)

    def _handle_post(self, client: ssl.SSLSocket, request: Request) -> Response:
        """
        Handles POSt request from a client
        """

    def _recv_request(self, client: ssl.SSLSocket) -> Request | None:
        """
        Receive request from client
        :return: request
        :raises: anything that recv raises
        """

        buffer = bytearray()
        while not self.stop_event.is_set():
            msg = client.recv(self.buf_len)
            if len(msg) == 0:
                break
            buffer += msg
            if buffer[-4:] == b'\r\n\r\n':
                return Request.create(buffer)
        return None

    def _accept(self) -> ssl.SSLSocket | None:
        """
        socket.accept, but for more graceful closing
        """

        while not self.stop_event.is_set():
            try:
                return self.sock.accept()[0]
            except BlockingIOError:
                time.sleep(0.001)
        return None


# class HTTPServer:
#
#     def client_handle(self, client: ssl.SSLSocket):
#         """
#         Handles client's connection
#         """
#
#         while True:
#             # receive request from client
#             raw_request = self._recvall(client)
#
#             if raw_request == b'':
#                 break
#
#             # decode request
#             request: Request = Request.create(raw_request)
#
#             # # log request
#             # async with aiofiles.open("logs.log", "a") as f:
#             #     await f.write(f"IP: {client.getpeername()[0]}\n{request}\n\n")
#
#             threading.Thread(target=self.handle_request, args=[client, request]).start()
#
#     def handle_request(self, client: ssl.SSLSocket, request: Request):
#         # handle requests
#         try:
#             match request.type:
#                 case "GET":
#                     self.handle_get_request(client, request)
#                 case _:
#                     pass
#
#         # break on exception
#         except Exception as e:
#             print(e)
#
#         # # close connection (stop page loading)
#         # self._close_client(client)
#
#     @staticmethod
#     def handle_get_request(client: ssl.SSLSocket, request: Request):
#         """
#         Handles user's GET request
#         """
#
#         # get available compression methods
#         compressions = [x.strip() for x in getattr(request, "Accept-Encoding", "").split(",")]
#
#         # check if request path is in the PATH_MAP
#         if request.path in PATH_MAP:
#             # if it is -> return file from that path
#             with open(PATH_MAP[request.path]["path"], "rb") as f:
#                 data = f.read()
#
#             # pre-compress data for HTML files
#             if PATH_MAP[request.path]["path"][-4:] == "html":
#                 data = minimize_html(data)
#
#             # add brotli compression header (if supported)
#             headers = {}
#             if "br" in compressions:
#                 headers["Content-Encoding"] = "br"
#
#             # else add gzip compression (if supported)
#             elif "gzip" in compressions:
#                 headers["Content-Encoding"] = "gzip"
#
#             # send 200 response with the file to the client
#             HTTPServer._send(client, 200, data, headers)
#
#         # if it's an API request
#         elif (api_version := request.path.split("/")[1]) in API_VERSIONS:
#             data = b''
#             headers = {}
#             match api_version:
#                 case "APIv1":
#                     status, data, headers = APIv1.respond(client, request)
#                 case _:
#                     status = 400
#
#             # if status is not 200 -> send bad response
#             if status != 200:
#                 HTTPServer._bad_response(client, status)
#                 return
#
#             # send data if no error
#             HTTPServer._send(client, status, data, headers)
#
#         # in case of error, return error page
#         else:
#             HTTPServer._bad_response(client, 404)
#
#     @staticmethod
#     def _bad_response(client: ssl.SSLSocket, status_code: int):
#         """
#         Sends a bad response page to the client.
#         :param client: client
#         :param status_code: status code
#         """
#
#         with open(I_PATH_MAP["/err/response.html"]["path"], "r") as f:
#             data = f.read()
#
#         # format error response
#         data = data.format(status_code=get_response_code(status_code).decode("ascii"))
#
#         # send response to the client
#         HTTPServer._send(client, status_code, data.encode("ascii"))


def main():
    server = HTTPServer(port=13700)
    server.start()


if __name__ == '__main__':
    main()
