"""
Classes definitions
"""


import asyncio
from io import BytesIO
from typing import Iterable, Coroutine, Any
from dataclasses import dataclass, field
from source.status_codes import *


HTTP_REQUEST_TYPES: list[bytes] = [
    b'GET',
    b'HEAD',
    b'OPTIONS',
    b'TRACE',
    b'PUT',
    b'DELETE',
    b'POST',
    b'PATCH',
    b'CONNECT']


@dataclass(frozen=True)
class Connection:
    """
    Connection wrapper
    """

    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    def write(self, *args, **kwargs) -> None:
        return self.writer.write(*args, **kwargs)

    async def drain(self, *args, **kwargs) -> None:
        return await self.writer.drain()

    def read(self, *args, **kwargs) -> Coroutine[Any, Any, bytes]:
        return self.reader.read(*args, **kwargs)

    def close(self, *args, **kwargs) -> None:
        return self.writer.close()


@dataclass(frozen=True)
class Header:
    """
    Generic header container
    """

    data: str


@dataclass(frozen=True)
class QualityHeader(Header):
    """
    Generic header container, that gets basic parsing
    """

    data: dict[str, float]


@dataclass(frozen=True)
class Request:
    """
    Client's HTTP request
    """

    type: str
    path: str
    query_args: dict[str, str]
    headers: dict[str, Header]
    data_stream: Iterable | None = None


@dataclass(frozen=True)
class Response:
    """
    HTTP response to client
    """

    status: StatusCode = STATUS_CODE_INTERNAL_SERVER_ERROR
    data: str | bytes | Iterable | BytesIO | None = None
    headers: dict[str, Header] = field(default_factory=lambda: dict())


class Page:
    """
    Page class
    """

    async def on_request(self, request: Request) -> Response:
        """
        Event that gets called when the user requests that page
        :param request: client request
        :return: server response
        """

        raise NotImplementedError
