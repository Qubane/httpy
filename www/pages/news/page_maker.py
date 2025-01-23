import os
import logging
from typing import Any, Generator
from datetime import datetime
from source.page_manager import Page
from source.functions import parse_md2html
from source.exceptions import NotFoundError
from source.settings import WEB_DIRECTORY, PAGE_NEWS_LIST_SIZE


LOGGER: logging.Logger = logging.getLogger(__name__)


POSTS_PATH: str = f"{WEB_DIRECTORY}/pages/news/posts/"
with open(f"{WEB_DIRECTORY}/templates/news.template.html", "r", encoding="utf-8") as _file:
    PAGE_TEMPLATE: str = _file.read()


class NewsPage(Page):
    """
    News page
    """

    def __init__(self, title: str, description: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title: str = title
        self.description: str = description
        self.publish_date: datetime = datetime.fromtimestamp(
            os.path.getmtime(self.filepath), datetime.now().tzinfo)


def make_page(**kwargs) -> tuple[bytes, str]:
    """
    Gets called from ClientHandler. Yields a page or part of it
    """

    locale: str = kwargs.get("locale", "en")

    if kwargs["path"].split("/")[-1] != "news":  # if not news
        raise NotFoundError("Page Not Found")

    post = kwargs.get("post")
    if post:  # if user opens post
        if post not in PostList.post_list:
            raise NotFoundError("Post Not Found")
        return PageMaker.make_news_page(post).encode("utf-8"), "text/html"
    else:  # if user searches all posts
        # get tags
        tags = kwargs.get("tags", "all")
        if tags not in PostList.tagged_posts and tags != "all":
            raise NotFoundError("Tag Not Found")

        # make page number
        try:
            page = int(kwargs.get("page", 0))
        except ValueError:
            page = 0

        return PageMaker.make_news_list_page(tags, page).encode("utf-8"), "text/html"


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

        filepath = f"{POSTS_PATH}{post}"
        post_name = os.path.splitext(post)[0]

        configs = {}
        with (open(filepath, "r", encoding="utf-8") as file):
            while True:
                config = file.readline().split(":")
                if len(config) == 1:
                    break
                configs[config[0]] = (config[1]
                                      .replace("\r", "")
                                      .replace("\n", ""))
            configs["tags"] = configs["tags"].split(",")
        cls.post_list[post_name] = Post(
            name=post_name,
            filepath=filepath,
            publish_date=datetime.fromtimestamp(os.path.getmtime(filepath)),
            **configs)

        LOGGER.info(f"Updated post: '{cls.post_list[post_name]}'")

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

    @staticmethod
    def make_news_list_page(tag: str, page_number: int) -> str:
        """
        Creates a list page of news
        :param tag: search tag
        :param page_number: page number
        :return: generated html page
        """

        sections = []
        if tag == "all":
            post_list = sorted(PostList.post_list.values(), key=lambda x: x.publish_date, reverse=True)
        else:
            post_list = sorted(PostList.tagged_posts[tag], key=lambda x: x.publish_date, reverse=True)
        for post in post_list[page_number * PAGE_NEWS_LIST_SIZE:(page_number+1) * PAGE_NEWS_LIST_SIZE]:
            sections.append(
                f"<section class='info-section'>"
                f"<div style='display: flex; flex-direction: column'>"
                f"<a href='/news?post={post.name}'><h1>{post.title}</h1></a>"
                f"<p style='color: grey; font-size: 70%'>creation date: {post.publish_date.__str__()}</p>"
                f"</div>"
                f"<p style='padding-top: 10px'>{post.description}</p>"
                f"</section>")
        return PAGE_TEMPLATE.format(sections=f"<div class='section-div'>{'<hr>'.join(sections)}</div>")

    @staticmethod
    def make_news_page(post_name: str) -> str:
        """
        Serves a news page
        :param post_name: name for a news post
        :return: generated html page
        """

        post = PostList.post_list[post_name]
        with open(post.filepath, "r", encoding="utf-8") as file:
            while len(file.readline()) > 2:  # skip configs section
                pass
            parsed = parse_md2html(file.read())
        return PAGE_TEMPLATE.format(
            sections=f"<div class='section-div'><section class='info-section'>{''.join(parsed)}</section></div>")


PostList.update()
