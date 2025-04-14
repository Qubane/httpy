"""
HTTPy server code
"""


from source.options import *
from source.classes import *


class Server:
    """
    Page server class
    """

    def __init__(self):
        self._path_tree: dict[str, dict | object] = dict()

    def add_path(self, path: str, page: "Page") -> None:
        """
        Adds path to path tree
        :param path: path to add
        :param page: page class reference
        """
