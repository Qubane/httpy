import asyncio
from dataclasses import dataclass
from collections.abc import Generator
from source.settings import READ_BUFFER_SIZE, MAX_QUERY_ARGS


class RequestTypes:
    GET = b'GET'
    HEAD = b'HEAD'
    POST = b'POST'
    PUT = b'PUT'
    DELETE = b'DELETE'
    CONNECT = b'CONNECT'
    OPTIONS = b'OPTIONS'
    TRACE = b'TRACE'
    PATCH = b'PATCH'

    ALL = [GET, HEAD, POST, PUT, DELETE, CONNECT, OPTIONS, TRACE, PATCH]


@dataclass(frozen=True)
class Request:
    """
    Client HTTP request
    """

    type: str
    path: str
    query_args: dict[str, str]
    data_stream: Generator[bytes, None, None] | None = None

    @staticmethod
    async def get(reader: asyncio.StreamReader):
        """
        Gets request from reader
        :param reader: client connection
        :return: request class
        """

        data = await reader.read(READ_BUFFER_SIZE)

        # request type
        for rtype in RequestTypes.ALL:
            if data[:len(rtype)] == rtype:
                break
        else:
            raise Exception

        # raw request path
        raw_rpath = data[len(rtype)+1:data.find(b' ', len(rtype)+1, 255)]

        # request path
        path_split = raw_rpath.split(b'?', 1)
        rpath = path_split[0]

        # query args
        query_args = dict()
        raw_query_args = path_split[1] if len(path_split) == 2 else b''
        for raw_arg in raw_query_args.split(b'&', MAX_QUERY_ARGS):
            if len(raw_arg := raw_arg.split(b'=', 1)) == 2:
                query_args[raw_arg[0].decode("ascii")] = raw_arg[1].decode("utf-8")

        print(rtype, rpath, query_args)
