"""
HTTPy video-share web page.

adds paths:
- '/videos/unlisted/*'
"""


import os
import glob
import asyncio
from source.server import *
from source.options import *
from source.classes import *
from source.functions import *
from source.status_codes import *


class VideoShareUnlistedPage(Page):
    """
    video-share unlisted
    """

    dir_path: str = f"{WWW_DIRECTORY}/video-share/unlisted_videos"

    def __init__(self, server: Server):
        server.add_path("/videos/unlisted/*", self)

        # "uuid": "path/to/file"
        self._video_list: dict[str, str] = {}

        asyncio.create_task(self._update_videos_routine())

    async def _update_videos_routine(self):
        """
        Checks for new videos every 5 minutes
        """

        while True:
            for file in glob.glob(self.dir_path + "/**/*", recursive=True):
                print(file)
            await asyncio.sleep(5 * 60)

    async def on_request(self, request: Request) -> Response:
        return Response(data=b'yes')


def setup(server: Server) -> None:
    # ensure path exists
    if not os.path.isdir(VideoShareUnlistedPage.dir_path):
        os.makedirs(VideoShareUnlistedPage.dir_path)

    server.add_page(VideoShareUnlistedPage(server))
