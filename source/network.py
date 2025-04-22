"""
Networking stuff
"""


import re
import asyncio
from source.classes import *
from source.options import *
from source.exceptions import *


def _parse_http_header(header: Header) -> QualityHeader:
    """
    Parses HTTP header data
    :param header: header
    :return: QualityHeader
    """

    header_parts = header.data.split(',')

    # decode
    decoded_header: dict[str, float] = {}
    for part in header_parts:
        part = part.strip()

        # check if part has quality
        if ';' in part:
            media_type, quality_str = part.split(';', maxsplit=1)
            try:
                quality_value = float(quality_str.split('=', maxsplit=1)[1])
            except ValueError:  # if not float, just use string
                quality_value = quality_str

        # if part doesn't, assign 1.0 as quality
        else:
            media_type = part
            quality_value = 1.0

        # add part of header
        decoded_header[media_type.strip()] = quality_value

    # return
    return QualityHeader(decoded_header)


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

    # empty request
    if initial_data == b'':
        raise ExternalServerError

    # get request type
    for request_type in HTTP_REQUEST_TYPES:
        if initial_data[:len(request_type)] == request_type:
            break

    # raise error in case of failure
    else:
        raise HTTPRequestTypeError(f"Failed to identify HTTP request type: {initial_data[:64]}")

    # fetch request path
    request_path = initial_data[len(request_type)+1:initial_data.find(b' ', len(request_type)+1, 255)]

    # split path to path and query args
    request_spit = request_path.split(b'?', maxsplit=1)
    request_path, request_args = request_spit if len(request_spit) == 2 else (request_spit[0], b'')
    request_path = request_path.decode("utf-8", "ignore")

    # make query args
    request_args = [x for x in request_args.split(b'&', maxsplit=1) if x]
    for idx, query_arg in enumerate(request_args):
        try:
            query_arg = query_arg.decode("utf-8", "ignore").split("=", maxsplit=1)
            if len(query_arg) != 2:
                continue
            request_args[idx] = query_arg
        except Exception:
            pass
    request_args = {x[0]: x[1] for x in request_args}

    # headers
    request_headers = dict()
    for raw_header in re.findall(r"\n(.*:.*)", initial_data.decode("ascii")):
        raw_header = raw_header.split(":", maxsplit=1)
        if len(raw_header) != 2:
            continue
        request_headers[raw_header[0].lower()] = Header(raw_header[1].strip())

    # parse commonly used headers
    for header_name in ["accept", "accept-encoding", "accept-language"]:
        if header_name in request_headers:
            request_headers[header_name] = _parse_http_header(request_headers[header_name])

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
        connection.write(f'{key}: {value.data}\r\n'.encode("utf-8"))
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
