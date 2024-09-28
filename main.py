import ssl
import asyncio
import logging.config
from src.logger import *
from src.status import *
from src.fileman import FileManager
from src.structures import Request, Response


class HTTPyServer:
    """
    Tiny HTTPy server
    """

    def __init__(
            self,
            port: int,
            certificate: str | None = None,
            private_key: str | None = None,
            enable_ssl: bool = False,
            allow_compression: bool = False,
            cache_everything: bool = False):
        # file manager (fileman)
        self.fileman: FileManager = FileManager(
            allow_compression=allow_compression,
            cache_everything=cache_everything,
            logger=logging.getLogger())
        self.fileman.update_paths()

        # sockets
        self.server: asyncio.Server | None = None
        self.port: int = port
        self.ctx: ssl.SSLContext | None = None
        if enable_ssl:
            self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER, check_hostname=False)
            self.ctx.load_cert_chain(certfile=certificate, keyfile=private_key)

        # signaling
        from signal import signal, SIGINT
        signal(SIGINT, self.stop)

    def start(self) -> None:
        """
        Starts the HTTPy server
        """

        asyncio.run(self._start())

    async def _start(self) -> None:
        """
        HTTPy server starting coro
        """

        self.server = await asyncio.start_server(
            client_connected_cb=self.client_handle,
            host=Config.SOCKET_BIND_ADDRESS,
            port=self.port,
            ssl=self.ctx)

        logging.info(f"Server running on '{Config.SOCKET_BIND_ADDRESS}:{self.port}'")
        async with self.server:
            try:
                await self.server.serve_forever()
            except asyncio.exceptions.CancelledError:
                pass
        logging.info("Server stopped.")

    def stop(self, *args) -> None:
        """
        HTTPy server stopping coro
        """

        if self.server is None:
            raise Exception("Cannot stop not started server")
        self.server.close()

    async def client_handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handles client connection
        :param reader: asyncio.StreamReader
        :param writer: asyncio.StreamWriter
        """

        # fetch request
        request = await self.receive_request(reader)
        if request is None:
            return

        # process request
        if request.type == "GET":
            response = self._handle_get(request)
        else:
            response = Response(data=b'Not implemented :<', status=STATUS_CODE_NOT_IMPLEMENTED)

        # modify response
        response.headers["Connection"] = "close"

        # send response
        for chunk in response.get_data_stream():
            writer.write(chunk)
            await writer.drain()

        # close writer
        writer.close()

    def _handle_get(self, request: Request) -> Response:
        """
        Handles GET requests
        :param request: client's request
        :return: response to request
        """

        # supported compressions
        encodings = [x.strip() for x in getattr(request, "Accept-Encoding", "").split(",")]

        if self.fileman.exists(request.path):
            container = self.fileman.get_container(request.path)
            headers = {"Content-Type": container.uncompressed.filetype, "Content-Length": container.uncompressed.size}
            data_stream = container.uncompressed.get_data_stream()
            if container.compressed:
                if "br" in encodings:  # brotli encoding (preferred)
                    headers["Content-Encoding"] = "br"
                    headers["Content-Length"] = container.brotli_compressed.size
                    data_stream = container.brotli_compressed.get_data_stream()
                elif "gzip" in encodings:  # gzip encoding
                    headers["Content-Encoding"] = "gzip"
                    headers["Content-Length"] = container.gzip_compressed.size
                    data_stream = container.gzip_compressed.get_data_stream()
            return Response(
                data_stream=data_stream,
                status=STATUS_CODE_OK,
                headers=headers)
        else:
            error = self.fileman.get_container("/err/response").uncompressed.get_full_data().decode("utf-8")
            error = error.format(
                status_code="404 Not Found",
                error_message=f"Page at '{request.path[1:]}' not found :<")
            return Response(
                data=error.encode("utf-8"),
                status=STATUS_CODE_NOT_FOUND)

    @staticmethod
    async def receive_request(reader: asyncio.StreamReader) -> Request:
        """
        Receives clients request
        :param reader: connection reader
        :return: request
        """

        buffer = bytearray()
        while data := await reader.read(Config.SOCKET_RECV_SIZE):
            buffer += data
            if buffer[-4:] == b'\r\n\r\n':
                return Request(buffer)
            if len(buffer) > Config.HTTP_MAX_RECV_SIZE or len(data) == 0:
                break


def parse_args():
    """
    Parses terminal arguments
    :return: args
    """

    from argparse import ArgumentParser

    # parser
    _parser = ArgumentParser(
        prog="httpy",
        description="https web server")

    # add arguments
    _parser.add_argument("-p", "--port",
                         help="binding port",
                         type=int,
                         required=True)
    _parser.add_argument("-c", "--certificate",
                         help="SSL certificate (or fullchain.pem)")
    _parser.add_argument("-k", "--private-key",
                         help="SSL private key")
    _parser.add_argument("--enable-ssl",
                         help="SSL for HTTPs encrypted connection (default False)",
                         default=False,
                         action="store_true")
    _parser.add_argument("--allow-compression",
                         help="allows to compress configured files (default False)",
                         default=False,
                         action="store_true")
    _parser.add_argument("--cache-everything",
                         help="stores ALL files inside cache (including compressed ones) (default False)",
                         default=False,
                         action="store_true")
    # TODO: implement verbosity check
    # _parser.add_argument("-v", "--verbose",
    #                      help="verbose (default False)",
    #                      default=False,
    #                      action="store_true")
    # TODO: implement live update
    # _parser.add_argument("-lu", "--live-update",
    #                      help="updates files in real time (default False)",
    #                      default=False,
    #                      action="store_true")

    # parse arguments
    args = _parser.parse_args()
    if args.enable_ssl and (args.certificate is None or args.private_key is None):  # check SSL keys
        _parser.error("enabled SSL requires CERTIFICATE and PRIVATE_KEY arguments")

    # return args
    return args


def main():
    args = parse_args()
    httpy = HTTPyServer(
        port=args.port,
        certificate=getattr(args, "certificate", None),
        private_key=getattr(args, "private_key", None),
        enable_ssl=args.enable_ssl,
        allow_compression=args.allow_compression,
        cache_everything=args.cache_everything
    )
    httpy.start()


if __name__ == '__main__':
    main()
