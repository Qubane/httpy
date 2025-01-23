import os
import json
import logging
import importlib
from typing import BinaryIO
from types import ModuleType
from source.settings import WEB_DIRECTORY
from source.functions import parse_md2html
from source.exceptions import InternalServerError


LOGGER: logging.Logger = logging.getLogger(__name__)


class Page:
    """
    Base class for page
    """

    def __init__(self, filepath: str, locales: list[str] | None = None):
        self.filepath: str = filepath
        self.locales: list[str] | None = locales
        self.is_scripted: bool = True if self.filepath[-3:] == ".py" else False
        self.type: str = "application/octet-stream"

        self._import: ModuleType | None = None
        if self.is_scripted:
            self._import_func()

        self._define_own_type()

    def _import_func(self) -> None:
        """
        Imports the script to generate the page
        """

        name = "." + os.path.splitext(os.path.basename(self.filepath))[0]
        package_path = os.path.dirname(self.filepath).replace("/", ".")

        self._import = importlib.import_module(name, package_path)

    def _define_own_type(self) -> None:
        """
        Defines own type using MIME types thing
        """

        extension = os.path.splitext(self.filepath)[1]

        # temp
        if self.is_scripted:
            self.type = "text/html"
            return

        # text types
        match extension:
            case ".htm" | ".html":
                self.type = "text/html"
            case ".css":
                self.type = "text/css"
            case ".txt" | ".md":
                self.type = "text/plain"
            case ".json":
                self.type = "application/json"
            case ".js":  # ono :<
                self.type = "text/javascript"

        # byte types
        match extension:
            case ".png" | ".bmp" | ".jpg" | ".jpeg" | ".webp":
                self.type = f"image/{extension[1:]}"
            case ".ico":
                self.type = "image/x-icon"
            case ".svg":
                self.type = "image/svg+xml"
            case ".mp3":
                self.type = "audio/mpeg"
            case ".aac" | ".mid" | ".midi" | ".wav":
                self.type = f"audio/{extension[1:]}"
            case ".mp4" | ".mpeg" | ".webm":
                self.type = f"video/{extension[1:]}"
            case ".ts":
                self.type = "video/mp2t"
            case ".avi":
                self.type = "video/x-msvideo"

    def _return_localized(self, locale: str) -> BinaryIO:
        """
        Internal method for returning a localized BinaryIO file
        """

        filepath = self.filepath
        if not self.locales or locale not in self.locales:
            locale = "en"
        return open(filepath.format(prefix=locale), "rb")

    def _return_scripted(self, **kwargs):
        """
        Internal method for returning scripted pages
        """

        if isinstance((result := self._import.make_page(**kwargs)), bytes):
            return result
        raise InternalServerError("Scripted request error")

    def get_data(self, **kwargs) -> bytes | BinaryIO:
        """
        Returns BinaryIO file or raw bytes
        """

        if self.is_scripted:  # requested pages
            return self._return_scripted(**kwargs)
        else:
            return self._return_localized(kwargs.get("locale", "en"))


class TemplatePage(Page):
    """
    Page that uses template in which it inserts data.
    Is strictly of HTML type
    """

    def __init__(self, template: str, *args, **kwargs):
        """
        :param template: path to template file
        """

        super().__init__(*args, **kwargs)

        self.type = "text/html"
        self.is_scripted = True

        with open(template, "r", encoding="utf-8") as file:
            self.template: str = file.read()

    def _return_scripted(self, **kwargs):
        """
        Parses .md formatted file and inserts into template
        """


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
