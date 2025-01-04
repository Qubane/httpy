import logging
import asyncio


class ClientHandler:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader: asyncio.StreamReader = reader
        self.writer: asyncio.StreamWriter = writer

    async def handle_client(self):
        """
        Handles the client's request
        """


async def accept_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> ClientHandler:
    """
    Accepts the client connection
    :param reader: asyncio server callback
    :param writer: asyncio server callback
    :return: Client handle
    """

    return ClientHandler(reader, writer)
