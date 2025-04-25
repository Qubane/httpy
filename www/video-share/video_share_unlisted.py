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
        # "uuid": "path/to/file"
        self._video_list: dict[str, str] = {}

        # define "api" access path
        self._video_www_path: str = "/videos/unlisted"

        # add path
        server.add_path(f"{self._video_www_path}/*", self)

        # start a routine
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
            # make video type
            video_type = os.path.splitext(self._video_list[video_id])[1][1:]

            # if query args contain 'raw' argument that is present and is equal to 'true' -> return raw video
            if request.query_args.get("raw", "false") == "true":
                # open video
                video = open(self._video_list[video_id], "rb")

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

            # if query args don't contain 'raw' argument, or it's equal to 'false' -> return body page
            else:
                # <h1> video 00000000-0000-0000-0000-00000000000000
                www_video_title = f"<h1> video {video_id} </h1>"
                # <source src="/tests/video-test.mp4" type="video/mp4">
                www_video_source = (f"<source"
                                    f" src=\"{self._video_www_path}?v={video_id}&raw=true\""
                                    f" type=\"video/{video_type}\">")

                with open(f"{WWW_DIRECTORY}/video-share/video_share_body.html", "r", encoding="utf-8") as f:
                    body = read_refactor_template(f, video_title=www_video_title, video_source=www_video_source)

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
        return Response(
            status=STATUS_CODE_NOT_FOUND,
            data=b'video not found')


def setup(server: Server) -> None:
    # ensure path exists
    if not os.path.isdir(VideoShareUnlistedPage.dir_path):
        os.makedirs(VideoShareUnlistedPage.dir_path)

    server.add_page(VideoShareUnlistedPage(server))
