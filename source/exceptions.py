from source.status import *


class ClientSideErrors(Exception):
    """
    It's all users fault :)
    """

    status = STATUS_CODE_BAD_REQUEST


class NotFoundError(ClientSideErrors):
    status = STATUS_CODE_NOT_FOUND


class ForbiddenError(ClientSideErrors):
    status = STATUS_CODE_FORBIDDEN


class ServerSideErrors(Exception):
    """
    O no :<
    """

    status = STATUS_CODE_INTERNAL_SERVER_ERROR


class InternalServerError(ServerSideErrors):
    status = STATUS_CODE_INTERNAL_SERVER_ERROR
