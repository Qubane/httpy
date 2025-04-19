"""
Some generic functions
"""


def read_refactor_template(path: str, **kwargs) -> str:
    """
    Reads and refactors a template file
    :param path: path to file
    :param kwargs: arguments to be refactored
    :return: bytes or str, depending on mode
    """

    key_args = {f"{{{x}}}" for x in kwargs.keys()}

    # output
    page = ""

    # read file
    with open(path, "r", encoding="utf-8") as f:
        # go through each line
        for line in f.readlines():
            # check if line argument is in key_args
            if (arg := line.strip()) in key_args:
                page += kwargs[arg[1:-1]]
            else:
                page += line

    # return page
    return page
