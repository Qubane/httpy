import os
import logging
from datetime import datetime
from source.functions import parse_md2html
from source.exceptions import NotFoundError
from source.page_classes import TemplatePage, DummyPage
from source.settings import WEB_DIRECTORY, PAGE_NEWS_LIST_SIZE


LOGGER: logging.Logger = logging.getLogger(__name__)


POSTS_PATH: str = f"{WEB_DIRECTORY}/pages/news/posts/"
with open(f"{WEB_DIRECTORY}/templates/news.template.html", "r", encoding="utf-8") as _file:
    PAGE_TEMPLATE: str = _file.read()


class NewsPage(TemplatePage):
    """
    News page
    """

    template: str = PAGE_TEMPLATE

    def __init__(self, name: str, *args, **kwargs):
        """
        :param name: internal reference name
        :key filepath: path to .md text file
        """

        self.tags: list[str] = list()
        self.name: str = name
        self.title: str = "untitled"
        self.description: str = "no description"

        super().__init__(*args, **kwargs)

        self.publish_date: datetime = datetime.fromtimestamp(
            os.path.getmtime(self.filepath), datetime.now().tzinfo)

    def _update_attributes(self) -> int:
        """
        Updates self attributes
        :return: end of attribute section in file
        """

        seek = super()._update_attributes()
        if isinstance(self.tags, str):  # this is awful...
            self.tags = self.tags.split(",")
        return seek


def make_page(**kwargs) -> DummyPage:
    """
    Gets called from ClientHandler. Yields a page or part of it
    """

    locale: str = kwargs.get("locale", "en")

    if kwargs["path"].split("/")[-1] != "news":  # if not news
        raise NotFoundError("Page Not Found")

    page_name = kwargs.get("post")
    if page_name:  # if user opens post
        if page_name not in PostList.post_list:
            raise NotFoundError("Post Not Found")
        return DummyPage(PageMaker.make_news_page(page_name), "text/html")
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

        return DummyPage(PageMaker.make_news_list_page(tags, page), "text/html")


class PostList:
    """
    List of posts with references to their tags, titles, descriptions and other generic data
    """

    # 'post': Post(...)
    post_list: dict[str, NewsPage] = dict()

    # 'tag': [Post(...), Post(...), Post(...), ...]
    tagged_posts: dict[str, list[NewsPage]] = dict()

    @classmethod
    def update_post(cls, post: str):
        """
        Updates configs for a single post.
        :param post: post name
        """

        post_name = os.path.splitext(post)[0]
        cls.post_list[post_name] = NewsPage(
            name=post_name,
            filepath=f"{POSTS_PATH}{post}")

        LOGGER.info(f"Updated post: '{cls.post_list[post_name]}'")

    @classmethod
    def update(cls):
        """
        Updates list of posts
        """

        for file in os.listdir(POSTS_PATH):
            cls.update_post(file)

        cls.tagged_posts.clear()
        for _, page in cls.post_list.items():
            for tag in page.tags:
                if tag not in cls.tagged_posts:
                    cls.tagged_posts[tag] = list()
                cls.tagged_posts[tag].append(page)


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
        return NewsPage.template.format(
            sections=f"<div class='section-div'>{'<hr>'.join(sections)}</div>")

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
        return NewsPage.template.format(
            sections=f"<div class='section-div'><section class='info-section'>{''.join(parsed)}</section></div>")


PostList.update()
