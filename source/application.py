"""
Main application file
"""


import asyncio


class App:
    """
    Main application class
    """

    def __init__(self):
        self.running_task: asyncio.Task | None = None

        self.address: tuple[str, int] | None = None
        self.ssl: tuple[str, str] | None = None

        self.server: asyncio.Server | None = None

    def run(self, address: tuple[str, int], ssl: tuple[str, str] | None = None) -> None:
        """
        Runs the application
        """

        # assign address and ssl keys
        self.address = address
        self.ssl = ssl

        # create new task
        try:
            self.running_task = asyncio.create_task(self._run_server())
        except asyncio.CancelledError:
            pass

    def quit(self) -> None:
        """
        Quits the application
        """

        self.running_task.cancel()

    async def _run_server(self):
        """
        Run server coroutine
        """


