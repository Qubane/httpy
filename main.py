"""
The mighty silly webserver written in python for no good reason
"""


import time
import json
import gzip
import socket
import asyncio
import htmlmin
import aiofiles
import threading


class Request:
    """
    Just a request
    """

    def __init__(self):
        self.type: str = ""
        self.path: str = ""

    @staticmethod
    def create(raw_request: bytes):
        """
        Creates self class from raw request
        :param raw_request: bytes
        :return: self
        """

        # new request
        request = Request()

        # fix type and path
        request.type = raw_request[:raw_request.find(b' ')].decode("ascii")
        request.path = raw_request[len(request.type)+1:raw_request.find(b' ', len(request.type)+1)].decode("ascii")

        # decode headers
        for raw_header in raw_request.split(b'\r\n'):
            if len(pair := raw_header.decode("ascii").split(":")) == 2:
                key, val = pair
                val = val.strip()

                # set attribute to key value pair
                setattr(request, key, val)

        # return request
        return request

    def __str__(self):
        return '\n'.join([f"{key}: {val}" for key, val in self.__dict__.items()])


class HTTPServer:
    """
    The mighty HTTP server
    """

    def __init__(self, *, port: int, packet_size: int = 2048):
        self.bind_port: int = port
        self.packet_size: int = packet_size
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.clients: list[socket.socket] = []

    def start(self):
        """
        Method to start the web server
        """

        # bind and start listening to port
        self.socket.bind(('', self.bind_port))
        self.socket.listen()

        # start the listening thread
        threading.Thread(target=self._listen_thread, daemon=True).start()

        # keep alive
        try:
            while True:
                # sleep 100 ms, otherwise the while true will 100% one of your cores
                time.sleep(0.1)

        # shutdown on keyboard interrupt
        except KeyboardInterrupt:
            self.socket.close()
            print("Closed.")

    def _listen_thread(self):
        """
        Listening for new connections
        """

        # run the coroutine
        asyncio.run(self._thread_listen_coro())

    async def _thread_listen_coro(self):
        while True:
            # accept new connection, add to client list and start listening to it
            client, _ = self.socket.accept()
            self.clients.append(client)
            await self.client_handle(client)

    async def client_handle(self, client: socket.socket):
        """
        Handles client's connection
        """

        while True:
            # receive request from client
            raw_request = self._recvall(client)

            # decode request
            request: Request = Request.create(raw_request)

            self._close_client(client)
            break

    def _close_client(self, client: socket.socket):
        """
        Closes a client
        """

        client.close()
        if client in self.clients:
            self.clients.remove(client)

    def _recvall(self, client: socket.socket) -> bytes:
        """
        Receive All (just receives the whole message, instead of 1 packet at a time)
        """

        # create message buffer
        buffer: bytearray = bytearray()

        # start fetching the message
        while True:
            try:
                # fetch packet
                message = client.recv(self.packet_size)
            except OSError:
                break

            # that happens when user stops loading the page
            if message == b'':
                break

            # append fetched message to the buffer
            buffer += message

            # check for EoF
            if buffer[-4:] == b'\r\n\r\n':
                # return the received message
                return buffer

        # return empty buffer on error
        return b''


def main():
    server = HTTPServer(port=13701)
    server.start()


if __name__ == '__main__':
    main()
