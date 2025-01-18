class ClientSideErrors(Exception):
    """
    It's all users fault :)
    """

    def __init__(self, *args):
        super().__init__(*args)


class NotFound(ClientSideErrors):
    def __init__(self, *args):
        super().__init__(*args)
