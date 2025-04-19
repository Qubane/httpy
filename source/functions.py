"""
Some generic functions
"""


from io import StringIO


def read_refactor_template(file: StringIO, **kwargs) -> str:
    """
    Reads and refactors a template file
    :param file: file
    :param kwargs: arguments to be refactored
    :return: bytes or str, depending on mode
    """

    key_args = {f"{{{x}}}" for x in kwargs.keys()}

    # output
    page = ""

    # go through each line
    with file:
        for line in file.readlines():
            # check if line argument is in key_args
            if (arg := line.strip()) in key_args:
                page += kwargs[arg[1:-1]]
            else:
                page += line

    # return page
    return page


def reads_refactor_template(data: str, **kwargs) -> str:
    """
    Reads and refactors a template file
    :param data: string data
    :param kwargs: arguments to be refactored
    :return: bytes or str, depending on mode
    """

    key_args = {f"{{{x}}}" for x in kwargs.keys()}

    # output
    page = ""

    # go through each line
    for line in data.split("\n"):
        # check if line argument is in key_args
        if (arg := line.strip()) in key_args:
            page += kwargs[arg[1:-1]]
        else:
            page += line

    # return page
    return page
