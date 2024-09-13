"""
Config manager
"""


class Config:
    SOCKET_RECV_SIZE: int
    SOCKET_SEND_SIZE: int

    LOGGING_PATH: str
    LOGGING_MAX_SIZE: int

    @classmethod
    def _read_configs(cls):
        """
        Reads config files.
        """

        import os
        import json

