import logging
import asyncio
from source.status import *
from source.classes import Request, Response


class ClientHandler:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader: asyncio.StreamReader = reader
        self.writer: asyncio.StreamWriter = writer

    async def handle_client(self) -> None:
        """
        Handles the client's request
        """

        request = await Request.read(self.reader)

        response = Response(b'hello :)', STATUS_CODE_OK)
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

    try:
        await client.handle_client()
    except Exception as e:
        logging.warning(f"Error occurred when handling client request:", exc_info=e)

    client.close()
