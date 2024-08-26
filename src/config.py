# generic
BUFFER_LENGTH = 65536           # 64 KiB
BUFFER_MAX_SIZE = 2**30 * 0.5   # 512 MiB
CLIENT_MAX_AMOUNT = 512         # max requests at once, after which the connections are dropped
CLIENT_MAX_PROCESS = 32         # max processing threads at once

# API
API_FILE_RANDOM_MIN_SIZE_LIMIT = 1              # 1 byte
API_FILE_RANDOM_MAX_SIZE_LIMIT = 2**30 * 5      # 5 GiB
API_VERSIONS = {
    "APIv1": {"supported": True}
}

# file manager
FILE_MAN_VERBOSE = True
FILE_MAN_PATH_MAP = {
    # external
    "/":                {"path": "www/index.html"},
    "/about":           {"path": "www/about.html"},
    "/testing":         {"path": "www/testing.html"},
    "/projects":        {"path": "www/projects.html"},
    "/images/*":        {"path": "www/images/*"},
    "/scripts/*":       {"path": "www/scripts/*"},
    "/robots.txt":      {"path": "www/robots.txt"},
    "/favicon.ico":     {"path": "www/favicon.ico"},
    "/css/styles.css":  {"path": "www/css/styles.css"},
}
