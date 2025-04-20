"""
HTTPy favicon web page.

adds paths:
- '/favicon.ico'
"""


from source.server import *
from source.options import *
from source.classes import *
from source.functions import *
from source.status_codes import *


class FaviconPage(Page):
    """
    index.html
    """

    def __init__(self, server: Server):
        server.add_path("/favicon.ico", self)

    async def on_request(self, request: Request) -> Response:
        with open(f"{WWW_DIRECTORY}/favicon/favicon.ico", "rb") as f:
            page = f.read()

        return generate_lazy_response(
            data=page,
            content_type="image/x-icon",
            status=STATUS_CODE_OK)


def setup(server: Server) -> None:
    server.add_page(FaviconPage(server))
