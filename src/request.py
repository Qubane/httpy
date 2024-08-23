from typing import Any
from ssl import SSLSocket
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
    def create(raw_request: bytes):
        """
        Creates self class from raw request
        :param raw_request: bytes
        :return: self
        """

        # new request
        request = Request()

        # change type and path
        request.type = raw_request[:raw_request.find(b' ')].decode("ascii")
        raw_path = raw_request[len(request.type)+1:raw_request.find(b' ', len(request.type)+1)].decode("ascii")

        # remove path args from path
        request.path = raw_path.split("?")[0]

        # decode path args
        raw_args = raw_path.split("/")[-1].split("?")
        raw_args = raw_args[1] if len(raw_args) == 2 else ""
        for raw_arg in raw_args.split("&"):
            split = raw_arg.split("=")

            # if there is a key value pair present
            if len(split) == 2:
                request.path_args[split[0]] = split[1]

            # if there is only a key present (and it's a valid key)
            elif len(split) == 1 and split[0] != "":
                request.path_args[split[0]] = None

        # decode headers
        for raw_header in raw_request.split(b'\r\n'):
            if len(pair := raw_header.decode("ascii").split(":")) == 2:
                key, val = pair
                val = val.strip()

                # set attribute to key value pair
                setattr(request, key, val)

        # return request
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
        :param kwarg: compress - whether to compress data or not
        """

        self.data: bytes = data
        self.status: StatusCode = status
        self.headers: dict[str, Any] = headers if headers is not None else dict()
        self.compress: bool = kwargs.get("compress", True)
