"""
Config manager
"""


from typing import Any


class Config:
    # sockets
    SOCKET_RECV_SIZE: int
    SOCKET_SEND_SIZE: int
    SOCKET_BIND_ADDRESS: str

    # logging
    LOGGING_PATH: str
    LOGGING_MAX_SIZE: int

    # http
    HTTP_MAX_PATH_LENGTH: int
    HTTP_MAX_ARG_NUMBER: int
    HTTP_MAX_HEADER_NUMBER: int
    HTTP_MAX_RECV_SIZE: int

    # threading
    THREADING_MAX_NUMBER: int
    THREADING_TIMEOUT: int

    # api
    API_VERSIONS: list[str]

    # file manager (fileman)
    FILEMAN_COMPRESS_PATH: str

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
