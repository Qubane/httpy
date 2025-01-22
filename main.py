import os
import ssl
import signal
import asyncio
import logging
import source.settings
import source.page_manager
from source.clients import client_callback
from source.http_to_https import TinyServer


LOGGER: logging.Logger = logging.getLogger()


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

        self.server: asyncio.Server | None = None
        self.bind_address: tuple[str, int] = bind_address

        self.ctx: ssl.SSLContext | None = None
        if ssl_keys and ssl_keys[0] and ssl_keys[1]:
            self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER, check_hostname=False)
            self.ctx.load_cert_chain(certfile=ssl_keys[0], keyfile=ssl_keys[1])

        signal.signal(signal.SIGINT, self.stop)

    def run(self):
        """
        Starts the HTTPy server
        """

        asyncio.run(self.run_coro())

    async def run_coro(self):
        """
        Starts the HTTPy server. Coroutine
        """

        self.server = await asyncio.start_server(
            client_connected_cb=client_callback,
            host=self.bind_address[0],
            port=self.bind_address[1],
            ssl=self.ctx)

        LOGGER.info(f"Server running on '{self.bind_address[0]}:{self.bind_address[1]}'")

        async with self.server:
            try:
                await self.server.serve_forever()
            except asyncio.exceptions.CancelledError:
                pass

        LOGGER.info("Server stopped")

    def stop(self, *args):
        """
        Stops the HTTPy server
        """

        self.server.close()
        for sock in self.server.sockets:
            sock.close()


def parse_args():
    """
    Parses terminal arguments
    :return: args
    """

    from argparse import ArgumentParser

    # parser
    parser = ArgumentParser(
        prog="HTTPy",
        description="HTTP python web server")

    # add arguments
    parser.add_argument("-a", "--address",
                        help="binding address:port",
                        required=True)
    parser.add_argument("-d", "--domain",
                        help="domain name",
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
        args.port = address[1]

    # make domain
    if args.domain[:8] != "https://":
        args.domain = f"https://{args.domain}"

    # return args
    return args


def main():
    args = parse_args()
    httpy = HTTPyServer(
        bind_address=(args.address, args.port),
        ssl_keys=(args.certificate, args.private_key))
    redirect = TinyServer(
        bind_address=(args.address, args.port+1),
        redirect=args.domain)

    async def coro():
        await asyncio.gather(
            httpy.run_coro(),
            redirect.run_coro())
    asyncio.run(coro())


if __name__ == '__main__':
    source.settings.init()
    source.page_manager.PageManager.init()
    main()
