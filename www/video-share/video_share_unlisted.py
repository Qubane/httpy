"""
HTTPy video-share web page.

adds paths:
- '/videos/unlisted/*'
"""


from source.server import *
from source.options import *
from source.classes import *
from source.functions import *
from source.status_codes import *


class VideoShareUnlistedPage(Page):
    """
    example.file
    """

    def __init__(self, server: Server):
        server.add_path("/videos/unlisted/*", self)

    async def on_request(self, request: Request) -> Response:
        raise NotImplementedError


def setup(server: Server) -> None:
    server.add_page(VideoShareUnlistedPage(server))
