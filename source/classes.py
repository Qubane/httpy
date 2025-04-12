"""
Classes definitions
"""


from typing import Iterable
from dataclasses import dataclass


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
