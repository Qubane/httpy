"""
The mighty silly webserver written in python for no good reason
"""
import os
import ssl
import time
import socket
import signal
import logging
import argparse
import threading
from src import APIv1
from src import file_man
from src.config import *
from src.request import *
from src.status_code import *


# typing
_usocket = socket.socket | ssl.SSLSocket

# logging
if not os.path.exists(f"{LOGGER_PATH}"):
    os.makedirs(f"{LOGGER_PATH}")
if os.path.isfile(f"{LOGGER_PATH}/latest.log") and os.path.getsize(f"{LOGGER_PATH}/latest.log") > 0:
    import gzip
    from datetime import datetime
    with open(f"{LOGGER_PATH}/latest.log", "rb") as file:
        with gzip.open(f"{LOGGER_PATH}/{datetime.now().strftime('%d-%m-%y %H-%M-%S')}.log.gz", "wb") as comp:
            comp.writelines(file)
    os.remove(f"{LOGGER_PATH}/latest.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"{LOGGER_PATH}/latest.log"),
        logging.StreamHandler()
    ]
)

# parser
_parser = argparse.ArgumentParser(
    prog="httpy",
    description="https web server")
_parser.add_argument("-p", "--port",
                     help="binding port (default 13700)",
                     type=int,
                     default=13700)
_parser.add_argument("-c", "--certificate",
                     help="certificate (or fullchain.pem)")
_parser.add_argument("-k", "--private-key",
                     help="private key")
_parser.add_argument("--compress-path",
                     help="enables pre-compression of files in 'www' folder (default False)",
                     default=False,
                     action="store_true")
_parser.add_argument("--disable-ssl",
                     help="SSL for HTTPs encrypted connection (default True)",
                     default=False,
                     action="store_true")
_parser.add_argument("-v", "--verbose",
                     help="verbose (default False)",
                     default=False,
                     action="store_true")
ARGS = _parser.parse_args()
if not ARGS.disable_ssl and (ARGS.certificate is None or ARGS.private_key is None):
    _parser.error("enabled SSL requires CERTIFICATE and PRIVATE_KEY arguments")


