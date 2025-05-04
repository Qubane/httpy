"""
HTTPy about web page.

adds paths:
- '/about/profile_picture.png'
"""


from source.server import *
from source.options import *
from source.classes import *
from source.functions import *
from source.status_codes import *


class AboutPagePicture(Page):
    """
    about
    """

    def __init__(self, server: Server):
        server.add_path("/about/profile_picture.png", self)

    async def on_request(self, request: Request) -> Response:
        page = open(f"{WWW_DIRECTORY}/about/profile_picture.png", "rb")

        page.seek(0, os.SEEK_END)
        headers = {
            "content-length": Header(page.tell()),
            "content-type": Header("image/png")}
        page.seek(0)

        return Response(
            status=STATUS_CODE_OK,
            data=page,
            headers=headers)


def setup(server: Server) -> None:
    server.add_page(AboutPagePicture(server))
