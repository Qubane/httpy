"""
The mighty silly webserver written in python for no good reason
"""


import ssl
import time
import socket
import signal
import threading
import traceback

from src import APIv1
from src.config import *
from src.request import *
from src.status_code import *
from src.file_man import PATH_MAP


# typing
usocket = socket.socket | ssl.SSLSocket


class HTTPServer:
    """
    The mightier HTTP server!
    Now uses threading
    """

    def __init__(
            self,
            *,
            port: int,
            enable_ssl: bool = True,
            path_map: dict[str, dict] | None = None,
            key_pair: tuple[str, str] | None = None
    ):
        """
        :param port: binding port
        :param enable_ssl: use https
        :param path_map: path map
        :param key_pair: fullchain.pem + privkey.pem
        """

        # Sockets
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if enable_ssl:
            # SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.check_hostname = False
            context.load_cert_chain(certfile=key_pair[0], keyfile=key_pair[1])
            self.sock: usocket = context.wrap_socket(sock, server_side=True)
        else:
            self.sock: usocket = sock
        self.port: int = port

        # client thread list
        self.client_threads: list[threading.Thread] = []
        self.semaphore: threading.Semaphore = threading.Semaphore(CLIENT_MAX_PROCESS)

        # add signaling
        self.stop_event = threading.Event()
        signal.signal(signal.SIGINT, self._signal_interrupt)

        # path mapping
        self.path_map: dict[str, dict] = path_map if path_map else PATH_MAP

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
            try:
                client = self._accept()
            except ssl.SSLEOFError:
                continue
            except OSError:
                print("Ignoring exception:\n", traceback.format_exc())
                continue
            if client is None:
                continue

            # create thread for new client and append it to the list
            th = threading.Thread(target=self._client_thread, args=[client])
            self.client_threads.append(th)
            th.start()

        # close server socket
        self.sock.close()

    def _client_thread(self, client: usocket):
        """
        Handles getting client's requests
        :param client: client ssl socket
        """

        self.semaphore.acquire()
        try:
            request = self._recv_request(client)
            if request is not None:
                self._client_request_handler(client, request)
        except ssl.SSLEOFError:
            pass
        except OSError as e:
            print(f"Request dropped due to: {e}")
        except Exception:
            print("Ignoring exception:\n", traceback.format_exc())

        # Remove self from thread list and close the connection
        self.client_threads.remove(threading.current_thread())
        self.semaphore.release()
        client.close()

    def _client_request_handler(self, client: usocket, request: Request):
        """
        Handles responses to client's requests
        :param client: client
        :param request: client's request
        """

        match request.type:
            case "GET":
                response = self._handle_get(client, request)
            case _:
                response = Response(b'', STATUS_CODE_NOT_FOUND)

        # process header data
        if response.headers.get("Connection") is None:
            response.headers["Connection"] = "close"

        # generate basic message
        message = b'HTTP/1.1 ' + response.status.__bytes__() + b'\r\n'
        for key, value in response.headers.items():
            message += f"{key}: {value}\r\n".encode("utf8")
        message += b'\r\n'

        # send message
        client.sendall(message)
        for packet in response.get_data_stream():
            if packet is None:
                break
            client.sendall(packet)

            # check for stop event
            if self.stop_event.is_set():
                break

    def _handle_get(self, client: usocket, request: Request) -> Response:
        """
        Handles GET requests from a client
        """

        split_path = request.path.split("/", maxsplit=16)[1:]
        if request.path in self.path_map:  # assume browser
            filedata = self.fetch_file(request.path)
            headers = self.fetch_file_headers(request.path)
            response = Response(b'', STATUS_CODE_OK, headers, data_stream=filedata)

            return response
        elif len(split_path) >= 2 and split_path[0] in API_VERSIONS:  # assume script
            # unsupported API version
            if not API_VERSIONS[split_path[0]]:
                if request.type == "GET":
                    return Response(b'API unavailable / deprecated', STATUS_CODE_BAD_REQUEST)

            # return API response
            return APIv1.api_call(client, request)
        else:
            return Response(b'', STATUS_CODE_NOT_FOUND)

    def _handle_post(self, client: usocket, request: Request) -> Response:
        """
        Handles POST request from a client
        """

    def _recv_request(self, client: usocket) -> Request | None:
        """
        Receive request from client
        :return: request
        :raises: anything that recv raises
        """

        buffer = bytearray()
        while not self.stop_event.is_set():
            if len(msg := client.recv(BUFFER_LENGTH)) == 0:
                break
            buffer += msg
            if buffer[-4:] == b'\r\n\r\n':
                return Request.create(buffer)
            if len(buffer) > BUFFER_MAX_SIZE:  # ignore big messages
                break
        return None

    def _accept(self) -> usocket | None:
        """
        socket.accept, but for more graceful closing
        """

        while not self.stop_event.is_set():
            try:
                if len(self.client_threads) < CLIENT_MAX_AMOUNT:
                    return self.sock.accept()[0]
            except BlockingIOError:
                time.sleep(0.005)
        return None

    def fetch_file_headers(self, path: str) -> dict[str, Any] | None:
        """
        Fetcher file header data
        :param path: filepath
        :return: headers
        """

        if path in self.path_map:
            return self.path_map[path]["headers"]
        return None

    def fetch_file(self, path: str) -> Generator[bytes, None, None] | None:
        """
        Fetches file
        :param path: filepath
        :return: data stream
        """

        if path in self.path_map:
            with open(self.path_map[path]["path"], "rb") as file:
                while (msg := file.read(BUFFER_LENGTH)):
                    yield msg
        yield None


def main():
    server = HTTPServer(port=13700, key_pair=("fullchain.pem", "privkey.pem"))
    server.start()


if __name__ == '__main__':
    main()
