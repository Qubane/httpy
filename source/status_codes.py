"""
HTTP status codes
"""


from dataclasses import dataclass


@dataclass(frozen=True)
class StatusCode:
    """
    HTTP status codes
    """

    code: int
    message: str

    def __bytes__(self):
        return f"{self.code} {self.message}".encode("utf-8")


# 2xx
STATUS_CODE_OK = StatusCode(200, "OK")

# 3xx
STATUS_CODE_MOVED_PERMANENTLY = StatusCode(301, "Moved Permanently")
STATUS_CODE_NOT_MODIFIED = StatusCode(304, "Not Modified")

# 4xx
STATUS_CODE_BAD_REQUEST = StatusCode(400, "Bad Request")
STATUS_CODE_UNAUTHORIZED = StatusCode(401, "Unauthorized")
STATUS_CODE_FORBIDDEN = StatusCode(403, "Forbidden")
STATUS_CODE_NOT_FOUND = StatusCode(404, "Not Found")
STATUS_CODE_PAYLOAD_TOO_LARGE = StatusCode(413, "Payload Too Large")
STATUS_CODE_URI_TOO_LONG = StatusCode(414, "URI Too Long")
STATUS_CODE_FUNNY_NUMBER = StatusCode(6969, "UwU")

# 5xx
STATUS_CODE_INTERNAL_SERVER_ERROR = StatusCode(500, "Internal Server Error")
STATUS_CODE_NOT_IMPLEMENTED = StatusCode(501, "Not Implemented")
STATUS_CODE_SERVICE_UNAVAILABLE = StatusCode(503, "Service Unavailable")
