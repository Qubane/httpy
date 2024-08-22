from time import sleep
from ssl import SSLSocket


_SOCK_TIME_DELAY = 1.e-3


def ssl_sock_accept(sock: SSLSocket) -> tuple[SSLSocket, str]:
    while True:
        try:
            return sock.accept()
        except BlockingIOError:
            sleep(_SOCK_TIME_DELAY)


def ssl_sock_recv(sock: SSLSocket, buflen: int = 1024):
    while (msg := sock.recv(buflen)) == b'':
        sleep(_SOCK_TIME_DELAY)
    return msg
