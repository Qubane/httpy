import time
from ssl import SSLSocket


async def ssl_sock_accept(sock: SSLSocket) -> tuple[SSLSocket, str]:
    while True:
        try:
            return sock.accept()
        except BlockingIOError:
            time.sleep(1.e-3)


async def ssl_sock_recv(sock: SSLSocket, buflen: int = 1024):
    while (msg := sock.recv(buflen)) == b'':
        time.sleep(1.e-3)
    return msg


async def ssl_sock_sendall(sock: SSLSocket, data: bytes):
    sock.sendall(data)
