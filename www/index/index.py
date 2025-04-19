"""
HTTPy index web page.

adds paths:
- '/'
- '/index.html'
"""


from source.classes import *
from source.server import Server
from source.status_codes import *


TEST_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title> Qubane's page </title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="/css/styles.css">
</head>
    <body>
        <header> Hello World! </header>
    </body>
</html>
"""


class IndexPage(Page):
    """
    index.html
    """

    def __init__(self, server: Server):
        server.add_path("/", self)
        server.add_path("/index.html", self)

    async def on_request(self, request: Request) -> Response:
        page = TEST_PAGE.encode("utf-8")

        return Response(
            status=STATUS_CODE_OK,
            data=page)


def setup(server: Server) -> None:
    server.add_page(IndexPage(server))
