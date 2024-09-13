import ssl
import socket
import signal
import threading
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
            self.ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER, check_hostname=False)
            self.ssl_ctx.load_cert_chain(certfile=certificate, keyfile=private_key)

        # signaling
        self.halted: threading.Event = threading.Event()
        signal.signal(signal.SIGINT, self.stop)

    def _make_socket(self):
        """
        Creates / recreates the socket
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
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


if __name__ == '__main__':
    pass
