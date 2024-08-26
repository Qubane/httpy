import os
from typing import Any
from src.config import FILE_MAN_PATH_MAP, FILE_MAN_VERBOSE, FILE_MAN_COMPRESS


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
            case ".js":
                headers["Content-Type"] = "text/javascript"
            case ".png":
                headers["Content-Type"] = "image/png"
            case ".webp":
                headers["Content-Type"] = "image/avif"
            case ".jpg" | ".jpeg":
                headers["Content-Type"] = "image/jpeg"
            case _:
                headers["Content-Type"] = "*/*"
        val["headers"] = headers
        headers["Content-Length"] = os.path.getsize(val["path"])

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
    Compresses all files using brotli
    """

    import brotli
    from src.minimizer import minimize_html
    if not os.path.exists(path_prefix):
        os.mkdir(path_prefix)
    for val in path_map.values():
        filepath = f"{path_prefix}/{val["path"]}"
        if val["headers"]["Content-Type"].split("/")[0] == "image":  # ignore images
            continue
        if not os.path.exists((dirs := os.path.dirname(filepath))):  # add missing folders
            os.makedirs(dirs)
        if not os.path.exists(filepath) or regen:
            # brotli compress
            if val["headers"]["Content-Type"] == "text/html":
                with open(filepath, "wb") as comp:
                    with open(val["path"], "rb") as file:
                        comp.write(
                            brotli.compress(minimize_html(file.read()))
                        )
            else:
                with open(filepath, "wb") as comp:
                    br = brotli.Compressor()
                    with open(val["path"], "rb") as file:
                        while (chunk := file.read(65536)):
                            br.process(chunk)
                            comp.write(br.flush())

        val["path"] = filepath
        val["headers"]["Content-Length"] = os.path.getsize(filepath)
        val["headers"]["Content-Encoding"] = "br"

    if FILE_MAN_VERBOSE:
        print("COMPRESSED PATH:")
        max_key_len = max([len(x) for x in path_map.keys()])
        max_val_len = max([len(x["path"]) for x in path_map.values()])
        max_size_len = max([len(x["headers"]["Content-Length"].__repr__()) for x in path_map.values()])
        print(f"\t{'web': ^{max_key_len}} | {'path': ^{max_val_len}} | {'size': ^{max_size_len}}\n"
              f"\t{'=' * max_key_len}=#={'=' * max_val_len}=#={'=' * max_size_len}")
        for key, val in path_map.items():
            print(f"\t{key: <{max_key_len}} | "
                  f"{val['path']: <{max_val_len}} | "
                  f"{val['headers']['Content-Length']: <{max_size_len}}")
        print("END OF LIST.", len(path_map), end="\n\n")

    return path_map


PATH_MAP = generate_path_map()
if FILE_MAN_COMPRESS:
    PATH_MAP = compress_path_map(PATH_MAP, regen=True)
