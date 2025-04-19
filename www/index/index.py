"""
HTTPy index web page.

adds paths:
- '/'
- '/index.html'
"""


from source.server import *
from source.options import *
from source.classes import *
from source.functions import *
from source.status_codes import *


class IndexPage(Page):
    """
    index.html
    """

    def __init__(self, server: Server):
        server.add_path("/", self)
        server.add_path("/index.html", self)

    async def on_request(self, request: Request) -> Response:
        page = read_refactor_template(
            f"{ASSETS_DIRECTORY}/template.html",
            head="",
            body="<header> hello world! </header>")

        return Response(
            status=STATUS_CODE_OK,
            data=page)


def setup(server: Server) -> None:
    server.add_page(IndexPage(server))
