import random
from collections.abc import Generator
from ssl import SSLSocket
from src.config import *
from src.request import *
from src.status_code import *


def random_data_gen(size: int, chunk_size: int = 65536) -> Generator[bytes, None, None]:
    """
    Generates SIZE bytes of random data in CHUNK_SIZE byte chunks
    :param size: bytes to generate
    :param chunk_size: size of each chunk (bytes)
    :return: random bytes
    """

    int_size = size // chunk_size
    for _ in range(int_size):
        yield random.randbytes(chunk_size)
    if (final_size := (int_size * chunk_size) - size) > 0:
        yield random.randbytes(final_size)


def decode_size(size: str) -> int:
    """
    Decodes size string like '128mib' and converts it to int size in bytes
    :param size: size string
    :return: number of bytes
    """

    # split string into number and size modifier
    int_string = ""
    size_modifier = ""
    integer = True
    for char in size:
        if not char.isdigit():
            integer = False
        if integer:
            int_string += char
        else:
            size_modifier += char
    size = int(int_string)

    # multiply size by size modifier
    match size_modifier:
        case "b":  # bytes
            pass
        case "kib":  # kibibytes
            size *= 2**10
        case "mib":  # mebibytes
            size *= 2**20
        case "gib":  # gibibytes
            size *= 2**30
        case _:
            pass

    return size


def api_call(client: SSLSocket, request: Request) -> Response:
    """
    Respond to clients API request
    """

    # decode API request
    split_path = request.path.split("/", maxsplit=16)[1:]

    # do something with it (oh god)
    if len(split_path) > 1 and split_path[1] == "file":
        if len(split_path) > 2 and split_path[2] == "random":
            # get size
            size_str = request.path_args.get("size", "16mib")
            size = decode_size(size_str)

            # check size
            if size < API_FILE_RANDOM_MIN_SIZE_LIMIT or size > API_FILE_RANDOM_MAX_SIZE_LIMIT:
                return Response(status=STATUS_CODE_BAD_REQUEST)

            return Response(
                status=STATUS_CODE_OK,
                headers={"Content-Length": str(size)},
                data_stream=random_data_gen(size))
    return Response(status=STATUS_CODE_BAD_REQUEST)
