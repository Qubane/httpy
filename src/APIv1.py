import random
from ssl import SSLSocket
from src.request import Request


API_FILE_RANDOM_MIN_SIZE_LIMIT = 1
API_FILE_RANDOM_MAX_SIZE_LIMIT = 2**30 * 2


def random_data_gen(size: int) -> bytes:
    """
    Generates SIZE bytes of random data in 64kib chunks
    :param size: bytes to generate
    :return: random bytes
    """

    data = bytearray()
    int_size = size // 65536
    for _ in range(int_size):
        data += random.randbytes(65536)
    data += random.randbytes((int_size * 65536) - size)

    return data


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


def respond(client: SSLSocket, request: Request) -> tuple[int, bytes, dict]:
    """
    Respond to clients API request
    """

    # decode API request
    split_path = request.path.split("/")
    api_level1 = split_path[2]
    api_request = split_path[3]

    # do something with it (oh god)
    if api_level1 == "file":
        if api_request == "random":
            # get size
            size_str = request.path_args.get("size", "16mib")
            size = decode_size(size_str)

            # check size
            if size < API_FILE_RANDOM_MIN_SIZE_LIMIT or size > API_FILE_RANDOM_MAX_SIZE_LIMIT:
                return 400, b'', {}

            return 200, random_data_gen(size), {}
        else:
            return 400, b'', {}
    else:
        return 400, b'', {}
