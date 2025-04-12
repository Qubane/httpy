"""
Classes definitions
"""


import asyncio
from io import BytesIO
from typing import Iterable
from dataclasses import dataclass, field
from source.status_codes import *


@dataclass(frozen=True)
class Connection:
    """
    Connection wrapper
    """

    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter


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
