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
        with open(f"{WWW_DIRECTORY}/index/index_body.html", "r", encoding="utf-8") as f:
            body = f.read()

        with open(f"{ASSETS_DIRECTORY}/template.html", "r", encoding="utf-8") as f:
            page = read_refactor_template(f, head="", body=body)

        additional_headers = {}
        if "accept-encoding" in request.headers:
            additional_headers["content-encoding"] = request.headers["accept-encoding"]

        return generate_lazy_response(
            data=page,
            content_type="text/html",
            additional_headers=additional_headers,
            status=STATUS_CODE_OK)


def setup(server: Server) -> None:
    server.add_page(IndexPage(server))
