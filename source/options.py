"""
Some configurations for the HTTPy server
"""


import os
import logging
import logging.handlers


# internal configurations
WRITE_BUFFER_SIZE: int = 2 ** 10 * 16

# directories
TEMP_DIRECTORY: str = "temp"
LOGS_DIRECTORY: str = "logs"
ASSETS_DIRECTORY: str = "assets"


def initialize():
    """
    Initializes some of the options
    """

    # ensure directories exist
    if not os.path.isdir(TEMP_DIRECTORY):
        os.makedirs(TEMP_DIRECTORY)
    if not os.path.isdir(LOGS_DIRECTORY):
        os.makedirs(LOGS_DIRECTORY)
    if not os.path.isdir(ASSETS_DIRECTORY):
        os.makedirs(ASSETS_DIRECTORY)

    # logging
    logging.basicConfig(
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
        format="[{asctime}] [{levelname:<8}] {name}: {message}",
        handlers=[
            logging.handlers.RotatingFileHandler(
                filename=f"{LOGS_DIRECTORY}/server.log",
                encoding="utf-8",
                maxBytes=2**20 * 2,  # 2 MiB
                backupCount=5),
            logging.StreamHandler()])
