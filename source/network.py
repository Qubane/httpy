"""
Networking stuff
"""


import asyncio
from source.classes import *
from source.options import *
from source.exceptions import *


async def fetch_request(connection: Connection) -> Request:
    """
    Fetches request from a connection
    :param connection: client connection
    :return: client request
    """

    # try reading the header data of request
    try:
        initial_data = await connection.read(WRITE_BUFFER_SIZE)
    except (asyncio.IncompleteReadError, asyncio.LimitOverrunError) as e:
        raise HTTPRequestError(e)

    # get request type
    for check_type in HTTP_REQUEST_TYPES:
        if initial_data[:len(check_type)] == check_type:
            break

    # raise error in case of failure
    else:
        raise HTTPRequestTypeError("Failed to identify HTTP request type")


async def send_response(connection: Connection, response: Response) -> None:
    """
    Sends a response to a connection
    :param connection: connection
    :param response: response
    :return: none
    """

    # generate header data
    connection.write(b'HTTP/1.1 ' + response.status.__bytes__() + b'\r\n')
    for key, value in response.headers.items():
        connection.write(f'{key}: {value}\r\n'.encode("utf-8"))
    connection.write(b'\r\n')

    # write generic data
    if isinstance(response.data, bytes):
        connection.write(response.data)
    elif isinstance(response.data, Iterable):
        for data in response.data:
            connection.write(data)
            if connection.writer.transport.get_write_buffer_size() >= WRITE_BUFFER_SIZE:
                await connection.drain()
    elif isinstance(response.data, BytesIO):
        try:
            while data := response.data.read(WRITE_BUFFER_SIZE):
                connection.write(data)
                if connection.writer.transport.get_write_buffer_size() >= WRITE_BUFFER_SIZE:
                    await connection.drain()
        except Exception as e:
            response.data.close()
            raise e
    if connection.writer.transport.get_write_buffer_size() > 0:
        await connection.drain()
