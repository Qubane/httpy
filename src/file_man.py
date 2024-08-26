import os
from typing import Any
from src.config import FILE_MAN_PATH_MAP, FILE_MAN_VERBOSE


def list_path(path) -> list[str]:
    if os.path.isfile(path):
        return [path]
    paths = []
    for file in os.listdir(path):
        paths += list_path(f"{path}/{file}")
    return paths


def generate_path_map() -> dict[str, dict[str, Any]]:
    """
    Generate a full path map for HTTP server
    """

    # generate basic path map
    path_map = {}
    for key in FILE_MAN_PATH_MAP.keys():
        if not (os.path.exists(FILE_MAN_PATH_MAP[key]["path"]) or os.path.exists(FILE_MAN_PATH_MAP[key]["path"][:-2])):
            if FILE_MAN_VERBOSE:
                print(f"Undefined path for '{key}' ({FILE_MAN_PATH_MAP[key]['path']})")
            continue
        if key[-1] == "*":
            keypath = FILE_MAN_PATH_MAP[key]["path"][:-2]
            for path in list_path(keypath):
                webpath = f"{key[:-1]}{path.replace(keypath+'/', '')}"
                path_map[webpath] = {"path": path}
        else:
            path_map[key] = {"path": FILE_MAN_PATH_MAP[key]["path"]}

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
            case ".png":
                headers["Content-Type"] = "image/png"
            case ".webp":
                headers["Content-Type"] = "image/avif"
            case ".jpg" | ".jpeg":
                headers["Content-Type"] = "image/jpeg"
        headers["Content-Length"] = os.path.getsize(val["path"])
        val["headers"] = headers

    # print list of paths
    if FILE_MAN_VERBOSE:
        print("LIST OF ALLOWED PATHS:")
        max_key_len = max([len(x) for x in path_map.keys()])
        max_val_len = max([len(x["path"]) for x in path_map.values()])
        print(f"\t{'web': ^{max_key_len}} | {'path': ^{max_val_len}}\n"
              f"\t{'='*max_key_len}=#={'='*max_val_len}")
        for key, val in path_map.items():
            print(f"\t{key: <{max_key_len}} | {val['path']}")
        print("END OF LIST.", len(path_map), end="\n\n")

    return path_map


def compress_path_map(path_map: dict[str, dict[str, Any]], path_prefix: str = "compress", regen: bool = False):
    """
    Compresses all files using gzip
    """

    import gzip
    if not os.path.exists(path_prefix):
        os.mkdir(path_prefix)
    for val in path_map.values():
        filepath = f"{path_prefix}/{val["path"]}"
        if not os.path.exists((dirs := os.path.dirname(filepath))):  # add missing folders
            os.makedirs(dirs)
        if not os.path.exists(filepath) or regen:
            with gzip.open(filepath, "wb") as comp:  # compress
                with open(val["path"], "rb") as file:
                    comp.writelines(file)
        val["path"] = filepath
        val["headers"]["Content-Length"] = os.path.getsize(filepath)

    if FILE_MAN_VERBOSE:
        print("COMPRESSED PATH MAP:")
        max_len = max([len(x["path"]) for x in path_map.values()])
        for val in path_map.values():
            print(f"\t'{val['path']: <{max_len}}' {val['headers']['Content-Length']} bytes")
        print("END OF LIST.", len(path_map), end="\n\n")

    return path_map


PATH_MAP = compress_path_map(generate_path_map())
