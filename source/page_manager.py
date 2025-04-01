import os
import json
import logging
from source.settings import WEB_DIRECTORY
from source.page_classes import *


LOGGER: logging.Logger = logging.getLogger(__name__)


class PathTree:
    """
    Tree of paths
    """

    tree: dict[str, dict | Page] = {}

    @classmethod
    def __contains__(cls, item) -> bool:
        if isinstance(item, str):
            return cls.get(item) is not None
        return False

    @classmethod
    def add(cls, path: str, page: Page) -> None:
        """
        Adds new path to the tree
        :param path: string path
        :param page: page to add
        """

        node = cls.tree
        split_path = path.split("/")
        for split in split_path[:-1]:
            if split not in node:
                node[split] = dict()
            node = node[split]
        node[split_path[-1]] = page

        if page.is_scripted:
            LOGGER.info(f"Added new request to path '{path}'")
        else:
            LOGGER.info(f"Added new page to path '{path}'")

    @classmethod
    def get(cls, path: str) -> Page | None:
        """
        Returns node at given path
        :param path: string path
        """

        node = cls.tree
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


class PageManager:
    """
    Controls access to pages and page indexing
    """

    @classmethod
    def init(cls) -> None:
        """
        Initializes path manager
        """

        # Very Important Path
        page = Page(f"{WEB_DIRECTORY}/favicon.ico")
        PathTree.add("/favicon.ico", page)

        # Append other paths
        for page_directory in os.listdir(f"{WEB_DIRECTORY}/pages"):
            dir_path = f"{WEB_DIRECTORY}/pages/{page_directory}"
            if not os.path.isfile(f"{dir_path}/index.json"):
                LOGGER.warning(f"missing 'index.json' file at '{dir_path}';")
                continue
            with open(f"{dir_path}/index.json") as file:
                data = json.load(file)

            filepath = f"{WEB_DIRECTORY}/pages/{page_directory}/{data['filepath']}"
            page = Page(filepath, locales=data["locales"])
            PathTree.add(data["web_path"], page)
            for alias in data["web_path_aliases"]:
                # reference same dict
                PathTree.add(alias, page)
