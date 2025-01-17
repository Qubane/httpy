import os
from typing import Any
from collections.abc import Generator
from source.classes import Request
from source.settings import WEB_DIRECTORY


with open(f"{WEB_DIRECTORY}/templates/news.template.html", "r", encoding="utf-8") as _file:
    PAGE_TEMPLATE = _file.read()


def make_page(**kwargs) -> Generator[bytes, Any, None]:
    """
    Makes page
    """

    locale: str = kwargs.get("locale", "en")
    request: Request = kwargs.get("request")
    if request is None:
        raise Exception("Request is None")

    dir_path = f"{WEB_DIRECTORY}/pages/news/posts/"
    for post in os.listdir(dir_path):
        filepath = dir_path + post
        configs = {}
        with open(filepath, "r", encoding="utf-8") as file:
            while True:
                config = file.readline().split(":")
                if len(config) == 1:
                    break
                configs[config[0].strip("-")] = config[1].replace("\r", "").replace("\n", "")

    yield b'yes'
