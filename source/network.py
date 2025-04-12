"""
Networking stuff
"""


from source.classes import *
from source.options import *


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
