class NotFoundError(Exception):
    """ App exception representing record not found """
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