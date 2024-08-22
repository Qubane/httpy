import random
from src.socks import *
from ssl import SSLSocket
from src.request import Request


async def respond(client: SSLSocket, request: Request) -> tuple[int, bytes]:
    """
    Respond to clients API request
    """

    # decode API request
    split_path = request.path.split("/")
    api_level1 = split_path[2]
    api_level2 = split_path[3]
    api_request = split_path[4]

    # do something with it (oh god)
    if api_level1 == "file":
        if api_level2 == "generated":
            if api_request == "1gib":
                return 200, random.randbytes(1048576)
            elif api_request == "5gib":
                return 200, random.randbytes(1048576)
            elif api_request == "10gib":
                return 200, random.randbytes(1048576)
            elif api_request == "20gib":
                return 200, random.randbytes(1048576)
            else:
                return 400, b''
        else:
            return 400, b''
    else:
        return 400, b''
