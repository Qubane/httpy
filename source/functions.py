"""
Some generic functions
"""


from typing import TextIO
from source.classes import *


def read_refactor_template(file: TextIO, **kwargs) -> str:
    """
    Reads and refactors a template file
    :param file: file
    :param kwargs: arguments to be refactored
    :return: bytes or str, depending on mode
    """

    key_args = {f"{{{x}}}" for x in kwargs.keys()}

    # output
    page = ""

    # go through each line
    for line in file.readlines():
        # check if line argument is in key_args
        if (arg := line.strip()) in key_args:
            page += kwargs[arg[1:-1]]
        else:
            page += line

    # return page
    return page


def reads_refactor_template(data: str, **kwargs) -> str:
    """
    Reads and refactors a template file
    :param data: string data
    :param kwargs: arguments to be refactored
    :return: bytes or str, depending on mode
    """

    key_args = {f"{{{x}}}" for x in kwargs.keys()}

    # output
    page = ""

    # go through each line
    for line in data.split("\n"):
        # check if line argument is in key_args
        if (arg := line.strip()) in key_args:
            page += kwargs[arg[1:-1]]
        else:
            page += line

    # return page
    return page


def generate_lazy_response(text: str, content_type: str, content_encoding: str, status: StatusCode) -> Response:
    """
    Generates a lazy response with automatically assigned headers
    :param text: text
    :param content_type: content type
    :param content_encoding: content encoding (compression)
    :param status: response status
    :return: Response
    """

    encoded_text = text.encode("utf-8")

    headers = {
        "Content-Length": len(encoded_text),
        "Content-Type": content_type,
        "Server": "HTTPy"
    }

    return Response(
        status=status,
        headers=headers,
        data=encoded_text)
