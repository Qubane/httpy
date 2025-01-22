import os
import asyncio
import logging
from typing import Any
from collections.abc import Generator
from source.status import *
from source.classes import *
from source.exceptions import *
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

        response = Response(status=STATUS_CODE_NOT_FOUND)
        if request.type == RequestTypes.GET:
            if request.path in PathTree():
                # fetch page info
                page_class = PathTree.get(request.path)
                page_data = page_class.get_data(
                    locale=request.headers.get("Accept-Language"),
                    **request.query_args)
                response = Response(
                    data=page_data,
                    status=STATUS_CODE_OK)
        await response.write(self.writer)

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

    response = None
    try:
        await client.handle_client()
    except Exception as e:
        LOGGER.warning(f"Error occurred when handling client request:", exc_info=e)
        response = Response(status=STATUS_CODE_INTERNAL_SERVER_ERROR)

    # if there's an exception response
    if response:
        try:
            await response.write(writer)
        except Exception:  # I don't know what it raises
            pass

    client.close()
