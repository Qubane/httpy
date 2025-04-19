"""
Some generic functions
"""


def read_refactor_template(path: str, mode: str, **kwargs) -> bytes | str:
    """
    Reads and refactors a template file
    :param path: path to file
    :param mode: mode (rb or r)
    :param kwargs: arguments to be refactored
    :return: bytes or str, depending on mode
    """
