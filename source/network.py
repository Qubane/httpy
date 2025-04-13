"""
Networking stuff
"""


import asyncio
from source.classes import *
from source.options import *
from source.exceptions import *


async def fetch_request(con: Connection) -> Request:
    """
    Fetches request from a connection
    :param con: client connection
    :return: client request
    """

    # try reading the header data of request
    try:
        initial_data = await con.reader.read(WRITE_BUFFER_SIZE)
    except (asyncio.IncompleteReadError, asyncio.LimitOverrunError) as e:
        raise HTTPRequestError(e)

    # get request type
    for check_type in HTTP_REQUEST_TYPES:
        if initial_data[:len(check_type)] == check_type:
            break

    # raise error in case of failure
    else:
        raise HTTPRequestTypeError("Failed to identify HTTP request type")

    print(initial_data)


async def send_response(con: Connection, response: Response) -> None:
    """
    Sends a response to a connection
    :param con: connection
    :param response: response
    :return: none
    """

    con.writer.write(b'HTTP/1.1 ' + response.status.__bytes__() + b'\r\n')
    for key, value in response.headers.items():
        con.writer.write(f'{key}: {value}\r\n'.encode("utf-8"))
    con.writer.write(b'\r\n')

    if isinstance(response.data, bytes):
        con.writer.write(response.data)
    elif isinstance(response.data, Iterable):
        for data in response.data:
            con.writer.write(data)
            if con.writer.transport.get_write_buffer_size() >= WRITE_BUFFER_SIZE:
                await con.writer.drain()
    elif isinstance(response.data, BytesIO):
        try:
            while data := response.data.read(WRITE_BUFFER_SIZE):
                con.writer.write(data)
                if con.writer.transport.get_write_buffer_size() >= WRITE_BUFFER_SIZE:
                    await con.writer.drain()
        except Exception as e:
            response.data.close()
            raise e
    if con.writer.transport.get_write_buffer_size() > 0:
        await con.writer.drain()
