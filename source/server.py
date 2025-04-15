"""
HTTPy server code
"""


from source.options import *
from source.classes import *
from source.status_codes import *


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

    def get_path(self, path: str) -> Page | None:
        """
        Get path from path tree
        :param path: path to get
        :return: Page class or None if path doesn't exit
        """

        node = self._path_tree
        split_path = path.split("/")
        for split in split_path:
            if "*" in node:
                return node["*"]
            if split not in node:
                return None
            node = node[split]
        if isinstance(node, dict) and "*" in node:
            return node["*"]
        return node

    async def process_request(self, request: Request) -> Response:
        """
        Process client request to page server
        :param request: client request
        :return: server response
        """

        # get page
        page = self.get_path(request.path)

        # give response
        if page is not None:
            return await page.on_request(request)
        else:
            return Response(status=STATUS_CODE_NOT_FOUND, data=b'page not found')

    async def import_page(self, import_path: str) -> None:
        """
        Imports page under a given path
        :param import_path: python script import path
        :return: None
        """
