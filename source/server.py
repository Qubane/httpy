"""
HTTPy server code
"""


import importlib
from source.options import *
from source.classes import *
from source.status_codes import *


LOGGER: logging.Logger = logging.getLogger(__name__)


class Server:
    """
    Page server class
    """

    def __init__(self):
        self._path_tree: dict[str, dict | Page] = dict()

    def add_path(self, path: str, page: Page) -> None:
        """
        Adds path to path tree
        :param path: path to add
        :param page: page class reference
        """

        node = self._path_tree
        split_path = path.split("/")
        for split in split_path[:-1]:
            if split not in node:
                node[split] = {}
            node = node[split]
        node[split_path[-1]] = {"__page__": page}

    def get_path(self, path: str) -> Page | None:
        """
        Get path from path tree
        :param path: path to get
        :return: Page class or None if path doesn't exit
        """

        node = self._path_tree
        split_path = path.split("/")

        # go through parts of path
        for idx, split in enumerate(split_path):
            if "*" in node:
                break
            if split not in node:
                return None
            node = node[split]
        if "*" in node:
            return node["*"]
        if "__page__" in node:
            return node["__page__"]

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

    def import_page(self, import_path: str) -> None:
        """
        Imports page under a given path
        :param import_path: python script import path
        :return: None
        """

        module = importlib.import_module(import_path)

        try:
            module.setup(self)
        except Exception as e:
            LOGGER.error(f"Error occurred when importing page at '{import_path}';", exc_info=e)
            return

        LOGGER.info(f"Page '{import_path}' imported")

    def add_page(self, page: Page) -> None:
        """
        Adds page to self. Generally called by setup
        :param page: page class
        :return: None
        """
