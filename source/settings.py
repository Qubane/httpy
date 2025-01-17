import os
import logging
import logging.handlers


READ_BUFFER_SIZE: int = 2 ** 15
WRITE_BUFFER_SIZE: int = 2 ** 24

MAX_QUERY_ARGS: int = 16

VARS_DIRECTORY: str = "var"
LOGS_DIRECTORY: str = "logs"
WEB_DIRECTORY: str = "www"

PAGE_NEWS_TAGS: set[str] = {"general", "youtube", "scrap-mechanic"}


def init():
    # create 'var' directory
    if not os.path.isdir(VARS_DIRECTORY):
        os.mkdir(VARS_DIRECTORY)

    # create 'logs' directory
    if not os.path.isdir(LOGS_DIRECTORY):
        os.mkdir(LOGS_DIRECTORY)

    # setup logging
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
