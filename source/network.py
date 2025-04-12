"""
Networking stuff
"""


from source.classes import *


async def fetch_request(con: Connection) -> Request:
    """
    Fetches request from a connection
    :param con: client connection
    :return: client request
    """


async def send_response(con: Connection, response: Response) -> None:
    """
    Sends a response to a connection
    :param con: connection
    :param response: response
    :return: none
    """
