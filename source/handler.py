"""
HTTPy client handling code
"""


import os
import glob
import asyncio
from source.server import *
from source.classes import *
from source.network import *
from source.exceptions import *
from source.status_codes import *


class ClientHandle:
    """
    Client handling class
    """

    server: Server | None = None

    def __init__(self, connection: Connection):
        self.connection: Connection = connection

    async def handle(self) -> Response:
        """
        Handle the client
        :return: response to client
        """

        request = await fetch_request(self.connection)
        response = await self.server.process_request(request)

        response.headers["server"] = Header("HTTPy")

        return response

    def close(self) -> None:
        """
        Closes the handle
        """

        self.connection.close()


async def accept_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """
    Accepts the client connection
    :param reader: client reader
    :param writer: client writer
    """

    # make connection and client handle
    connection: Connection = Connection(reader, writer)
    client_handle: ClientHandle = ClientHandle(connection)

    # try generating a response
    try:
        response = await client_handle.handle()

    # error handling for external (non-server related) problems
    except ExternalServerError as e:
        response = Response(status=e.status, data=e.status.message.encode("utf-8"))

    # error handling for internal problems
    except (Exception, InternalServerError) as e:
        LOGGER.warning(f"Error occurred while processing client response", exc_info=e)
        response = Response(status=STATUS_CODE_INTERNAL_SERVER_ERROR)

    # try sending response
    try:
        await send_response(connection, response)
    except Exception:
        pass

    # close client handle
    client_handle.close()


async def accept_http_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """
    Accepts the client connection
    :param reader: client reader
    :param writer: client writer
    """

    # make connection
    connection: Connection = Connection(reader, writer)

    # define request as dummy
    request = Request("GET", "nothing", dict(), dict())

    # fetch request
    try:
        request = await fetch_request(connection)

    # error handling for external (non-server related) problems
    except ExternalServerError as e:
        pass

    # error handling for internal problems
    except (Exception, InternalServerError) as e:
        LOGGER.warning(f"Error occurred while processing client response", exc_info=e)

    # try fetching a page
    page = ClientHandle.server.get_path(request.path)

    # TODO: make proper redirects
    redirect = "https://qubane.ru/"

    # if page is not found
    if hasattr(page, "__secret__"):
        # make secret response
        response = Response(
            status=STATUS_CODE_OK,
            data=getattr(page, "__secret__"))
    else:
        # make redirect response
        response = Response(
            status=STATUS_CODE_MOVED_PERMANENTLY,
            data=f"Moved Permanently. Redirecting to {redirect}".encode("ascii"),
            headers={"location": Header(redirect)})

    # try sending response
    try:
        await send_response(connection, response)
    except Exception:
        pass


def initialize_client_handle() -> None:
    """
    Initializes ClientHandle server attribute.
    """

    # create instance of server
    if ClientHandle.server is None:
        ClientHandle.server = Server()

    # import pages
    for file in glob.glob(f"{WWW_DIRECTORY}/**/*", recursive=True):
        # skip all non-files
        if not os.path.isfile(file):
            continue

        # skip all non-py files
        if os.path.splitext(file)[1] != ".py":
            continue

        filepath = file.replace("\\", "/")
        module_path = os.path.splitext(filepath)[0].replace("/", ".")
        ClientHandle.server.import_page(module_path)
