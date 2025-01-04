import os
import ssl
import signal
import asyncio
import logging


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
        if ssl_keys:
            self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER, check_hostname=False)
            self.ctx.load_cert_chain(certfile=ssl_keys[0], keyfile=ssl_keys[1])


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
    args = parse_args()
    httpy = HTTPyServer()


if __name__ == '__main__':
    main()
