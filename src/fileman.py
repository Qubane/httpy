"""
File Manager for controlling access to files
"""


import os
from collections.abc import Generator
from src.config import Config


class File:
    """
    File
    """

    def __init__(self, filepath: str, cached: bool = False):
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File '{filepath}' doesn't exist")

        self._filepath: str = filepath
        self._filetype: str = "*/*"
        self._cached: bytes | None = b'empty' if cached else None

        self._define_type()
        self.update_file()

    def update_file(self) -> None:
        """
        Updates data inside a file
        """

        if self._cached is not None:
            with open(self._filepath, "rb") as file:
                self._cached = file.read()

    def _define_type(self) -> None:
        """
        Defines type for self
        """

        match os.path.splitext(self._filepath)[1]:
            case ".htm" | ".html":
                self._content_type = "text/html"
            case ".css":
                self._content_type = "text/css"
            case ".txt":
                self._content_type = "text/plain"
            case ".js":
                self._content_type = "text/javascript"
            case ".png":
                self._content_type = "image/png"
            case ".webp":
                self._content_type = "image/webp"
            case ".jpg" | ".jpeg":
                self._content_type = "image/jpeg"
            case ".ico":
                self._content_type = "image/*"
            case ".pdf":
                self._content_type = "application/pdf"
            case ".json":
                self._content_type = "application/json"
            case _:
                self._content_type = "*/*"

    def get_data_stream(self) -> Generator[bytes, None, None]:
        """
        Yields bytes from file
        """

        if self._cached is not None:  # file is cached
            for i in range(0, len(self._cached), Config.SOCKET_SEND_SIZE):
                yield self._cached[i:i + Config.SOCKET_SEND_SIZE]
        else:  # file is on the drive
            with open(self._filepath, "rb") as file:
                while data := file.read(Config.SOCKET_SEND_SIZE):
                    yield data


class FileContainer:
    """
    Contains multiple files inside
    """

    def __init__(self, filepath: str, compress: bool = True, cache: bool = False):
        self.uncompressed: File = File(filepath, cached=cache)
        self.compressed: bool = compress

        if compress:  # if compression is enabled
            c_filepath = os.path.join(Config.FILEMAN_COMPRESS_PATH, "gzip", filepath)
            self.gzip_compressed: File = File(c_filepath, cached=cache)
            c_filepath = os.path.join(Config.FILEMAN_COMPRESS_PATH, "brotli", filepath)
            self.brotli_compressed: File = File(c_filepath, cached=cache)


class FileManager:
    """
    File Manager (FileMan)
    """

    def __init__(self):
        self._path_map: dict
