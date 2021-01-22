class RequestError(Exception):
    def __init__(self, message, error_type):
        self.error_type = error_type
        super().__init__(message)


__all__ = ['RequestError']
