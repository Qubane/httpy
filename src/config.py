"""
Config manager
"""


class Config:
    # sockets
    SOCKET_RECV_SIZE: int
    SOCKET_SEND_SIZE: int

    # logging
    LOGGING_PATH: str
    LOGGING_MAX_SIZE: int

    # http
    HTTP_MAX_PATH_LENGTH: int
    HTTP_MAX_ARG_NUMBER: int
    HTTP_MAX_HEADER_NUMBER: int

    # threading
    THREADING_MAX_NUMBER: int
    THREADING_TIMEOUT: int

    # api
    API_VERSIONS: list[str]

    # file manager (fileman)
    FILEMAN_COMPRESS_PATH: str

    @classmethod
    def initialize(cls):
        """
        Reads config files.
        """

        import os
        import json
        if not os.path.exists("cfg/config.json") or not os.path.exists("cfg/paths.json"):
            raise FileNotFoundError("Missing config")

        with open("cfg/config.json", "r", encoding="utf-8") as file:
            config = json.loads(file.read())

        # sockets
        cls.SOCKET_RECV_SIZE = config["socket"]["socket_recv_size"]
        cls.SOCKET_SEND_SIZE = config["socket"]["socket_send_size"]

        # logging
        cls.LOGGING_PATH = config["logging"]["logging_path"]
        cls.LOGGING_MAX_SIZE = config["logging"]["logging_max_size"]

        # http
        cls.HTTP_MAX_PATH_LENGTH = config["http"]["http_max_path_length"]
        cls.HTTP_MAX_ARG_NUMBER = config["http"]["http_max_arg_number"]
        cls.HTTP_MAX_HEADER_NUMBER = config["http"]["http_max_header_number"]

        # threading
        cls.THREADING_MAX_NUMBER = config["threading"]["threading_max_number"]
        cls.THREADING_TIMEOUT = config["threading"]["threading_timeout"]

        # api
        cls.API_VERSIONS = config["api"]["api_versions"]

        # file manager (fileman)
        cls.FILEMAN_COMPRESS_PATH = config["fileman"]["fileman_compress_path"]


Config.initialize()
