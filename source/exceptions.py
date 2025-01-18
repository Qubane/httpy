class ClientSideErrors(Exception):
    """
    It's all users fault :)
    """

    def __init__(self, *args):
        super().__init__(*args)


class NotFoundError(ClientSideErrors):
    def __init__(self, *args):
        super().__init__(*args)


class ForbiddenError(ClientSideErrors):
    def __init__(self, *args):
        super().__init__(*args)
