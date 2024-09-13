"""
HTTP status codes
"""


class StatusCode:
    """
    HTML status code
    """

    def __init__(self, code: int, message: str):
        self._code: int = code
        self._message: str = message

    def __bytes__(self):
        return f"{self._code} {self._message}".encode("utf8")

    def __str__(self):
        return f"{self._code} {self._message}"

    @property
    def code(self):
        return self._code

    @property
    def message(self):
        return self._message


# Status codes!
# 2xx
STATUS_CODE_OK = StatusCode(200, "OK")

# 4xx
STATUS_CODE_BAD_REQUEST = StatusCode(400, "Bad Request")
STATUS_CODE_UNAUTHORIZED = StatusCode(401, "Unauthorized")
STATUS_CODE_FORBIDDEN = StatusCode(403, "Forbidden")
STATUS_CODE_NOT_FOUND = StatusCode(404, "Not Found")
STATUS_CODE_PAYLOAD_TOO_LARGE = StatusCode(413, "Payload Too Large")
STATUS_CODE_URI_TOO_LONG = StatusCode(414, "URI Too Long")
STATUS_CODE_IM_A_TEAPOT = StatusCode(418, "I'm a teapot")  # I followed mozilla's dev page, it was there
STATUS_CODE_FUNNY_NUMBER = StatusCode(6969, "UwU")

# 5xx
STATUS_CODE_INTERNAL_SERVER_ERROR = StatusCode(500, "Internal Server Error")
STATUS_CODE_NOT_IMPLEMENTED = StatusCode(501, "Not Implemented")
STATUS_CODE_SERVICE_UNAVAILABLE = StatusCode(503, "Service Unavailable")
