"""
Networking stuff
"""


import re
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
    for request_type in HTTP_REQUEST_TYPES:
        if initial_data[:len(request_type)] == request_type:
            break

    # raise error in case of failure
    else:
        raise HTTPRequestTypeError("Failed to identify HTTP request type")

    # fetch request path
    request_path = initial_data[len(request_type)+1:initial_data.find(b' ', len(request_type)+1, 255)]

    # split path to path and query args
    request_spit = request_path.split(b'?', maxsplit=1)
    request_path, request_args = request_spit if len(request_spit) == 2 else (request_spit[0], b'')
    request_path = request_path.decode("utf-8", "ignore")

    # make query args
    request_args = [x for x in request_args.split(b'&') if x]
    for idx, query_arg in enumerate(request_args):
        try:
            request_args[idx] = query_arg.decode("utf-8", "ignore").split("=")
        except Exception:
            pass
    request_args = {x[0]: x[1] for x in request_args}

    # headers
    request_headers = dict()
    for raw_header in re.findall(r"\r\n(.*:.*)\r\n", initial_data.decode("ascii")):
        raw_header = raw_header.split(": ")
        request_headers[raw_header[0].lower()] = raw_header[1]

    # return request
    return Request(
        request_type.decode("ascii"),
        request_path,
        request_args,
        request_headers)


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
    elif isinstance(response.data, str):
        connection.write(response.data.encode("utf-8"))
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
