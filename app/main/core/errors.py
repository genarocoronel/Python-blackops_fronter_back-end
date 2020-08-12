class NotFoundError(Exception):
    """ App exception representing record not found """
    def __init(self, arg):
        self.args = arg

class NoDuplicateAllowed(Exception):
    """ App exception representing duplicate record not allowed """
    def __init(self, arg):
        self.args = arg

class BadRequestError(Exception):
    """ App exception representing bad request """
    def __init(self, arg):
        self.args = arg

class ConfigurationError(Exception):
    """ App exception representing misconfiguration error """
    def __init(self, arg):
        self.args = arg

class ServiceProviderError(Exception):
    """ App exception representing an external service provider error """
    def __init(self, arg):
        self.args = arg

class ServiceProviderLockedError(Exception):
    """ App exception representing an external service provider 'Locked' error """
    def __init(self, arg):
        self.args = arg

class StateMachineError(Exception):
    """ State machine errors"""
    def __init(self, arg):
        self.args = arg

class ForbiddenError(Exception):
    """ App exception representing permission error """
    def __init(self, arg):
        self.args = arg

class BadParamsError(Exception):
    """ App exception representing bad params/params not present. """
    def __init(self, arg):
        self.args = arg
