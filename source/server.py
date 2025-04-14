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
        self._path_tree: dict[str, dict | Page] = dict()

    def add_path(self, path: str, page: "Page") -> None:
        """
        Adds path to path tree
        :param path: path to add
        :param page: page class reference
        """

        node = self._path_tree
        split_path = path.split("/")
        for split in split_path[:-1]:
            if split not in node:
                node[split] = dict()
            node = node[split]
        node[split_path[-1]] = page

    async def process_request(self, request: Request) -> Response:
        """
        Process client request to page server
        :param request: client request
        :return: server response
        """
