import os
import gzip
import brotli
import logging
from src.argparser import ARGS
from src.config import BUFFER_LENGTH
from collections.abc import Generator


def list_path(path) -> list[str]:
    if os.path.isfile(path):
        return [path]
    paths = []
    for file in os.listdir(path):
        paths += list_path(f"{path}/{file}")
    return paths


class File:
    """
    Class that stores information about the file
    """

    def __init__(self, filepath: str, **kwargs):
        """
        :param filepath: path to file
        :key cached: always store file in ram
        """

        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File '{self.filepath}' not found.")

        self._filepath: str = filepath
        self._cached: bool = kwargs.get("cached", False)
        self._data: bytes = b''

        # http related
        self._content_length: int = 0
        self._content_type: str = "*/*"

        self.update_data()

    def update_data(self) -> None:
        """
        Updates data in file
        """

        if self._cached:
            with open(self.filepath, "rb") as file:
                self._data = file.read()
        self._content_length = os.path.getsize(self.filepath)

    def _define_type(self) -> None:
        """
        Defines type for itself
        """

        extension = os.path.splitext(self.filepath)[1]
        match extension:
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
            case _:
                self._content_type = "*/*"

    def get_data_stream(self) -> Generator[bytes, None, None]:
        """
        Yields data from file
        """

        if self.cached:
            for i in range(0, len(self._data), BUFFER_LENGTH):
                yield self._data[i:i+BUFFER_LENGTH]
        else:
            with open(self.filepath, "rb") as file:
                while chunk := file.read(BUFFER_LENGTH):
                    yield chunk

    @property
    def filepath(self) -> str:
        return self._filepath

    @property
    def content_length(self) -> int:
        return self._content_length

    @property
    def content_type(self) -> str:
        return self._content_type

    @property
    def cached(self) -> bool:
        return self._cached

    def __repr__(self) -> str:
        return f"[file at: '{self._filepath}']"


class FileManager:
    """
    Class that manages files
    """

    def __init__(self):
        self._path_map: dict[str, dict[str, File]] = dict()
        # webpath: {"-": ..., "br": ..., "gz": ..., "compressed": ...}
        #                      nullable   nullable

        self._compressed_br_path: str = ""
        self._compressed_gz_path: str = ""

    def configure(self, path_config: dict[str, dict], compress_path: bool, compressed_path: str) -> None:
        """
        Configures new path map to the file manager
        """

        # add compress path directories
        if compress_path:
            if not os.path.exists(compressed_path):
                os.makedirs(compressed_path)
            self._compressed_br_path: str = os.path.join(compressed_path, "br")
            if not os.path.exists(self._compressed_br_path):
                os.mkdir(self._compressed_br_path)
            self._compressed_gz_path: str = os.path.join(compressed_path, "gz")
            if not os.path.exists(self._compressed_gz_path):
                os.mkdir(self._compressed_gz_path)

        # generate a path map
        self._generate_path_map(path_config=path_config)
        if compress_path:
            self._add_compression()

    def _generate_path_map(self, path_config: dict[str, dict]) -> None:
        """
        Generate full path map for HTTPy Server
        """

        if ARGS.verbose:
            logging.info("Started processing path map...")
        for key in path_config.keys():
            path = path_config[key]["path"]

            # check for file's existence
            if not (os.path.exists(path) or os.path.exists(path[:-2])):
                logging.warning(f"Undefined path for '{key}' ({path_config[key]['path']})")
                continue

            if ARGS.verbose:
                logging.info(f"Processing path '{path}'")
            if key[-1] == "*":  # lists whole directory
                keypath = path[:-2]
                for filepath in list_path(keypath):
                    web_path = key[:-1] + filepath.replace(keypath + "/", "")
                    if ARGS.verbose:
                        logging.info(f"Processing '*' path '{filepath}'")
                    file_dictionary = {
                        "-": File(filepath=filepath, cached=path_config[key].get("caching", False)),
                        "compressed": path_config[key].get("compress", True)}
                    self._path_map[web_path] = file_dictionary
            else:  # single file
                file_dictionary = {
                    "-": File(filepath=path, cached=path_config[key].get("caching", False)),
                    "compressed": path_config[key].get("compress", True)}
                self._path_map[key] = file_dictionary
        if ARGS.verbose:
            logging.info("Finished processing path map.")

    def _add_compression(self) -> None:
        """
        Adds compression to current path map. Excludes any
        """

        if ARGS.verbose:
            logging.info("Started file compression...")
        for file_dictionary in self._path_map.values():
            if ARGS.verbose:
                logging.info(f"Processing file '{file_dictionary['-'].filepath}'")

            # skip if not compressed
            if not file_dictionary["compressed"]:
                if ARGS.verbose:
                    logging.info(f"Skipping file '{file_dictionary['-'].filepath}'; compression forced off")
                continue

            # brotli compression
            path = os.path.join(self._compressed_br_path, file_dictionary["-"].filepath)
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            with open(path, "wb") as compress:
                br = brotli.Compressor()
                with open(file_dictionary["-"].filepath, "rb") as file:
                    while chunk := file.read(65536):
                        br.process(chunk)
                        compress.write(br.flush())
            file_dictionary["br"] = File(filepath=path, cached=file_dictionary["-"].cached)
            if ARGS.verbose:
                logging.info(f"Finished brotli compression for file '{file_dictionary['-'].filepath}'")

            # gzip compression
            path = os.path.join(self._compressed_gz_path, file_dictionary["-"].filepath)
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            with gzip.open(path, "wb") as compress:
                with open(file_dictionary["-"].filepath, "rb") as file:
                    compress.writelines(file)
            file_dictionary["gz"] = File(filepath=path, cached=file_dictionary["-"].cached)
            if ARGS.verbose:
                logging.info(f"Finished gzip compression for file '{file_dictionary['-'].filepath}'")
        if ARGS.verbose:
            logging.info("Finished file compression.")

    def exists(self, web_path: str) -> bool:
        """
        Returns True if given path is valid, False in any other case
        :param web_path: page path
        :return: boolean
        """

        return self._path_map.get(web_path) is not None

    def get_file(self, web_path: str, encoding: str = "-") -> File:
        """
        Returns File for given web path
        :param web_path: page path
        :param encoding: compression used
        :return: file with given encoding
        :raises KeyError: when path doesn't exist
        """

        return self._path_map[web_path][encoding]

    def get_file_dict(self, web_path: str) -> dict[str, File | bool]:
        """
        Returns file dictionary
        :param web_path: page path
        :return: file dictionary
        :raises KeyError: when path doesn't exist
        """

        return self._path_map[web_path]
