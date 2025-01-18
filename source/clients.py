import asyncio
import logging
from typing import Any
from collections.abc import Generator
from source.status import *
from source.classes import *
from source.page_manager import PageManager, PathTree


LOGGER: logging.Logger = logging.getLogger(__name__)


class ClientHandler:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader: asyncio.StreamReader = reader
        self.writer: asyncio.StreamWriter = writer

    async def handle_client(self) -> None:
        """
        Handles the client's request
        """

        request = await Request.read(self.reader)

        LOGGER.debug(request)

        file = None
        response = Response(status=STATUS_CODE_NOT_FOUND)
        if request.type == RequestTypes.GET:
            if request.path in PathTree():
                # fetch page info
                page_info = PathTree.get(request.path)

                # pick locale
                for lang_pair in request.headers["Accept-Language"]:
                    if lang_pair[0] in page_info["locales"]:
                        locale = lang_pair[0]
                        break
                else:  # force English
                    locale = "en"

                if page_info["filepath"] is not None:  # normal file
                    # find and format file path accordingly
                    filepath = page_info["filepath"]
                    filepath = filepath.format(prefix=locale)

                    # open and make response
                    file = open(filepath, "rb")
                    response = Response(
                        data=file,
                        status=STATUS_CODE_OK)
                else:  # request
                    page: Generator[bytes, Any, None] = page_info["script"].make_page(
                        locale=locale,
                        request=request)

                    response = Response(
                        data=page,
                        status=STATUS_CODE_NOT_IMPLEMENTED)
        try:
            await response.write(self.writer)
        except Exception as e:
            # if file was open, close it
            if file:
                file.close()
            raise e

    def close(self) -> None:
        """
        Closes client connection
        """

        self.writer.close()


async def client_callback(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """
    Accepts the client connection
    :param reader: asyncio server callback
    :param writer: asyncio server callback
    :return: Client handle
    """

    client = ClientHandler(reader, writer)

    try:
        await client.handle_client()
    except Exception as e:
        LOGGER.warning(f"Error occurred when handling client request:", exc_info=e)
        try:
            await Response(status=STATUS_CODE_INTERNAL_SERVER_ERROR).write(writer)
        except Exception:  # I don't know what it could raise
            pass

    client.close()
