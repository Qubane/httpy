import os
import json
import logging
import importlib
from typing import Any
from dataclasses import dataclass
from source.settings import WEB_DIRECTORY


LOGGER: logging.Logger = logging.getLogger(__name__)


@dataclass
class Page:
    """
    Page class
    """

    filepath: str
    locales: list[str]
    is_scripted: bool = False


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
    def add(cls, path: str, page: Page):
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

    @classmethod
    def get(cls, path: str) -> Page | None:
        """
        Returns node at given path
        :param path: string path
        """

        node = cls.tree
        split_path = path.split("/")
        for split in split_path[:-1]:
            if "*" in node:
                return node["*"]
            if split not in node:
                return None
            node = node[split]
        if "*" in node:
            return node["*"]
        return node.get(split_path[-1])


class PageManager:
    """
    Controls access to pages and page indexing
    """

    @classmethod
    def init(cls):
        """
        Initializes path manager
        """

        # Very Important Path
        page_info = {
            "filepath": f"{WEB_DIRECTORY}/favicon.ico",
            "locales": ["en"]}
        PathTree.add("/favicon.ico", page_info)
        LOGGER.info(f"Added '/favicon.ico' as '{WEB_DIRECTORY}/favicon.ico';")

        # Append other paths
        for page_directory in os.listdir(f"{WEB_DIRECTORY}/pages"):
            dir_path = f"{WEB_DIRECTORY}/pages/{page_directory}"
            if not os.path.isfile(f"{dir_path}/index.json"):
                LOGGER.warning(f"missing 'index.json' file at '{dir_path}';")
                continue
            with open(f"{dir_path}/index.json") as file:
                data = json.load(file)

            page_info: dict[str, Any] = {"locales": data["locales"]}
            if data["filepath"]:  # normal file
                page_info["filepath"] = f"{WEB_DIRECTORY}/pages/{page_directory}/{data['filepath']}"
                LOGGER.info(f"Added '{data['web_path']}' as '{page_info['filepath']}';")
            else:  # scripted file
                page_info["filepath"] = None
                lib_path = f"{WEB_DIRECTORY}/pages/{page_directory}/{data['script_path']}"
                import_path, package_name = (os.path.dirname(lib_path).replace("/", "."),
                                             "." + os.path.splitext(os.path.basename(lib_path))[0])
                page_info["script"] = importlib.import_module(package_name, import_path)
                LOGGER.info(f"Added request '{data['web_path']}' using '{lib_path}';")

            PathTree.add(data["web_path"], page_info)
            for alias in data["web_path_aliases"]:
                # reference same dict
                PathTree.add(alias, page_info)
                LOGGER.info(f"Added '{alias}' as '{page_info['filepath']}';")
