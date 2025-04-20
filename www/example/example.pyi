"""
HTTPy exampel web page.

adds paths:
- '/example'
"""


from source.server import *
from source.options import *
from source.classes import *
from source.functions import *
from source.status_codes import *


class ExamplePage(Page):
    """
    example.file
    """

    def __init__(self, server: Server):
        server.add_path("/example", self)

    async def on_request(self, request: Request) -> Response:
        with open(f"{WWW_DIRECTORY}/example/example.pyi", "rb") as f:
            page = f.read()

        additional_headers = {}
        if "accept-encoding" in request.headers:
            additional_headers["content-encoding"] = request.headers["accept-encoding"]

        return generate_lazy_response(
            data=page,
            content_type="text/html",
            additional_headers=additional_headers,
            status=STATUS_CODE_OK)


def setup(server: Server) -> None:
    server.add_page(ExamplePage(server))
