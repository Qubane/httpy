import ssl
import socket
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


if __name__ == '__main__':
    pass
