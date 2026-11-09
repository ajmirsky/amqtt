
class RateLimiter:
    """Base class for rate limiters"""

    def __init__(self, message_limit: int, time_window: int):
        self.message_limit = message_limit
        self.time_window = time_window

    def allow(self, client_id: str, *args, **kwargs ) -> bool:
        """Returns false if the client is not allowed to send a message, otherwise true"""
        raise NotImplementedError("please create a subclass")





