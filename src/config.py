# generic
LOGGER_PATH = "logs"
BUFFER_LENGTH = 2**16           # 64 KiB
BUFFER_MAX_SIZE = 2**30 * 0.5   # 512 MiB
PATH_MAX_LENGTH = 255           # actually 256
PATH_ARGS_MAX_COUNT = 32
PATH_HEADER_MAX_COUNT = 256

# threading
CLIENT_MAX_AMOUNT = 2**15       # max requests at once, after which the connections are dropped
CLIENT_MAX_PROCESS = 64         # max processing threads at once

# sockets
SOCKET_TIMEOUT = 10.0
SOCKET_ACK_INTERVAL = 0.005
SOCKET_TIMER = SOCKET_TIMEOUT / SOCKET_ACK_INTERVAL

# API
API_FILE_RANDOM_MIN_SIZE_LIMIT = 1              # 1 byte
API_FILE_RANDOM_MAX_SIZE_LIMIT = 2**30 * 5      # 5 GiB
API_VERSIONS = {
    "APIv1": {"supported": True}
}

# file manager
FILE_MAN_COMPRESSED_PATH = "compress"
FILE_MAN_PATH_MAP = {
    # external
    "/":                {"path": "www/index.html", "compress": True},
    "/about":           {"path": "www/about.html", "compress": True},
    "/testing":         {"path": "www/testing.html", "compress": True},
    "/projects":        {"path": "www/projects.html", "compress": True},
    "/images/*":        {"path": "www/images/*", "compress": False},
    "/scripts/*":       {"path": "www/scripts/*", "compress": True},
    "/robots.txt":      {"path": "www/robots.txt", "compress": False},
    "/favicon.ico":     {"path": "www/favicon.ico", "compress": True},
    "/css/styles.css":  {"path": "www/css/styles.css", "compress": True},

    "/study":           {"path": "www/study.html", "compress": True},
    "/study/books/*":   {"path": "www/pdf/*", "compress": True},

    "/testing/pyscript": {"path": "www/pyscript.html", "compress": True},
}
