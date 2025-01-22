class ClientSideErrors(Exception):
    """
    It's all users fault :)
    """


class NotFoundError(ClientSideErrors):
    pass


class ForbiddenError(ClientSideErrors):
    pass


class ServerSideErrors(Exception):
    """
    O no :<
    """


class InternalServerError(ServerSideErrors):
    pass
