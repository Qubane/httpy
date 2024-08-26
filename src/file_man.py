import os
from src.config import FILE_MAN_PATH_MAP, FILE_MAN_VERBOSE


def list_path(path) -> list[str]:
    if os.path.isfile(path):
        return [path]
    paths = []
    for file in os.listdir(path):
        paths += list_path(f"{path}/{file}")
    return paths


def generate_path_map():
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

    if FILE_MAN_VERBOSE:
        print("LIST OF ALLOWED PATHS:")
        max_key_len = max([len(x) for x in path_map.keys()])
        max_val_len = max([len(x.__repr__()) for x in path_map.values()])
        print(f"\t{'web': ^{max_key_len}} | {'path': ^{max_val_len}}\n"
              f"\t{'='*max_key_len}=#={'='*max_val_len}")
        for key, val in path_map.items():
            print(f"\t{key: <{max_key_len}} | {val}")
        print("END OF LIST.")
    return path_map


PATH_MAP = generate_path_map()
