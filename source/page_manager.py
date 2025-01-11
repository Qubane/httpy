import os
import json
import logging
from source.settings import WEB_DIRECTORY


class PageManager:
    """
    Controls access to pages and page indexing
    """

    # 'web_path': {'filepath': ..., 'locales': ['en', 'ru']}
    path_tree: dict[str, dict[str, str | list]] = dict()

    logger: logging.Logger = logging.getLogger(__name__)

    @classmethod
    def init(cls):
        for page_directory in os.listdir(f"{WEB_DIRECTORY}/pages"):
            dir_path = f"{WEB_DIRECTORY}/pages/{page_directory}"
            if not os.path.isfile(f"{dir_path}/index.json"):
                cls.logger.warning(f"missing 'index.json' file at '{dir_path}';")
                continue
            with open(f"{dir_path}/index.json") as file:
                data = json.load(file)

            page_info = {
                "filepath": data["filepath"],
                "locales": data["locales"]}
            cls.path_tree[data["web_path"]] = page_info
            cls.logger.info(f"Added '{data['web_path']}' as '{page_info['filepath']}';")
            for alias in data["web_path_aliases"]:
                # reference same dict
                cls.path_tree[alias] = page_info
                cls.logger.info(f"Added '{alias}' as '{page_info['filepath']}';")
