"""
HTTPy server exceptions
"""


class HTTPyException(Exception):
    """
    Base class for HTTPy server exceptions
    """


class HTTPRequestError(HTTPyException):
    """
    Any type of HTTP request related error
    """
