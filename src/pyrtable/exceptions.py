class RequestError(Exception):
    def __init__(self, message, type):
        self.type = type
        super().__init__(message)


__all__ = ['RequestError']
