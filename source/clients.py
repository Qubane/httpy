import asyncio
import logging
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
            if request.path in PathTree:
                # pick locale
                for lang_pair in request.headers["Accept-Language"]:
                    if lang_pair[0] in PathTree.get(request.path)["locales"]:
                        locale = lang_pair[0]
                        break
                else:  # force English
                    locale = "en"

                # find and format file path accordingly
                filepath = PathTree.get(request.path)["filepath"]
                filepath = filepath.format(prefix=locale)

                # open and make response
                file = open(filepath, "rb")
                response = Response(
                    data=file,
                    status=STATUS_CODE_OK)
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

    client.close()
