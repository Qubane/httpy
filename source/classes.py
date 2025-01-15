import re
import asyncio
from io import BytesIO
from collections.abc import Iterable
from dataclasses import dataclass, field
from source.status import StatusCode
from source.settings import READ_BUFFER_SIZE, WRITE_BUFFER_SIZE, MAX_QUERY_ARGS


def parse_accept_language(header_val: str) -> list[tuple[str, float]]:
    """
    Parses 'Accept-Language' header in request
    :param header_val: header value
    :return: list of tuples of accepted languages
    """

    langs = header_val.split(",")
    locale_q_pairs = []

    for lang in langs:
        if (lang_pair := lang.split(";")[0]) == lang:
            locale_q_pairs.append((lang.strip(), 1))
        else:
            locale = lang_pair[0].strip()
            q = float(lang_pair[1].split("=")[1])
            locale_q_pairs.append((locale, q))
    return locale_q_pairs


class RequestTypes:
    GET = 'GET'
    HEAD = 'HEAD'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    CONNECT = 'CONNECT'
    OPTIONS = 'OPTIONS'
    TRACE = 'TRACE'
    PATCH = 'PATCH'

    ALL = [GET, HEAD, POST, PUT, DELETE, CONNECT, OPTIONS, TRACE, PATCH]
    RAW_ALL = [x.encode("ascii") for x in ALL]


@dataclass(frozen=True)
class Request:
    """
    Client HTTP request
    """

    type: str
    path: str
    query_args: dict[str, str]
    headers: dict[str, str]
    data_stream: Iterable | None = None

    @staticmethod
    async def read(reader: asyncio.StreamReader):
        """
        Reads request from client's stream
        :param reader: client connection
        :return: request class
        """

        data = await reader.read(READ_BUFFER_SIZE)

        # request type
        for rtype in RequestTypes.RAW_ALL:
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

        if "Accept-Language" in rheaders:
            try:
                rheaders["Accept-Language"] = parse_accept_language(rheaders["Accept-Language"])
            except Exception:
                rheaders["Accept-Language"] = [("en", 1)]

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

    status: StatusCode
    data: bytes | Iterable | BytesIO | None = None
    headers: dict[str, str] = field(default_factory=lambda: dict())

    async def write(self, writer: asyncio.StreamWriter):
        """
        Writes response to client stream
        :param writer: client stream
        """

        writer.write(b'HTTP/1.1 ' + self.status.__bytes__() + b'\r\n')
        for key, value in self.headers.items():
            writer.write(f"{key}: {value}\r\n".encode("utf-8"))
        writer.write(b'\r\n')

        if isinstance(self.data, bytes):
            writer.write(self.data)
        elif isinstance(self.data, Iterable):
            for data in self.data:
                writer.write(data)
                if writer.transport.get_write_buffer_size() >= WRITE_BUFFER_SIZE:
                    await writer.drain()
        elif isinstance(self.data, BytesIO):
            while data := self.data.read(WRITE_BUFFER_SIZE):
                writer.write(data)

        if writer.transport.get_write_buffer_size() > 0:
            await writer.drain()