class HTTPyServer:
    """
    Tiny HTTPy server
    """

    def __init__(
            self,
            *,
            port: int,
            path_map: dict[str, dict],
            enable_ssl: bool = True,
            keypair: tuple[str, str] | None = None
    ):
        """
        :param port: binding port
        :param enable_ssl: use https
        :param path_map: path map
        :param keypair: fullchain.pem + privkey.pem
        """

        # Sockets
        self.port: int = port
        self.sock: _usocket | None = None
        self.ssl_enabled: bool = enable_ssl
        self.ssl_context: ssl.SSLContext | None = None
        self.make_socket(keypair)

        # client thread list
        self.client_threads: list[threading.Thread] = []
        self.semaphore: threading.Semaphore = threading.Semaphore(CLIENT_MAX_PROCESS)

        # add signaling
        self.stop_event = threading.Event()
        signal.signal(signal.SIGINT, self._signal_interrupt)

        # path mapping
        self.path_map: dict[str, dict] = path_map

    def _signal_interrupt(self, *args):
        """
        Checks for CTRL+C keyboard interrupt, to properly stop the HTTP server
        """

        # stop all threads
        self.stop_event.set()
        for thread in self.client_threads:
            thread.join()

    def make_socket(self, keypair: tuple | None = None):
        """
        Binds server to 0.0.0.0:PORT.
        """

        http_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.ssl_enabled and self.ssl_context is None:  # if ssl is on, but ssl context is None
            # if keypair was not given, raise an exception
            if keypair is None:
                raise KeyError("Key pair was not provided; unable to create ssl context.")

            # create new ssl context
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.ssl_context.check_hostname = False
            self.ssl_context.load_cert_chain(certfile=keypair[0], keyfile=keypair[1])
        if self.ssl_enabled:  # if ssl is on -> wrap socket
            self.sock = self.ssl_context.wrap_socket(http_socket, server_side=True)
        else:  # if ssl is off -> assign generic socket
            self.sock = http_socket

    def bind_listen(self):
        """
        Binds socket to 0.0.0.0:port and starts listening
        """

        self.sock.bind(('', self.port))
        self.sock.listen()

    def reconnect(self):
        """
        Reconnects HTTPy server
        """

        # stop all threads
        self.stop_event.set()
        for thread in self.client_threads:
            thread.join()

        # ensure closed socket
        self.sock.close()

        # make and bind listen socket
        self.make_socket()
        self.bind_listen()

        # clear the event
        self.stop_event.clear()

    def start(self):
        """
        Method to start the web server
        """

        # bind and start listening to port
        self.bind_listen()
        self.sock.setblocking(False)

        def _accept_client():
            client = self._accept()
            if client is None:
                return

            # create thread for new client and append it to the list
            th = threading.Thread(target=self._client_thread, args=[client])
            self.client_threads.append(th)
            th.start()

        # loop
        while not self.stop_event.is_set():
            try:
                _accept_client()
            except Exception as e:
                logging.warning(f"ignoring exception:", exc_info=e)

        # close server socket
        self.sock.close()

    def _client_thread(self, client: _usocket):
        """
        Handles getting client's requests
        :param client: client ssl socket
        """

        self.semaphore.acquire()

        try:
            client.settimeout(10)
            client.setblocking(False)
            request = self._recv_request(client)
            if request is not None:
                # log request
                logging.info(f"IP: {client.getpeername()[0]}")
                for key, val in request.__dict__.items():
                    logging.info(f"{key}: {val}")

                # handle request
                self._client_request_handler(client, request)
        except Exception as e:
            logging.warning("ignoring error:", exc_info=e)

        # Remove self from thread list and close the connection
        self.client_threads.remove(threading.current_thread())
        self.semaphore.release()

        try:
            client.close()
        except (ssl.SSLError, OSError):
            pass

    def _client_request_handler(self, client: _usocket, request: Request):
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
        self._send_response(client, response)

    def _handle_get(self, client: _usocket, request: Request) -> Response:
        """
        Handles GET requests from a client
        """

        split_path = request.path.split("/", maxsplit=16)[1:]
        if request.path in self.path_map:  # assume browser
            filedata = self.fetch_file(request.path)
            headers = self.fetch_file_headers(request.path)
            return Response(b'', STATUS_CODE_OK, headers, data_stream=filedata)
        elif len(split_path) >= 2 and split_path[0] in API_VERSIONS:  # assume script
            # unsupported API version
            if not API_VERSIONS[split_path[0]]:
                if request.type == "GET":
                    return Response(b'API unavailable / deprecated', STATUS_CODE_BAD_REQUEST)

            # return API response
            return APIv1.api_call(client, request)
        else:
            return Response(b'Page not found...', STATUS_CODE_NOT_FOUND)

    def _handle_post(self, client: _usocket, request: Request) -> Response:
        """
        Handles POST request from a client
        """

    def _recv_request(self, client: _usocket) -> Request | None:
        """
        Receive request from client
        :return: request
        :raises: anything that recv raises
        """

        buffer = bytearray()
        size = 0
        timer = SOCKET_TIMER
        while not self.stop_event.is_set() and timer > 0:
            try:
                buffer += client.recv(BUFFER_LENGTH)
                if buffer[-4:] == b'\r\n\r\n':
                    return Request.create(buffer)
                if size == len(buffer):  # got 0 bytes
                    break
                if size > BUFFER_MAX_SIZE:
                    break
                size = len(buffer)
            except (ssl.SSLWantReadError, BlockingIOError):
                time.sleep(SOCKET_ACK_INTERVAL)
            except (ssl.SSLError, OSError):
                break
            timer -= 1
        return None

    def _send_response(self, client: _usocket, response: Response) -> None:
        """
        Send response to client
        """

        # append connection status headers
        response.headers["Connection"] = "close"

        # generate basic message
        message = b'HTTP/1.1 ' + response.status.__bytes__() + b'\r\n'
        for key, value in response.headers.items():
            message += f"{key}: {value}\r\n".encode("utf8")
        message += b'\r\n'

        # send message
        is_first = True
        for packet in response.get_data_stream():
            timer = SOCKET_TIMER
            while timer > 0:
                try:
                    # doesn't work with 'else' or if no 'print(is_first)' is present
                    # I have no clue as to why
                    if is_first:
                        client.sendall(message)
                        is_first = False
                    if not is_first:
                        client.sendall(packet)
                        break
                except (ssl.SSLWantWriteError, BlockingIOError):
                    pass
                except (ssl.SSLError, OSError):
                    return
                time.sleep(SOCKET_ACK_INTERVAL)
                timer -= 1
            if self.stop_event.is_set() or timer <= 0:
                return

    def _accept(self) -> _usocket | None:
        """
        socket.accept, but for more graceful closing
        """

        while not self.stop_event.is_set():
            try:
                if len(self.client_threads) < CLIENT_MAX_AMOUNT:
                    return self.sock.accept()[0]
            except (ssl.SSLError, BlockingIOError):
                pass
            except OSError as e:
                if e.errno == 38:  # operation on something that is not a socket
                    self.reconnect()
                    logging.info("Socket reconnected")
                else:  # anything else
                    pass
            time.sleep(SOCKET_ACK_INTERVAL)
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
                while msg := file.read(BUFFER_LENGTH):
                    yield msg


def main():
    path_map = file_man.generate_path_map(verbose=ARGS.verbose)
    if ARGS.compress_path:
        path_map = file_man.compress_path_map(
            path_map,
            path_prefix=FILE_MAN_COMPRESSED_PATH,
            regen=True,
            verbose=ARGS.verbose)

    server = HTTPyServer(
        port=ARGS.port,
        path_map=path_map,
        keypair=(ARGS.certificate, ARGS.private_key),
        enable_ssl=not ARGS.disable_ssl)
    server.start()


if __name__ == '__main__':
    main()
