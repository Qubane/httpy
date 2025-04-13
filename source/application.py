"""
Main application file
"""


import asyncio


class App:
    """
    Main application class
    """

    def __init__(self, address: tuple[str, int], ssl: tuple[str, str] | None = None):
        self.running_task: asyncio.Task | None = None

        self.address: tuple[str, int] | None = address
        self.ssl: tuple[str, str] | None = ssl

        self.server: asyncio.Server | None = None

    def run(self) -> None:
        """
        Runs the application
        """

        asyncio.run(self.run_coro())

    async def run_coro(self):
        """
        Runs the application. Is a coroutine
        """

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


