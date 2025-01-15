import os
import logging
import logging.handlers


READ_BUFFER_SIZE = 2 ** 15
WRITE_BUFFER_SIZE = 2 ** 24

MAX_QUERY_ARGS = 16

VARS_DIRECTORY = "var"
LOGS_DIRECTORY = "logs"
WEB_DIRECTORY = "www"


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
                maxBytes=2**20 * 32,  # 32 MiB
                backupCount=5),
            logging.StreamHandler()])
