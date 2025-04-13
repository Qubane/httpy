"""
Some configurations for the HTTPy server
"""


import os


# internal configurations
WRITE_BUFFER_SIZE: int = 2 ** 10 * 16

# directories
TEMP_DIRECTORY: str = "temp"
LOGS_DIRECTORY: str = "logs"
ASSETS_DIRECTORY: str = "assets"

# ensure directories exist
if not os.path.isdir(TEMP_DIRECTORY):
    os.makedirs(TEMP_DIRECTORY)
if not os.path.isdir(LOGS_DIRECTORY):
    os.makedirs(LOGS_DIRECTORY)
if not os.path.isdir(ASSETS_DIRECTORY):
    os.makedirs(ASSETS_DIRECTORY)
