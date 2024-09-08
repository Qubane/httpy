import json
import os
import gzip
import brotli
import logging
from typing import Any
from src.config import FILE_MAN_PATH_MAP, FILE_MAN_COMPRESSED_PATH
from src.argparser import ARGS


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
        return self.cached

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

        if ARGS.compress_path:
            if not os.path.exists(FILE_MAN_COMPRESSED_PATH):
                os.makedirs(FILE_MAN_COMPRESSED_PATH)
            if not os.path.exists(os.path.join(FILE_MAN_COMPRESSED_PATH, "br")):
                os.mkdir(os.path.join(FILE_MAN_COMPRESSED_PATH, "br"))
            if not os.path.exists(os.path.join(FILE_MAN_COMPRESSED_PATH, "gz")):
                os.mkdir(os.path.join(FILE_MAN_COMPRESSED_PATH, "gz"))

        # generate path map
        self._generate_path_map()
        if ARGS.compress_path:
            self._add_compression()

    def _generate_path_map(self):
        """
        Generate full path map for HTTPy Server
        """

        if ARGS.verbose:
            logging.info("Started processing path map...")
        for key in FILE_MAN_PATH_MAP.keys():
            path = FILE_MAN_PATH_MAP[key]["path"]
            if not (os.path.exists(path) or os.path.exists(path[:-2])):
                logging.warning(f"Undefined path for '{key}' ({FILE_MAN_PATH_MAP[key]['path']})")
                continue
            if ARGS.verbose:
                logging.info(f"Processing path '{path}'")
            if key[-1] == "*":  # list whole directory
                keypath = path[:-2]
                for filepath in list_path(keypath):
                    web_path = os.path.join(keypath, path).replace("\\", "/")
                    if ARGS.verbose:
                        logging.info(f"Processing '*' path '{filepath}'")
                    file_dictionary = {
                        "-": File(filepath=filepath, cached=FILE_MAN_PATH_MAP[key].get("caching", False)),
                        "compressed": FILE_MAN_PATH_MAP[key].get("compress", True)}
                    self._path_map[web_path] = file_dictionary
            else:  # single file
                file_dictionary = {
                    "-": File(filepath=path, cached=FILE_MAN_PATH_MAP[key].get("caching", False)),
                    "compressed": FILE_MAN_PATH_MAP[key].get("compress", True)}
                self._path_map[key] = file_dictionary
        if ARGS.verbose:
            logging.info("Finished processing path map.")

    def _add_compression(self):
        """
        Compresses all files that should be compressed
        """




def generate_path_map(verbose: bool = False) -> dict[str, dict[str, Any]]:
    """
    Generate a full path map for HTTP server
    """

    # generate basic path map
    path_map = {}
    for key in FILE_MAN_PATH_MAP.keys():
        if not (os.path.exists(FILE_MAN_PATH_MAP[key]["path"]) or os.path.exists(FILE_MAN_PATH_MAP[key]["path"][:-2])):
            logging.warning(f"Undefined path for '{key}' ({FILE_MAN_PATH_MAP[key]['path']})")
            continue
        if key[-1] == "*":
            keypath = FILE_MAN_PATH_MAP[key]["path"][:-2]
            for path in list_path(keypath):
                webpath = f"{key[:-1]}{path.replace(keypath+'/', '')}"
                path_map[webpath] = {
                    "path": path,
                    "compress": FILE_MAN_PATH_MAP[key]["compress"]}
        else:
            path_map[key] = {
                "path": FILE_MAN_PATH_MAP[key]["path"],
                "compress": FILE_MAN_PATH_MAP[key]["compress"]}

    # add headers
    for val in path_map.values():
        extension = os.path.splitext(val["path"])[1]
        headers = {}
        match extension:
            case ".htm" | ".html":
                headers["Content-Type"] = "text/html"
            case ".css":
                headers["Content-Type"] = "text/css"
            case ".txt":
                headers["Content-Type"] = "text/plain"
            case ".js":
                headers["Content-Type"] = "text/javascript"
            case ".png":
                headers["Content-Type"] = "image/png"
            case ".webp":
                headers["Content-Type"] = "image/webp"
            case ".jpg" | ".jpeg":
                headers["Content-Type"] = "image/jpeg"
            case ".ico":
                headers["Content-Type"] = "image/*"
            case _:
                headers["Content-Type"] = "*/*"
        headers["Content-Length"] = os.path.getsize(val["path"])
        val["headers"] = headers

    # print list of paths
    if verbose:
        logging.info("LIST OF ALLOWED PATHS:")
        max_key_len = max([len(x) for x in path_map.keys()])
        max_val_len = max([len(x["path"]) for x in path_map.values()])
        logging.info(f"{'web': ^{max_key_len}} | {'path': ^{max_val_len}}")
        logging.info(f"{'='*max_key_len}=#={'='*max_val_len}")
        for key, val in path_map.items():
            logging.info(f"{key: <{max_key_len}} | {val['path']}")
        logging.info(f"END OF LIST. {len(path_map)}")

    return path_map


def compress_path_map(path_map: dict[str, dict[str, Any]],
                      path_prefix: str = "compress",
                      regen: bool = False,
                      verbose: bool = False):
    """
    Compresses all files using brotli
    """

    import gzip
    import htmlmin
    if not os.path.exists(path_prefix):
        os.mkdir(path_prefix)
    for val in path_map.values():
        filepath = f"{path_prefix}/{val["path"]}"
        if not val["compress"]:
            continue
        if not os.path.exists((dirs := os.path.dirname(filepath))):  # add missing folders
            os.makedirs(dirs)
        if not os.path.exists(filepath) or regen:
            if val["headers"]["Content-Type"] == "text/html":
                with open(filepath, "wb") as comp:
                    with open(val["path"], "rb") as file:
                        comp.write(
                            gzip.compress(htmlmin.minify(
                                file.read().decode("utf-8"),
                                remove_comments=True,
                                remove_empty_space=True,
                                remove_all_empty_space=True,
                                reduce_boolean_attributes=True).encode("utf-8")))
            else:
                with gzip.open(filepath, "wb") as comp:
                    with open(val["path"], "rb") as file:
                        comp.writelines(file)

        val["path"] = filepath
        val["headers"]["Content-Length"] = os.path.getsize(filepath)
        val["headers"]["Content-Encoding"] = "gzip"

    if verbose:
        logging.info("COMPRESSED PATH:")
        max_key_len = max([len(x) for x in path_map.keys()])
        max_val_len = max([len(x["path"]) for x in path_map.values()])
        max_size_len = max([len(x["headers"]["Content-Length"].__repr__()) for x in path_map.values()])
        logging.info(f"{'web': ^{max_key_len}} | {'path': ^{max_val_len}} | {'size': ^{max_size_len}}")
        logging.info(f"{'=' * max_key_len}=#={'=' * max_val_len}=#={'=' * max_size_len}")
        for key, val in path_map.items():
            logging.info(
                f"{key: <{max_key_len}} | "
                f"{val['path']: <{max_val_len}} | "
                f"{val['headers']['Content-Length']: <{max_size_len}}")
        logging.info(f"END OF LIST. {len(path_map)}")

    return path_map
