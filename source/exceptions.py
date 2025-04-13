"""
HTTPy server exceptions
"""


from source.status_codes import *


class HTTPyException(Exception):
    """
    Base class for HTTPy server exceptions
    """

    status = STATUS_CODE_INTERNAL_SERVER_ERROR


class InternalServerError(HTTPyException):
    """
    Any internal server errors
    """

    status = STATUS_CODE_INTERNAL_SERVER_ERROR


class ExternalServerError(HTTPyException):
    """
    Any external (client-side / network side) errors
    """

    status = STATUS_CODE_BAD_REQUEST


class HTTPRequestError(InternalServerError):
    """
    Any type of HTTP request related error
    """


class HTTPRequestTypeError(HTTPRequestError):
    """
    HTTP request type error
    """
