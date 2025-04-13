"""
Main application file
"""


import ssl
import asyncio
from source.server import *


class App:
    """
    Main application class
    """

    def __init__(self, address: tuple[str, int], ssl_keys: tuple[str, str] | None = None):
        self.server: asyncio.Server | None = None

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

        asyncio.run(self._run_server())

    def quit(self) -> None:
        """
        Quits the application
        """

        self.server.close()
        for sock in self.server.sockets:
            sock.close()

    async def _run_server(self):
        """
        Run server coroutine
        """

        self.server = await asyncio.start_server(
            client_connected_cb=accept_client,
            host=self.address[0],
            port=self.address[1],
            ssl=self.ctx)

        async with self.server:
            try:
                await self.server.serve_forever()
            except asyncio.exceptions.CancelledError:
                pass
