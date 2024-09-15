"""
File Manager for controlling access to files
"""


class File:
    """
    File
    """

    def __init__(self, filepath: str, compress: bool = True, cache: bool = False):
        pass


class FileContainer:
    """
    Contains multiple files inside
    """

    def __init__(self, filepath: str):
        pass


class FileManager:
    """
    File Manager (FileMan)
    """

    def __init__(self):
        self._path_map: dict
