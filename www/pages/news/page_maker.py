import os
from typing import Any
from datetime import datetime
from collections.abc import Generator
from dataclasses import dataclass, field
from source.classes import Request
from source.settings import WEB_DIRECTORY, PAGE_NEWS_LIST_SIZE


POSTS_PATH: str = f"{WEB_DIRECTORY}/pages/news/posts/"
with open(f"{WEB_DIRECTORY}/templates/news.template.html", "r", encoding="utf-8") as _file:
    PAGE_TEMPLATE: str = _file.read()


def make_page(**kwargs) -> Generator[bytes, Any, None]:
    """
    Gets called from ClientHandler. Yields a page or part of it
    """

    locale: str = kwargs.get("locale", "en")
    request: Request = kwargs.get("request")


@dataclass(frozen=True)
class Post:
    """
    Post container
    """

    filepath: str
    publish_date: datetime  # last modification date
    title: str = "untitled"
    description: str = "no description"
    tags: list[str] = field(default_factory=lambda: list())


class PostList:
    """
    List of posts with references to their tags, titles, descriptions and other generic data
    """

    # 'post': Post(...)
    post_list: dict[str, Post] = dict()

    # 'tag': [Post(...), Post(...), Post(...), ...]
    tagged_posts: dict[str, list[Post]] = dict()

    @classmethod
    def update_post(cls, post: str):
        """
        Updates configs for a single post.
        :param post: post name
        """

        filepath = f"{POSTS_PATH}/{post}"

        configs = {"filepath": filepath}
        with (open(filepath, "r", encoding="utf-8") as file):
            while True:
                config = file.readline().split(":")
                if len(config) == 1:
                    break
                configs[config[0]] = (config[1]
                                      .replace("\r", "")
                                      .replace("\n", ""))
        cls.post_list[post] = Post(
            filepath=filepath,
            publish_date=datetime.fromtimestamp(os.path.getmtime(filepath)),
            **configs)

    @classmethod
    def update(cls):
        """
        Updates list of posts
        """

        for file in os.listdir(POSTS_PATH):
            cls.update_post(file)

        cls.tagged_posts.clear()
        for _, post in cls.post_list.items():
            for tag in post.tags:
                if tag not in cls.tagged_posts:
                    cls.tagged_posts[tag] = list()
                cls.tagged_posts[tag].append(post)


class PageMaker:
    """
    Page making namespace
    """

    # def make_news_list_page(page_number: int) -> str:
    #     """
    #     Creates a list page of news
    #     :param page_number: page number
    #     :return: generated html page
    #     """
    #
    #     sections = []
    #     file_list = sorted(os.listdir(POSTS_PATH))
    #     for post in file_list[page_number * PAGE_NEWS_LIST_SIZE:(page_number+1) * PAGE_NEWS_LIST_SIZE]:
    #         file, configs = get_post(f"{POSTS_PATH}/{post}")
    #         file.close()
    #         sections.append(
    #             f"<section class='info-section'>"
    #             f"<h1>{configs.get('title', 'Untitled')}</h1>"
    #             f"<p>{configs.get('description', '')}</p>"
    #             f"</section>")
    #     return PAGE_TEMPLATE.format(sections=f"<div class='section-div'>{'<hr>'.join(sections)}</div>")
