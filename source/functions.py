"""
Some generic functions
"""


import gzip
import brotli
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


def generate_lazy_response(
        data: str | bytes,
        content_type: str,
        status: StatusCode,
        additional_headers: dict | None = None,
        content_encoding: str | None = None) -> Response:
    """
    Generates a lazy response with automatically assigned headers
    :param data: text
    :param content_type: content type
    :param status: response status
    :param additional_headers: additional headers
    :param content_encoding: content encoding (compression)
    :return: Response
    """

    # check type
    if isinstance(data, str):
        encoded_text = data.encode("utf-8")
    elif isinstance(data, bytes):
        encoded_text = data
    else:
        raise ValueError

    # compress if needed
    if content_encoding == "gzip":
        encoded_text = gzip.compress(encoded_text)
    elif content_encoding == "br":
        encoded_text = brotli.compress(encoded_text)

    # add headers
    headers = {
        "Content-Length": len(encoded_text),
        "Content-Type": content_type,
        "Server": "HTTPy"
    }
    if additional_headers:
        headers.update(additional_headers)

    # return response
    return Response(
        status=status,
        headers=headers,
        data=encoded_text)
