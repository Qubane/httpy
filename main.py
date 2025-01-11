import ssl
import signal
import asyncio
import logging
import source.settings
import source.page_manager
from source.clients import client_callback


class HTTPyServer:
    """
    Tiny HTTPy server
    """

    def __init__(
            self,
            bind_address: tuple[str, int],
            ssl_keys: tuple[str, str] | None = None
    ):
        """
        :param bind_address: binding (address, port)
        :param ssl_keys: (certfile, keyfile) pair
        """

        self.logger: logging.Logger = logging.getLogger()

        self.server: asyncio.Server | None = None
        self.bind_address: tuple[str, int] = bind_address

        self.ctx: ssl.SSLContext | None = None
        if ssl_keys:
            self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER, check_hostname=False)
            self.ctx.load_cert_chain(certfile=ssl_keys[0], keyfile=ssl_keys[1])

        signal.signal(signal.SIGINT, self.stop)

    def run(self):
        """
        Starts the HTTPy server
        """

        async def coro():
            self.server = await asyncio.start_server(
                client_connected_cb=client_callback,
                host=self.bind_address[0],
                port=self.bind_address[1],
                ssl=self.ctx)

            self.logger.info(f"Server running on '{self.bind_address[0]}:{self.bind_address[1]}'")

            async with self.server:
                try:
                    await self.server.serve_forever()
                except asyncio.exceptions.CancelledError:
                    pass

            self.logger.info("Server stopped")

        asyncio.run(coro())

    def stop(self, *args):
        """
        Stops the HTTPy server
        """

        self.server.close()


def parse_args():
    """
    Parses terminal arguments
    :return: args
    """

    from argparse import ArgumentParser

    # parser
    parser = ArgumentParser(
        prog="httpy",
        description="https web server")

    # add arguments
    parser.add_argument("-p", "--port",
                        help="binding port",
                        type=int,
                        required=True)
    parser.add_argument("-c", "--certificate",
                        help="SSL certificate (or fullchain.pem)")
    parser.add_argument("-k", "--private-key",
                        help="SSL private key")
    # TODO: implement verbosity check
    # parser.add_argument("-v", "--verbose",
    #                     help="verbose (default False)",
    #                     default=False,
    #                     action="store_true")
    # TODO: implement live update
    # parser.add_argument("-lu", "--live-update",
    #                     help="updates files in real time (default False)",
    #                     default=False,
    #                     action="store_true")

    # parse arguments
    args = parser.parse_args()
    if args.enable_ssl and (args.certificate is None or args.private_key is None):  # check SSL keys
        parser.error("enabled SSL requires CERTIFICATE and PRIVATE_KEY arguments")

    # return args
    return args


def main():
    # args = parse_args()
    httpy = HTTPyServer(
        bind_address=("0.0.0.0", 80))
    httpy.run()


if __name__ == '__main__':
    source.settings.init()
    source.page_manager.PageManager.init()
    main()
