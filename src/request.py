class Request:
    """
    Just a request
    """

    def __init__(self):
        self.type: str = ""
        self.path: str = ""

    @staticmethod
    def create(raw_request: bytes):
        """
        Creates self class from raw request
        :param raw_request: bytes
        :return: self
        """

        # new request
        request = Request()

        # fix type and path
        request.type = raw_request[:raw_request.find(b' ')].decode("ascii")
        request.path = raw_request[len(request.type)+1:raw_request.find(b' ', len(request.type)+1)].decode("ascii")

        # decode headers
        for raw_header in raw_request.split(b'\r\n'):
            if len(pair := raw_header.decode("ascii").split(":")) == 2:
                key, val = pair
                val = val.strip()

                # set attribute to key value pair
                setattr(request, key, val)

        # return request
        return request

    def __str__(self):
        return '\n'.join([f"{key}: {val}" for key, val in self.__dict__.items()])
