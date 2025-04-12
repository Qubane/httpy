"""
Classes definitions
"""


from io import BytesIO
from typing import Iterable
from dataclasses import dataclass, field


class Connection:
    """
    Connection wrapper
    """

    def __init__(self):
        ...


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

    status: int
    data: bytes | Iterable | BytesIO | None = None
    headers: dict[str, str] = field(default_factory=lambda: dict())
