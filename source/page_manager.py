import os
import json
import logging
from typing import Any
from source.settings import WEB_DIRECTORY


LOGGER: logging.Logger = logging.getLogger(__name__)


class PageManager:
    """
    Controls access to pages and page indexing
    """

    # 'web_path': {'filepath': ..., 'locales': ['en', 'ru']}
    path_tree: dict[str, dict[str, Any]] = dict()

    @classmethod
    def init(cls):
        """
        Initializes path manager
        """

        # Very Important Path
        page_info = {
            "filepath": f"{WEB_DIRECTORY}/favicon.ico",
            "locales": ["en"]}
        cls.path_tree["/favicon.ico"] = page_info
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
                page_info["script_path"] = f"{WEB_DIRECTORY}/pages/{page_directory}/{data['script_path']}"
                LOGGER.info(f"Added script '{data['web_path']}' using '{page_info['script_path']}';")

            cls.path_tree[data["web_path"]] = page_info
            for alias in data["web_path_aliases"]:
                # reference same dict
                cls.path_tree[alias] = page_info
                LOGGER.info(f"Added '{alias}' as '{page_info['filepath']}';")

    @classmethod
    def get(cls, web_path: str) -> dict[str, str | list] | None:
        """
        Returns reference to page info dictionary
        :param web_path: web request path
        :return: filepath with unformatted prefix
        """

        return cls.path_tree.get(web_path)
