import argparse


_parser = argparse.ArgumentParser(
    prog="httpy",
    description="https web server")
_parser.add_argument("-p", "--port",
                     help="binding port (default 13700)",
                     type=int,
                     default=13700)
_parser.add_argument("-c", "--certificate",
                     help="certificate (or fullchain.pem)")
_parser.add_argument("-k", "--private-key",
                     help="private key")
_parser.add_argument("--compress-path",
                     help="enables pre-compression of files in 'www' folder (default False)",
                     default=False,
                     action="store_true")
_parser.add_argument("--enable-ssl",
                     help="SSL for HTTPs encrypted connection (default False)",
                     default=False,
                     action="store_true")
_parser.add_argument("-v", "--verbose",
                     help="verbose (default False)",
                     default=False,
                     action="store_true")
_parser.add_argument("-lu", "--live-update",
                     help="verbose (default False)",
                     default=False,
                     action="store_true")
ARGS = _parser.parse_args()
if ARGS.enable_ssl and (ARGS.certificate is None or ARGS.private_key is None):
    _parser.error("enabled SSL requires CERTIFICATE and PRIVATE_KEY arguments")