"""
HTTPy server basic structures
"""


from src.config import Config


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


class Response:
    """
    HTTP response
    """

    def __init__(self):
        pass
