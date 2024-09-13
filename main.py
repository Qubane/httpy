import ssl
import socket
import threading
from time import sleep
from src.logger import *
from src.structures import unified_socket


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

        # main loop
        while not self.halted.is_set():
            try:  # try to accept new client
                self._accept_request()
            except Exception as e:  # in case of exception -> log and continue
                logging.warning("ignoring exception:", exc_info=e)

        # close server after interrupt
        self.sock.close()

    def stop(self, *args, **kwargs) -> None:
        """
        Stops all threads
        """

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
        if client is None:
            return

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
                pass
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
