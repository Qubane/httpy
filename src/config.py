"""
Config manager
"""


from typing import Any


class Config:
    # sockets
    SOCKET_RECV_SIZE: int           # buffer size for recv
    SOCKET_SEND_SIZE: int           # data split size
    SOCKET_BIND_ADDRESS: str        # binding address

    # logging
    LOGGING_PATH: str               # path to logs folder
    LOGGING_MAX_SIZE: int           # WIP; maximum logs folder size

    # http
    HTTP_MAX_PATH_LENGTH: int       # maximum request path length
    HTTP_MAX_ARG_NUMBER: int        # maximum number of path arguments
    HTTP_MAX_HEADER_NUMBER: int     # maximum amount of headers
    HTTP_MAX_RECV_SIZE: int         # maximum request size (bytes). Affects top variables
    HTTP_TIMEOUT: float             # client timeout

    # api
    API_VERSIONS: list[str]         # supported api versions

    # file manager (fileman)
    FILEMAN_COMPRESS_PATH: str      # path to compressed file tree 'www'

    @classmethod
    def initialize(cls) -> None:
        """
        Reads config files.
        """

        import os
        import json
        if not os.path.exists("cfg/config.json") or not os.path.exists("cfg/paths.json"):
            raise FileNotFoundError("Missing config")

        with open("cfg/config.json", "r", encoding="utf-8") as file:
            config = json.loads(file.read())

        config: dict[str, dict[str, Any]]
        for category in config.values():
            for key, value in category.items():
                setattr(cls, key.upper(), value)


Config.initialize()
