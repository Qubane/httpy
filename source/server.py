"""
HTTPy server code
"""


import asyncio
from source.classes import *
from source.network import *
from source.exceptions import *
from source.status_codes import *


class ClientHandle:
    """
    Client handling class
    """

    def __init__(self, con: Connection):
        self.con: Connection = con

    async def handle(self) -> Response:
        """
        Handle the client
        :return: response to client
        """

        request = await fetch_request(self.con)

    def close(self) -> None:
        """
        Closes the handle
        """

        self.con.writer.close()


async def accept_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """
    Accepts the client connection
    :param reader: client reader
    :param writer: client writer
    """

    # make connection and client handle
    connection: Connection = Connection(reader, writer)
    client_handle: ClientHandle = ClientHandle(connection)

    # define response
    response: Response | None = None

    # try generating a response
    try:
        response = await client_handle.handle()

    # error handling for external (non-server related) problems
    except ExternalServerError as e:
        response = Response(status=e.status, data=e.status.message.encode("utf-8"))

    # error handling for internal problems
    except (Exception, InternalServerError) as e:
        # TODO: add logging
        response = Response(status=STATUS_CODE_INTERNAL_SERVER_ERROR)

    # try sending response
    try:
        await send_response(connection, response)
    except Exception:
        ...

    # close client handle
    client_handle.close()
