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
            page_content = file.read()

    yield b'yes'


def parse_md2html(text: str) -> str:
    """
    Parses md to html
    :param text: md formatted string
    :return: html formatted string
    """

    text = text.replace("\r", "").split("\n")

    # make formatting
    is_bold = False
    is_italics = False
    for _ in range(len(text)):
        line = text.pop(0)
        new_line = ""
        format_buffer = ""
        for char in line:
            if char == "*":
                format_buffer += char
                continue
            if format_buffer == "*" and char != "*":
                format_buffer = ""
                is_italics = not is_italics
                if is_italics:
                    new_line += "<i>"
                else:
                    new_line += "</i>"
            if format_buffer == "**" and char != "*":
                format_buffer = ""
                is_bold = not is_bold
                if is_italics:
                    new_line += "<b>"
                else:
                    new_line += "</b>"
            new_line += char
        text.append(new_line)

    # make headers
    for _ in range(len(text)):
        line = text.pop(0)
        if len(line) == 0:
            continue
        if line[0] == "#":
            header = 1
            if len(line) > 2 and line[1] == "#":
                header = 2
            if len(line) > 3 and line[2] == "#":
                header = 3
            text.append(f"<p><h{header}>{line[header:].strip()}</h{header}></p>")
            continue
        text.append(f"<p>{line.strip()}</p>")

    return "".join(text)
