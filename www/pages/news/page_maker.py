import os
from typing import Any, TextIO
from collections.abc import Generator
from source.classes import Request
from source.settings import WEB_DIRECTORY, PAGE_NEWS_LIST_SIZE


POSTS_PATH: str = f"{WEB_DIRECTORY}/pages/news/posts/"
with open(f"{WEB_DIRECTORY}/templates/news.template.html", "r", encoding="utf-8") as _file:
    PAGE_TEMPLATE: str = _file.read()


def make_page(**kwargs) -> Generator[bytes, Any, None]:
    """
    Makes page
    """

    locale: str = kwargs.get("locale", "en")
    request: Request = kwargs.get("request")
    if request is None:
        raise Exception("Request is None")

    yield make_news_list_page(0).encode("utf-8")


def get_post(filename: str) -> tuple[TextIO, dict[str, Any]]:
    """
    Returns TextIO and information about the news post
    :param filename: name of the post
    :return: file and configs
    """

    configs = {}
    file = open(filename, "r", encoding="utf-8")
    while True:
        config = file.readline().split(":")
        if len(config) == 1:
            break
        configs[config[0].strip("-")] = config[1].replace("\r", "").replace("\n", "")
    return file, configs


def make_news_list_page(page_number: int) -> str:
    """
    Creates a list page of news
    :param page_number: page number
    :return: generated html page
    """

    sections = []
    file_list = sorted(os.listdir(POSTS_PATH))
    for post in file_list[page_number * PAGE_NEWS_LIST_SIZE:(page_number+1) * PAGE_NEWS_LIST_SIZE]:
        file, configs = get_post(f"{POSTS_PATH}/{post}")
        file.close()
        sections.append(
            f"<section class='info-section'>"
            f"<h1>{configs.get('title', 'Untitled')}</h1>"
            f"<p>{configs.get('description', '')}</p>"
            f"</section>")
    return PAGE_TEMPLATE.format(sections=f"<div class='section-div'>{'<hr>'.join(sections)}</div>")