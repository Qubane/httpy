import asyncio
import logging
from source.status import *
from source.page_manager import PageManager
from source.classes import Request, Response


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

        if request.path in PageManager.path_tree:
            filepath = PageManager.get(request.path)["filepath"]
            filepath = filepath.format(prefix="en")  # temporary

            with open(filepath, "rb") as file:
                await Response(
                    data=file,
                    status=STATUS_CODE_OK).write(self.writer)
        else:
            await Response(status=STATUS_CODE_NOT_FOUND).write(self.writer)

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

    client.close()
