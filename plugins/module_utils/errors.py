from __future__ import absolute_import, division, print_function

__metaclass__ = type


class IPFabricError(Exception):
    pass


class AuthError(IPFabricError):
    pass


class UnexpectedAPIResponse(IPFabricError):
    def __init__(self, status, data):
        self.message = "Unexpected response - {0} {1}".format(status, data)
        super(UnexpectedAPIResponse, self).__init__(self.message)
