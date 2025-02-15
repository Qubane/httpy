"""
File Manager for controlling access to files
"""


import os
import logging
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
        self._filesize: int = 0
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
        self._filesize = os.path.getsize(self._filepath)

    def _define_type(self) -> None:
        """
        Defines type for self
        """

        match os.path.splitext(self._filepath)[1]:
            case ".htm" | ".html":
                self._filetype = "text/html"
            case ".css":
                self._filetype = "text/css"
            case ".txt":
                self._filetype = "text/plain"
            case ".js":
                self._filetype = "text/javascript"
            case ".png":
                self._filetype = "image/png"
            case ".webp":
                self._filetype = "image/webp"
            case ".jpg" | ".jpeg":
                self._filetype = "image/jpeg"
            case ".ico":
                self._filetype = "image/*"
            case ".pdf":
                self._filetype = "application/pdf"
            case ".json":
                self._filetype = "application/json"
            case _:
                self._filetype = "*/*"

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

    def get_full_data(self) -> bytes:
        """
        Returns all data from file
        """

        if self._cached is not None:  # file is cached
            return self._cached
        else:  # file is on the drive
            with open(self._filepath, "rb") as file:
                return file.read()

    @property
    def filepath(self) -> str:
        return self._filepath

    @property
    def filetype(self) -> str:
        return self._filetype

    @property
    def size(self) -> int:
        return self._filesize


class FileContainer:
    """
    Contains multiple files inside
    """

    def __init__(self, filepath: str, compressed: bool = True, cached: bool = False):
        self.uncompressed: File = File(filepath, cached=cached)
        self.compressed: bool = compressed

        if compressed:  # if compression is enabled
            # gzip compression
            c_filepath = os.path.join(Config.FILEMAN_COMPRESS_PATH, "gzip", filepath)
            if not os.path.exists(c_filepath):  # ensure existence
                if not os.path.exists(os.path.dirname(c_filepath)):
                    os.makedirs(os.path.dirname(c_filepath))
                with open(c_filepath, "wb") as f:
                    f.write(b'file')
            self.gzip_compressed: File = File(c_filepath, cached=cached)

            # brotli compression
            c_filepath = os.path.join(Config.FILEMAN_COMPRESS_PATH, "brotli", filepath)
            if not os.path.exists(c_filepath):
                if not os.path.exists(os.path.dirname(c_filepath)):
                    os.makedirs(os.path.dirname(c_filepath))
                with open(c_filepath, "wb") as f:
                    f.write(b'file')
            self.brotli_compressed: File = File(c_filepath, cached=cached)

            # actually compress files
            self.compress_files()

    def compress_files(self) -> None:
        """
        (Re)Compresses files
        """

        if not self.compressed:
            return

        import gzip
        import brotli
        chunk_size = 2**20 * 64  # 64 MiB
        with gzip.open(self.gzip_compressed.filepath, "wb") as compressed:
            with open(self.uncompressed.filepath, "rb") as file:
                compressed.writelines(file)
        with open(self.brotli_compressed.filepath, "wb") as compressed:
            br = brotli.Compressor()
            with open(self.uncompressed.filepath, "rb") as file:
                while data := file.read(chunk_size):
                    br.process(data)
                    compressed.write(br.flush())

    def update(self) -> None:
        """
        Updates files inside
        """

        self.uncompressed.update_file()
        if self.compressed:
            self.compress_files()
            self.gzip_compressed.update_file()
            self.brotli_compressed.update_file()


class FileManager:
    """
    File Manager (FileMan)
    """

    def __init__(
            self,
            allow_compression: bool = False,
            cache_everything: bool = False):
        """
        File manager class
        :param allow_compression: allows file compression
        :param cache_everything: caches EVERY file (do not use for big sites)
        """

        self._path_map: dict[str, FileContainer] = dict()
        # {webpath: FileContainer, webpath: FileContainer, ...}

        self._allow_compression: bool = allow_compression
        self._cache_everything: bool = cache_everything

    def update_paths(self):
        """
        Update's path map
        """

        import json
        if not os.path.isfile("cfg/paths.json"):
            raise FileNotFoundError("Missing path config")
        with open("cfg/paths.json", "r", encoding="utf-8") as file:
            paths: dict[str, dict[str, str | bool]] = json.loads(file.read())

        logging.info("Updating paths...")
        for webpath, arguments in paths.items():
            if webpath[-1] == "*":  # star path
                web_dirpath = webpath[:-1]
                real_dirpath = arguments["path"][:-1]
                if not os.path.exists(real_dirpath):  # dir not found
                    logging.warning(f"Unable to find directory at '{real_dirpath}'")
                    continue
                for entry in os.scandir(real_dirpath):
                    if not entry.is_file():
                        continue
                    web_filepath = f"{web_dirpath}{entry.path[len(real_dirpath):]}"
                    self.update_container(
                        webpath=web_filepath,
                        filepath=entry.path,
                        compressed=arguments.get("compressed"),
                        cached=arguments.get("cached"))
            else:  # direct path
                self.update_container(
                    webpath=webpath,
                    filepath=arguments["path"],
                    compressed=arguments.get("compressed"),
                    cached=arguments.get("cached"))
        logging.info("Paths updated.")

    def update_container(
            self,
            webpath: str,
            filepath: str,
            compressed: bool | None,
            cached: bool | None) -> None:
        """
        Updates file container at a given web path.
        :param webpath: web path relative to /
        :param filepath: path to uncompressed file
        :param compressed: allows compression for the file container. (Default True)
        :param cached: cache the file container. (Default False)
        """

        if not os.path.exists(filepath):
            logging.warning(f"Unable to find file at '{filepath}'")
            return

        if compressed is None:
            compressed = True if self._allow_compression else False
        if cached is None:
            cached = True if self._cache_everything else False

        if webpath in self._path_map:
            self._path_map[webpath].update()
        else:
            self._path_map[webpath] = FileContainer(
                filepath=filepath, compressed=compressed, cached=cached)

        logging.info(f"Processed '{webpath}' -> '{filepath}'")

    def exists(self, webpath) -> bool:
        """
        Checks if a given path exists
        :param webpath: client request path
        :return: True or False
        """

        return webpath in self._path_map

    def get_container(self, webpath) -> FileContainer:
        """
        Returns a file container
        :param webpath: client's request path
        :return: FileContainer
        :raises KeyError: when path is not found
        """

        if self.exists(webpath):
            return self._path_map[webpath]
        raise KeyError("Path not found")
