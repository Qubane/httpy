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
    _update_videos_routine_interval: float = 5 * 60  # 5 minutes (* 60 seconds)

    def __init__(self, server: Server):
        server.add_path("/videos/unlisted/*", self)

        # "uuid": "path/to/file"
        self._video_list: dict[str, str] = {}

        asyncio.create_task(self._update_videos_routine())

    async def _update_videos_routine(self):
        """
        Checks for new videos
        """

        while True:
            for filepath in glob.glob(self.dir_path + "/**/*", recursive=True):
                filepath = filepath.replace("\\", "/")
                video_name = os.path.basename(os.path.splitext(filepath)[0])
                self._video_list[video_name] = filepath
            await asyncio.sleep(self._update_videos_routine_interval)

    async def on_request(self, request: Request) -> Response:
        if (video_id := request.query_args.get("v")) is not None and video_id in self._video_list:
            video = open(self._video_list[video_id], "rb")
            video_type = os.path.splitext(self._video_list[video_id])[1]

            # generate basic headers
            video.seek(0, os.SEEK_END)
            headers = {
                "content-length": Header(video.tell()),
                "content-type": Header(f"video/{video_type}")}
            video.seek(0)

            # return response
            return Response(
                status=STATUS_CODE_OK,
                data=video,
                headers=headers)
        return Response(
            status=STATUS_CODE_NOT_FOUND,
            data=b'video not found')


def setup(server: Server) -> None:
    # ensure path exists
    if not os.path.isdir(VideoShareUnlistedPage.dir_path):
        os.makedirs(VideoShareUnlistedPage.dir_path)

    server.add_page(VideoShareUnlistedPage(server))
