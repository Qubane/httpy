import logging.config
import ssl
import socket
import threading
from time import sleep
from src.logger import *
from src.structures import unified_socket, Request, Response


class HTTPyServer:
    """
    Tiny HTTPy server
    """

    def __init__(
            self,
            port: int,
            certificate: str | None = None,
            private_key: str | None = None,
            enable_ssl: bool = False):
        # file manager (fileman)
        self.fileman = None

        # sockets
        self.port: int = port
        self.sock: unified_socket | None = None
        self.ctx: ssl.SSLContext | None = None
        if enable_ssl:
            self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER, check_hostname=False)
            self.ctx.load_cert_chain(certfile=certificate, keyfile=private_key)

        # signaling
        import signal
        self.halted: threading.Event = threading.Event()
        signal.signal(signal.SIGINT, self.stop)

    def _make_socket(self) -> None:
        """
        Creates / recreates the socket
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        if self.ctx is None:  # context doesn't exist -> ssl is disabled
            self.sock = sock
        else:  # ssl is enabled
            self.sock = self.ctx.wrap_socket(sock, server_side=True)

    def _bind_listen(self) -> None:
        """
        Binds and listens to socket
        """

        self.sock.bind(("", self.port))
        self.sock.listen()

    def start(self) -> None:
        """
        Starts the HTTPy Server
        """

        # make and bind server socket
        self._make_socket()
        self._bind_listen()

        logging.info("Server started")

        # main loop
        while not self.halted.is_set():
            try:  # try to accept new client
                self._accept_request()
            except Exception as e:  # in case of exception -> log and continue
                logging.warning("ignoring exception:", exc_info=e)

        logging.info("Server stopped.")

        # close server after interrupt
        self.sock.close()

    def stop(self, *args, **kwargs) -> None:
        """
        Stops all threads
        """

        logging.info("Server stopping...")

        self.halted.set()
        for thread in threading.enumerate():
            if thread is threading.main_thread() or thread.daemon:
                continue
            thread.join()

    def reconnect(self) -> None:
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

    def _accept_request(self) -> None:
        """
        Accepts client's requests
        """

        client = self._accept()
        if client:
            threading.Thread(target=self._handle_client, args=(client,)).start()

    def _handle_client(self, client: unified_socket) -> None:
        """
        Handles client's connection
        """

        threading.Thread(target=self._client_daemon, args=(client,), daemon=True).start()
        timer = Config.THREADING_TIMEOUT / 100
        while timer > 0 and not self.halted.is_set():
            sleep(0.1)
            timer -= 1

    def _client_daemon(self, client: unified_socket):
        """
        Client's daemon thread
        """

        request = self._recv(client)
        print(request)

    def _send(self, client: unified_socket, response: Response) -> None:
        """
        Send response to client
        :param client: client connection
        :param response: response
        """

        for data in response.get_data_stream():
            sent = 0
            while sent < len(data):
                try:
                    sent += client.send(data[sent:])
                except (ssl.SSLWantWriteError, BlockingIOError):
                    sleep(Config.SOCKET_ACK_INTERVAL)
                except (ssl.SSLError, OSError):
                    return

    def _recv(self, client: unified_socket) -> Request:
        """
        Recv request from client
        :param client: client connection
        :return: request
        """

        buffer = bytearray()
        while not self.halted.is_set():
            size = len(buffer)
            try:
                buffer += client.recv(Config.SOCKET_RECV_SIZE)
            except (ssl.SSLWantReadError, BlockingIOError):
                sleep(Config.SOCKET_ACK_INTERVAL)
            except (ssl.SSLError, OSError):
                break
            if buffer[-4:] == b'\r\n\r\n':
                return Request(buffer)
            if size == len(buffer) or size > Config.SOCKET_MAX_SIZE:
                break

    def _accept(self) -> unified_socket | None:
        """
        Accepts new connections
        """

        while not self.halted.is_set():
            if len(threading.enumerate()) > Config.THREADING_MAX_NUMBER:
                continue
            try:
                return self.sock.accept()[0]
            except BlockingIOError:
                sleep(Config.SOCKET_ACK_INTERVAL)


def main():
    httpy = HTTPyServer(
        port=13700,
        certificate=None,
        private_key=None,
        enable_ssl=False)
    httpy.start()


if __name__ == '__main__':
    main()
