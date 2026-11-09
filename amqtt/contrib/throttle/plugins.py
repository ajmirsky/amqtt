from dataclasses import dataclass

from amqtt.contexts import Action
from amqtt.plugins.base import BaseTopicPlugin
from amqtt.session import Session


class ThrottlePlugin(BaseTopicPlugin):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        ...

    def topic_filtering(
        self, *, session: Session | None = None, topic: str | None = None, action: Action | None = None
    ) -> bool | None:

        # if action is publish, check if the client is allowed to publish
        ...


    @dataclass
    class Config:
        """Configuration for the Throttle plugin."""
        rate_limiter: str = "window"
        """algorithm to rate limit publisher: 'window' or 'bucket'"""
        other_config_option_1: int = 10
        other_config_option_2: str = "value"
        other_config_option_3: bool = True
