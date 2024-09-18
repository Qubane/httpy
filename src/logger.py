"""
Exception / request logging for HTTPy Server
"""


from src.config import Config


def init_logger():
    import os
    import logging
    if not os.path.exists(f"{Config.LOGGING_PATH}"):
        os.makedirs(f"{Config.LOGGING_PATH}")
    if os.path.isfile(f"{Config.LOGGING_PATH}/latest.log") and os.path.getsize(f"{Config.LOGGING_PATH}/latest.log") > 0:
        import gzip
        from datetime import datetime
        with open(f"{Config.LOGGING_PATH}/latest.log", "rb") as file:
            with gzip.open(f"{Config.LOGGING_PATH}/{datetime.now().strftime('%d-%m-%y %H-%M-%S')}.log.gz",
                           "wb") as comp:
                comp.writelines(file)
        os.remove(f"{Config.LOGGING_PATH}/latest.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(f"{Config.LOGGING_PATH}/latest.log"),
            logging.StreamHandler()
        ]
    )


init_logger()
