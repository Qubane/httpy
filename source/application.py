"""
Main application file
"""


import ssl
import signal
import asyncio
from source.server import *


class App:
    """
    Main application class
    """

    def __init__(self, address: tuple[str, int], ssl_keys: tuple[str, str] | None = None):
        # define running boolean
        self.running: bool = False

        # define server and running task
        self._server: asyncio.Server | None = None

        # assign address and define ssl context
        self.address: tuple[str, int] | None = address
        self.ctx: ssl.SSLContext | None = None

        # make context if needed
        if ssl_keys and ssl_keys[0] and ssl_keys[1]:
            self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER, check_hostname=False)
            self.ctx.load_cert_chain(certfile=ssl_keys[0], keyfile=ssl_keys[1])

    def run(self) -> None:
        """
        Runs the application
        """

        # set running flag to True
        self.running = True

        # create signaling
        signal.signal(signal.SIGINT, self.quit)

        # run the task
        asyncio.run(self._run_server())

    def quit(self, *args) -> None:
        """
        Quits the application
        """

        self.running = False

    async def _run_server(self):
        """
        Run server coroutine
        """

        self._server = await asyncio.start_server(
            client_connected_cb=accept_client,
            host=self.address[0],
            port=self.address[1],
            ssl=self.ctx)

        # create running loop
        while self.running:
            await asyncio.sleep(0.01)
            await self._server.start_serving()

        # close server
        self._server.close()
