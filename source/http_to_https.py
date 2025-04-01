import signal
import asyncio
import logging
from source.status import *
from source.classes import *
from source.settings import READ_BUFFER_SIZE, WRITE_BUFFER_SIZE

LOGGER: logging.Logger = logging.getLogger()


class TinyServer:
    """
    HTTP to HTTPs redirecting server
    """

    def __init__(self, bind_address: tuple[str, int], redirect: str):
        self.server: asyncio.Server | None = None
        self.bind_address: tuple[str, int] = bind_address

        self.redirect: str = redirect

    def run(self):
        """
        Starts the TinyServer server
        """

        asyncio.run(self.run_coro())

    async def run_coro(self):
        """
        Starts the TinyServer server. Coroutine
        """

        self.server = await asyncio.start_server(
            client_connected_cb=self.client_handle,
            host=self.bind_address[0],
            port=self.bind_address[1])

        LOGGER.info(f"Redirect server running on '{self.bind_address[0]}:{self.bind_address[1]}'")

        async with self.server:
            try:
                await self.server.serve_forever()
            except asyncio.exceptions.CancelledError:
                pass

        LOGGER.info("Redirect server stopped")

    def stop(self, *args):
        """
        Stops the HTTPy server
        """

        self.server.close()
        for sock in self.server.sockets:
            sock.close()

    async def client_handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Quick client handler
        """

        # we don't care what the client has to say
        await reader.read(READ_BUFFER_SIZE)

        # respond with 301
        response = Response(
            data=f"Moved Permanently. Redirecting to {self.redirect}".encode("ascii"),
            status=STATUS_CODE_MOVED_PERMANENTLY,
            headers={"Location": self.redirect})
        await response.write(writer)

        writer.close()
