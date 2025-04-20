"""
HTTPy video test mp4 file web page.

adds paths:
- '/test/video-test.mp4'
"""


import os
from source.server import *
from source.options import *
from source.classes import *
from source.functions import *
from source.status_codes import *


class VideoTestPage(Page):
    """
    video test
    """

    def __init__(self, server: Server):
        server.add_path("/tests/video-test.mp4", self)

    async def on_request(self, request: Request) -> Response:
        page = open(f"{WWW_DIRECTORY}/video-test/test_video.mp4", "rb")

        additional_headers = {}
        if "accept-encoding" in request.headers:
            additional_headers["content-encoding"] = request.headers["accept-encoding"]

        page.seek(0, os.SEEK_END)
        headers = {
            "content-length": Header(page.tell()),
            "content-type": Header("video/mp4"),
            "server": Header("HTTPy")}
        page.seek(0)

        return Response(
            status=STATUS_CODE_OK,
            data=page,
            headers=headers)


def setup(server: Server) -> None:
    server.add_page(VideoTestPage(server))
