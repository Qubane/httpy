import os
import ssl
import asyncio
import logging


class HTTPyServer:
    """
    Tiny HTTPy server
    """

    def __init__(
            self,
    ):
        pass


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
    parser.add_argument("--enable-ssl",
                        help="SSL for HTTPs encrypted connection (default False)",
                        default=False,
                        action="store_true")
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
