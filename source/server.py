"""
HTTPy server code
"""


from source.classes import *
from source.network import *


class ClientHandle:
    """
    Client handling class
    """

    def __init__(self, con: Connection):
        self.con: Connection = con

    async def handle(self) -> None:
        """
        Handle the client
        """

        request = fetch_request(self.con)

    def close(self) -> None:
        """
        Closes the handle
        """

        self.con.writer.close()
