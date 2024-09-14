"""
HTTPy server basic structures
"""


from ssl import SSLSocket
from socket import socket
from collections.abc import Generator
from src.config import Config
from src.status import StatusCode, STATUS_CODE_NOT_FOUND, STATUS_CODE_OK


unified_socket = SSLSocket | socket


class Request:
    """
    HTTP request
    """

    def __init__(self, raw_http: bytes):
        self._type: str = ""
        self._path: str = ""
        self._path_args: dict[str, str] = dict()

        self._construct(raw_http)

    def _construct(self, raw_http: bytes) -> None:
        """
        Constructs self from raw http data
        """

        # get type
        index = raw_http.find(b' ', 0, 10)
        if index == -1:
            return None
        self._type = raw_http[:index].decode("ascii")

        # get path
        index = raw_http.find(b' ', len(self._type) + 1, Config.HTTP_MAX_PATH_LENGTH + len(self._type))
        if index == -1:
            return None
        raw_path = raw_http[len(self._type) + 1:index].decode("ascii")
        q_split = raw_path.split("?", maxsplit=1)
        self._path = q_split[0]

        # get args
        raw_args = q_split[1] if len(q_split) == 2 else ""
        for raw_arg in raw_args.split("&", maxsplit=Config.HTTP_MAX_ARG_NUMBER):
            split = raw_arg.split("=", maxsplit=1)
            if len(split) == 2:  # if there is a key value pair present
                self._path_args[split[0]] = split[1]

        # get headers
        header_data = raw_http.split(b'\r\n', maxsplit=Config.HTTP_MAX_HEADER_NUMBER)
        for raw_header in header_data:
            if len(pair := raw_header.decode("utf8").split(":", maxsplit=1)) == 2:
                key, val = pair
                val = val.strip()

                # check attribute
                if key in self.__dict__:
                    return None

                # set attribute to key value pair
                setattr(self, key, val)

    @property
    def type(self) -> str:
        return self._type

    @property
    def path(self) -> str:
        return self._path

    @property
    def args(self) -> dict[str, str]:
        return self._path_args

    def __str__(self) -> str:
        return '\n'.join([f"{key}: {val}" for key, val in self.__dict__.items()])


class Response:
    """
    HTTP response
    """

    def __init__(
            self,
            data: bytes | None = None,
            data_stream: Generator[bytes, None, None] | None = None,
            status: StatusCode | None = None,
            headers: dict[str, str] | None = None):
        self.data: bytes | None = data
        self._data_stream: Generator[bytes, None, None] | None = data_stream
        self._status: StatusCode | None = status
        self.headers: dict[str, str] | None = headers if headers else dict()

        if self.data is None and self._data_stream is None:  # data not present
            self._status = STATUS_CODE_NOT_FOUND
        elif self._status is None:  # data present, but no status code
            self._status = STATUS_CODE_OK

    def get_data_stream(self) -> Generator[bytes, None, None]:
        msg = b'HTTP/1.1 ' + self._status.__bytes__() + b'\r\n'
        for key, val in self.headers.items():
            msg += f"{key}: {val}\r\n".encode("utf-8")
        yield msg + b'\r\n'
        if self._data_stream is not None:
            for val in self._data_stream:
                yield val
        elif self.data is not None:
            for i in range(0, len(self.data), Config.SOCKET_SEND_SIZE):
                yield self.data[i:i + Config.SOCKET_SEND_SIZE]

    @property
    def status(self) -> StatusCode:
        return self._status

    def __str__(self) -> str:
        return '\n'.join([f"{key}: {val}" for key, val in self.__dict__.items()])
