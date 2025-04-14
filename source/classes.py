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

    async def drain(self, *args, **kwargs) -> Coroutine[Any, Any, None]:
        return self.writer.drain()

    def read(self, *args, **kwargs) -> Coroutine[Any, Any, bytes]:
        return self.reader.read(*args, **kwargs)

    def close(self, *args, **kwargs) -> None:
        return self.writer.close()


@dataclass(frozen=True)
class Request:
    """
    Client's HTTP request
    """

    type: str
    path: str
    query_args: dict[str, str]
    headers: dict[str, str]
    data_stream: Iterable | None = None


@dataclass(frozen=True)
class Response:
    """
    HTTP response to client
    """

    status: StatusCode = STATUS_CODE_INTERNAL_SERVER_ERROR
    data: bytes | Iterable | BytesIO | None = None
    headers: dict[str, str] = field(default_factory=lambda: dict())


class ServerStub:
    """
    Server stub class
    """

    def add_path(self, path: str, page: "Page") -> None:
        """
        Adds path to path tree
        :param path: path to add
        :param page: page class reference
        """

        raise NotImplementedError


class Page:
    """
    Page class
    """

    def __init__(self, server: ServerStub):
        ...
