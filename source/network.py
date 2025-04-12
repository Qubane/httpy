"""
Networking stuff
"""


import asyncio
from source.classes import Connection


async def fetch_request(con: Connection) -> Request:
    """
    Fetches request from a connection
    :param con: client connection
    :return: client request
    """
