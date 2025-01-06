import re
import asyncio
from collections.abc import Generator
from dataclasses import dataclass, field
from source.settings import READ_BUFFER_SIZE, MAX_QUERY_ARGS
from source.status import StatusCode, STATUS_CODE_INTERNAL_SERVER_ERROR


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
    headers: dict[str, str]
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
        rquery_args = dict()
        raw_query_args = path_split[1] if len(path_split) == 2 else b''
        for raw_arg in raw_query_args.split(b'&', MAX_QUERY_ARGS):
            if len(raw_arg := raw_arg.split(b'=', 1)) == 2:
                rquery_args[raw_arg[0].decode("ascii")] = raw_arg[1].decode("utf-8")

        # headers
        rheaders = dict()
        for raw_header in re.findall(r"\r\n(.*:.*)\r\n", data.decode("ascii")):
            raw_header = raw_header.split(": ")
            rheaders[raw_header[0]] = raw_header[1]

        # data
        # TODO: make data streams

        return Request(
            type=rtype.decode("ascii"),
            path=rpath.decode("utf-8"),
            query_args=rquery_args,
            headers=rheaders)


@dataclass(frozen=True)
class Response:
    """
    Server HTTP response
    """

    data: bytes | Generator[bytes, None, None] | None
    status: StatusCode
    headers: dict[str, str]
