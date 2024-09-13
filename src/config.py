"""
Config manager
"""


class Config:
    SOCKET_RECV_SIZE: int
    SOCKET_SEND_SIZE: int

    LOGGING_PATH: str
    LOGGING_MAX_SIZE: int

    HTTP_MAX_PATH_LENGTH: int
    HTTP_MAX_ARG_NUMBER: int
    HTTP_MAX_HEADER_NUMBER: int

    THREADING_MAX_NUMBER: int
    THREADING_TIMEOUT: int

    API_VERSIONS: list[str]

    @classmethod
    def _read_configs(cls):
        """
        Reads config files.
        """

        import os
        import json
        if not os.path.exists("cfg/config.json"):
            raise FileNotFoundError("Missing config")


