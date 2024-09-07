from typing import Any
from collections.abc import Generator
from src.config import *
from src.status_code import StatusCode


class Request:
    """
    Just a request
    """

    def __init__(self):
        self.type: str = ""
        self.path: str = ""
        self.path_args: dict[str, str | None] = dict()

    @staticmethod
    def construct(raw_request: bytes):
        """
        Constructs request for raw bytes
        :param raw_request: bytes of request
        :return: Request | None
        """

        request = Request()

        # get type
        index = raw_request.find(b' ', 0, 10)
        if index == -1:
            return None
        request.type = raw_request[:index].decode("ascii")

        # get path
        index = raw_request.find(b' ', len(request.type)+1, PATH_MAX_LENGTH+len(request.type))
        if index == -1:
            return None
        raw_path = raw_request[len(request.type)+1:index].decode("ascii")
        q_split = raw_path.split("?", maxsplit=1)
        request.path = q_split[0]

        # get args
        raw_args = q_split[1] if len(q_split) == 2 else ""
        for raw_arg in raw_args.split("&", maxsplit=PATH_ARGS_MAX_COUNT):
            split = raw_arg.split("=", maxsplit=1)
            if len(split) == 2:                         # if there is a key value pair present
                request.path_args[split[0]] = split[1]
            elif len(split) == 1 and split[0] != "":    # if there is only a key present (and it's a valid key)
                request.path_args[split[0]] = None

        # get headers
        header_data = raw_request.split(b'\r\n', maxsplit=PATH_HEADER_MAX_COUNT)
        for raw_header in header_data:
            if len(pair := raw_header.decode("utf8").split(":", maxsplit=1)) == 2:
                key, val = pair
                val = val.strip()

                # check attribute
                if key in request.__dict__:
                    return None

                # set attribute to key value pair
                setattr(request, key, val)

        return request

    def __str__(self):
        return '\n'.join([f"{key}: {val}" for key, val in self.__dict__.items()])


class Response:
    """
    Server response
    """

    def __init__(self, data: bytes, status: StatusCode, headers: dict[str, Any] = None, **kwargs):
        """

        :param data: response data
        :param status: response status code
        :param headers: headers to include
        :key compress: compress data or not
        :key data_stream: stream of data
        """

        self.data: bytes = data
        self.data_stream: Generator[bytes, None, None] | None = kwargs.get("data_stream")
        self.status: StatusCode = status
        self.headers: dict[str, Any] = headers if headers is not None else dict()

        # # check for content-length when using data_stream
        # if self.data_stream is not None and self.headers.get("Content-Length") is None:
        #     raise Exception("Undefined length for data stream")

    def get_data_stream(self):
        if self.data_stream is None:
            def generator() -> bytes:
                for i in range(0, len(self.data), BUFFER_LENGTH):
                    yield self.data[i:i+BUFFER_LENGTH]
            return generator()
        else:
            return self.data_stream
