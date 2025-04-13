"""
HTTPy server exceptions
"""


class HTTPyException(Exception):
    """
    Base class for HTTPy server exceptions
    """


class InternalServerError(HTTPyException):
    """
    Any internal server errors
    """


class ExternalServerError(HTTPyException):
    """
    Any external (client-side / network side) errors
    """


class HTTPRequestError(InternalServerError):
    """
    Any type of HTTP request related error
    """


class HTTPRequestTypeError(HTTPRequestError):
    """
    HTTP request type error
    """
