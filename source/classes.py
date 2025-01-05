import asyncio
from dataclasses import dataclass, field
from collections.abc import Generator


@dataclass(frozen=True)
class Request:
    """
    Client HTTP request
    """

    type: str
    path: str
    query_args: dict[str, str] = field(default_factory=lambda: dict())
    data_stream: Generator[bytes, None, None] | None = None

    @staticmethod
    async def get(reader: asyncio.StreamReader):
        """
        Gets request from reader
        :param reader: client connection
        :return: request class
        """
