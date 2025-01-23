import os
import importlib
from typing import BinaryIO
from types import ModuleType
from source.functions import parse_md2html
from source.exceptions import InternalServerError


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

        result = self._import.make_page(**kwargs)
        if isinstance(result, DummyPage):
            return result.get_data()
        raise InternalServerError("Scripted request error")

    def get_data(self, **kwargs) -> bytes | BinaryIO:
        """
        Returns BinaryIO file or raw bytes
        """

        if self.is_scripted:  # requested pages
            return self._return_scripted(**kwargs)
        else:
            return self._return_localized(kwargs.get("locale", "en"))


class DummyPage:
    """
    Dummy page container, stores actual byte data instead of file path / script request
    """

    def __init__(self, data: bytes | str, type_: str | None = None):
        self.filepath: None = None
        self.locales: None = None
        self.is_scripted: bool = True
        self.type: str = type_ if type_ else "application/octet-stream"

        self._data = data if isinstance(data, bytes) else data.encode("utf-8")

    def get_data(self, **kwargs) -> bytes:
        """
        Returns raw bytes of page
        """

        return self._data


class TemplatePage(Page):
    """
    Page that uses template in which it inserts data.
    Is strictly of HTML type
    """

    def __init__(self, template: str | None = None, *args, **kwargs):
        """
        :param template: path to template file
        """

        super().__init__(*args, **kwargs)

        self.type = "text/html"
        self.is_scripted = True

        if template:
            with open(template, "r", encoding="utf-8") as file:
                self.template: str = file.read()
        else:
            self.template: str = "{sections}"

        self._update_attributes()

    def _update_attributes(self) -> int:
        """
        Updates self attributes
        :return: end of attribute section in file
        """

        with open(self.filepath, "r", encoding="utf-8") as file:
            while True:  # read starting configs
                config = file.readline().split(":")
                if len(config) == 1:
                    break
                name = config[0]
                value = config[1].replace("\r", "").replace("\n", "")
                setattr(self, name, value)
            return file.tell()

    def _return_scripted(self, **kwargs):
        """
        Parses .md formatted file and inserts into template
        """

        with open(self.filepath, "r", encoding="utf-8") as file:
            file.seek(self._update_attributes())
            parsed = parse_md2html(file.read())
        sections = []
        for header in parsed.split("<h1>"):
            sections.append(f"<section class='info-section'><h1>{header}</section>")
        return self.template.format(
            sections=f"<div class='section-div'>{'<br>'.join(sections)}</div>")