"""
The mighty silly webserver written in python for no good reason
"""
import os
import ssl
import time
import socket
import signal
import logging
import threading
from src import APIv1
from src import file_man
from src.request import *
from src.status_code import *
from src.argparser import ARGS


# typing
unified_socket = socket.socket | ssl.SSLSocket

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


class HTTPyServer:
    """
    Tiny HTTPy server
    """

    def __init__(
            self,
            port: int,
            keypair: tuple[str, str] | None,
            path_config: dict,
            compress_path: bool,
            compressed_path: str,
            enable_ssl: bool = False):
        # file manager
        self.fileman: file_man.FileManager = file_man.FileManager()
        self.fileman.configure(path_config=path_config, compress_path=compress_path, compressed_path=compressed_path)

        # sockets
        self.port: int = port
        self.sock: unified_socket | None = None
        self.ssl_ctx: ssl.SSLContext | None = None
        if enable_ssl:
            self.ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER, check_hostname=False)
            self.ssl_ctx.load_cert_chain(certfile=keypair[0], keyfile=keypair[1])

        # threading
        self.semaphore: threading.Semaphore = threading.Semaphore(128)

        # signals
        self.halted: threading.Event = threading.Event()
        signal.signal(signal.SIGINT, self.stop)

    def _make_socket(self):
        """
        Creates / recreates the socket
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        if self.ssl_ctx is None:  # context doesn't exist -> ssl is disabled
            self.sock = sock
        else:  # ssl is enabled
            self.sock = self.ssl_ctx.wrap_socket(sock, server_side=True)

    def _bind_listen(self):
        """
        Binds and listens to socket
        """

        self.sock.bind(("", self.port))
        self.sock.listen()

    def start(self):
        """
        Starts the HTTPy Server
        """

        # make and bind server socket
        self._make_socket()
        self._bind_listen()

        # main loop
        while not self.halted.is_set():
            try:  # try to accept new client
                self._accept_call()
            except Exception as e:  # in case of exception -> log and continue
                logging.warning("ignoring exception:", exc_info=e)

        # close server after interrupt
        self.sock.close()

    def stop(self, *args, **kwargs):
        """
        Stops all threads
        """

        self.halted.set()
        for thread in threading.enumerate():
            if thread is threading.main_thread() or thread.daemon:
                continue
            thread.join()

    def reconnect(self):
        """
        Reconnects the socket in case of some wierd error
        """

        # stop the server
        self.stop()
        self.sock.close()

        # remake the socket
        self._make_socket()
        self._bind_listen()

        # clear halted flag
        self.halted.clear()

    def _accept_call(self):
        """
        Accept call to server socket
        """

        client = self._accept()
        if client is None:
            return

        threading.Thread(target=self._client_thread, args=[client]).start()

    def _client_thread(self, client: unified_socket):
        """
        Handles getting client's requests
        :param client: client ssl socket
        """

        self.semaphore.acquire()
        try:
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
            logging.warning("ignoring exception in thread:", exc_info=e)
        self.semaphore.release()

        try:
            client.close()
        except (ssl.SSLError, OSError):
            pass

    def _client_request_handler(self, client: unified_socket, request: Request):
        """
        Handles responses to client's requests
        :param client: client
        :param request: client's request
        """

        match request.type:
            case "GET":
                response = self._handle_get(client, request)
            case _:
                response = Response(b'Unable to process any request, other than GET')
        self._send_response(client, response)

    def _handle_get(self, client: unified_socket, request: Request) -> Response:
        """
        Handles GET requests from a client
        """

        # get supported compression algorithms
        encodings = [x.strip() for x in getattr(request, "Accept-Encoding", "").split(",")]

        split_path = request.path.split("/", maxsplit=16)[1:]
        if self.fileman.exists(request.path):  # assume browser
            file_dict = self.fileman.get_file_dict(request.path)
            headers = {
                "Content-Type": file_dict["-"].content_type,
                "Content-Length": file_dict["-"].content_length}
            data_stream = file_dict["-"].get_data_stream()
            if ARGS.compress_path and file_dict["compressed"]:
                if "br" in encodings:  # brotli compression
                    headers["Content-Encoding"] = "br"
                    headers["Content-Length"] = file_dict["br"].content_length
                    data_stream = file_dict["br"].get_data_stream()
                elif "gzip" in encodings:  # gzip compression
                    headers["Content-Encoding"] = "gzip"
                    headers["Content-Length"] = file_dict["gz"].content_length
                    data_stream = file_dict["gz"].get_data_stream()
            return Response(
                status=STATUS_CODE_OK, headers=headers, data_stream=data_stream)
        elif len(split_path) >= 2 and split_path[0] in API_VERSIONS:  # assume script
            # unsupported API version
            if not API_VERSIONS[split_path[0]]:
                return Response(b'API unavailable / deprecated', status=STATUS_CODE_BAD_REQUEST)

            # return API response
            return APIv1.api_call(client, request)
        else:
            return Response(b'Page not found...', status=STATUS_CODE_NOT_FOUND)

    def _handle_post(self, client: unified_socket, request: Request) -> Response:
        """
        Handles POST request from a client
        """

    def _recv_request(self, client: unified_socket) -> Request | None:
        """
        Receive request from client
        :return: request
        :raises: anything that recv raises
        """

        buffer = bytearray()
        size = 0
        timer = SOCKET_TIMER
        while not self.halted.is_set() and timer > 0:
            try:
                buffer += client.recv(BUFFER_LENGTH)
                if buffer[-4:] == b'\r\n\r\n':
                    return Request.construct(buffer)
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

    def _send_response(self, client: unified_socket, response: Response) -> None:
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
            if self.halted.is_set() or timer <= 0:
                return

    def _accept(self) -> unified_socket | None:
        """
        socket.socket.accept(), but for graceful exit handling
        """

        while not self.halted.is_set():
            try:
                if len(threading.enumerate()) < CLIENT_MAX_AMOUNT:
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


def main():
    server = HTTPyServer(
        port=ARGS.port,
        path_config=FILE_MAN_PATH_MAP,
        compress_path=ARGS.compress_path,
        compressed_path=FILE_MAN_COMPRESSED_PATH,
        keypair=(ARGS.certificate, ARGS.private_key),
        enable_ssl=ARGS.enable_ssl)
    server.start()


if __name__ == '__main__':
    main()
