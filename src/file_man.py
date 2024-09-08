import os
import gzip
import brotli
import logging
from typing import Any
from src.config import FILE_MAN_PATH_MAP, FILE_MAN_COMPRESSED_PATH


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
        :key compress: turn on compression for the file
        :key ram_stored: always store file in ram
        """

        self.filepaths: list[str] = [filepath, "", ""]
        # 0 - uncompressed path
        # 1 - brotli path
        # 2 - gzip path
        self._compress: bool = kwargs.get("compress", True)

        self._ram_stored: bool = kwargs.get("ram_stored", False)
        self._data: list[bytes] = [b'' for _ in range(3)]
        # 0 - uncompressed data
        # 1 - brotli data
        # 2 - gzip data

        if not os.path.isfile(self.filepaths[0]):
            raise FileNotFoundError(f"File '{self.filepaths[0]}' not found.")

    def update_data(self):
        """
        Updates data in file
        """

        if self._ram_stored:
            with open(self.filepaths[0], "rb") as file:
                self._data[0] = file.read()                     # uncompressed data
            if self._compress:
                self._data[1] = brotli.compress(self._data[0])  # br compressed data
                self._data[2] = brotli.compress(self._data[0])  # gz compressed data
        elif self._compress:
            # brotli compression
            with open(self.filepath_br, "wb") as compressed:
                br = brotli.Compressor()
                with open(self.filepath, "rb") as file:
                    while chunk := file.read(65536):
                        br.process(chunk)
                        compressed.write(br.flush())
            # gzip compression
            with gzip.open(self.filepath_gz, "wb") as compressed:
                with open(self.filepath, "rb") as file:
                    compressed.writelines(file)

    @property
    def filepath(self):
        return self.filepaths[0]

    @property
    def filepath_br(self):
        return self.filepaths[1]

    @property
    def filepath_gz(self):
        return self.filepaths[2]

    def __repr__(self):
        return self.filepaths.__repr__()


class FileManager:
    """
    Class that manages files
    """

    def __init__(self):
        self._path_map: dict[str, File] = dict()

        if not os.path.exists(FILE_MAN_COMPRESSED_PATH):
            os.makedirs(FILE_MAN_COMPRESSED_PATH)
            os.mkdir(os.path.join(FILE_MAN_COMPRESSED_PATH, "br"))
            os.mkdir(os.path.join(FILE_MAN_COMPRESSED_PATH, "gz"))

    def get(self, path: str, default=None) -> File:
        return self._path_map.get(path, default)


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
