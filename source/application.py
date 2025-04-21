"""
Main application file
"""


import ssl
import signal
import asyncio
import logging
import argparse
from source.handler import *


LOGGER: logging.Logger = logging.getLogger(__name__)


class App:
    """
    Main application class
    """

    def __init__(self, address: tuple[str, int], ssl_keys: tuple[str, str] | None = None):
        # define running boolean
        self.running: bool = False

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
        asyncio.get_event_loop().run_until_complete(self._run_server())

    def quit(self, *args) -> None:
        """
        Quits the application
        """

        logging.info(f"Attempting to close the server")
        self.running = False

    async def _run_server(self):
        """
        Run server coroutine
        """

        # define servers
        logging.info("Attempting to start generic server")
        generic_server = await asyncio.start_server(
            client_connected_cb=accept_client,
            host=self.address[0],
            port=self.address[1],
            ssl=self.ctx)
        logging.info(f"Server started at '{self.address[0]}:{self.address[1]}'")

        # if ssl context is present, enable auth server
        if self.ctx is not None:
            logging.info("Attempting to start auth server")
            auth_server = await asyncio.start_server(
                client_connected_cb=accept_http_client,
                host=self.address[0],
                port=self.address[1]+1)
            logging.info(f"Server started at '{self.address[0]}:{self.address[1]+1}'")

        # client handle initialization
        logging.info(f"Initializing client handler")
        initialize_client_handle()
        logging.info(f"Client handler initialized")

        async def generic_coro():
            # create running loop
            while self.running:
                await asyncio.sleep(0.01)
                await generic_server.start_serving()
            generic_server.close()

        async def auth_coro():
            # if ssl context doesn't exist, exit
            if self.ctx is None:
                return
            
            # create running loop
            while self.running:
                await asyncio.sleep(0.01)
                await auth_server.start_serving()
            auth_server.close()

        await asyncio.gather(generic_coro(), auth_coro())

        # close server
        logging.info(f"Server closed")


def parse_arguments() -> argparse.Namespace:
    """
    Parses CLI arguments
    :return: arguments
    """

    # parser
    parser = argparse.ArgumentParser(
        prog="HTTPy",
        description="HTTP python web server")

    # add arguments
    parser.add_argument("-a", "--address",
                        help="binding address:port",
                        required=True)
    parser.add_argument("-c", "--certificate",
                        help="SSL certificate (or fullchain.pem)")
    parser.add_argument("-k", "--private-key",
                        help="SSL private key")

    # parse arguments
    args = parser.parse_args()

    # make address
    address = args.address.split(":")
    if len(address) == 1:  # only address
        args.port = 8080  # 80 requires special permissions, so use 8080 instead
    else:  # address:port
        args.address = address[0]
        args.port = int(address[1])

    return args
