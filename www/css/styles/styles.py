"""
HTTPy css/styles.css web page.

adds paths:
- '/css/styles.css'
"""


from source.server import *
from source.options import *
from source.classes import *
from source.functions import *
from source.status_codes import *


class StylesPage(Page):
    """
    css/styles.css
    """

    def __init__(self, server: Server):
        server.add_path("/css/styles.css", self)

    async def on_request(self, request: Request) -> Response:
        with open(f"{WWW_DIRECTORY}/css/styles/styles.css", "rb") as f:
            page = f.read()

        additional_headers = {}
        if "accept-encoding" in request.headers:
            additional_headers["content-encoding"] = request.headers["accept-encoding"]

        return generate_lazy_response(
            data=page,
            content_type="text/css",
            additional_headers=additional_headers,
            status=STATUS_CODE_OK)


def setup(server: Server) -> None:
    server.add_page(StylesPage(server))
