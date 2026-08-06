import asyncio
import warnings
from collections import defaultdict
from dataclasses import dataclass

from amqtt.contexts import BaseContext, Action
from amqtt.plugins.base import (


    BaseAuthPlugin)
from amqtt.session import Session


class SlidingWindowThrottle(BaseAuthPlugin):

    def __init__(self, context: BaseContext) -> None:
        super().__init__(context)
        self.window: dict[str, int] = defaultdict(int)
        self.last_update: float = 0
        self.loop = asyncio.get_event_loop()
        self.duration = self._get_config_option("duration", None)
        self.depth = self._get_config_option("depth", None)
        if self.duration <= 0 or self.depth <= 0:
            warnings.warn("SlidingWindowThrottle is disabled. Check configuration for valid `duration` and `depth`.")

    async def topic_filtering(
            self, *, session: Session | None = None, topic: str | None = None, action: Action | None = None
    ) -> bool | None:

        last_update = self.last_update
        self.last_update = self.loop.time()

        if not self.duration or not self.depth or self.duration <= 0 or self.depth <= 0:
            return True

        if not session or not session.client_id:
            return True

        if self.loop.time() - last_update >= self.duration:
            self.window.clear()

        if action == Action.PUBLISH:
            if session.client_id in self.window and self.window[session.client_id] >= self.depth:
                return False

            self.window[session.client_id] += 1
            return True

        return True

    @dataclass
    class Config:
        """Control the length of the window and how many messages can be sent."""

        duration: int = 0
        """Length of the window, in seconds"""
        depth: int = 0
        """Number of messages allowed in the window."""


class TokenBucketThrottle(BaseAuthPlugin):
    """Control the number of messages sent by a client, using a token bucket algorithm.

    Limits a client from flooding the broker with messages while still allowing a client
    to send a burst of messages; for example, when a client reconnects.
    """

    def __init__(self, context: BaseContext) -> None:
        super().__init__(context)
        self.buckets = defaultdict(int)
        self.max = self._get_config_option("max", None)
        self.rate = self._get_config_option("rate", None)
        self.increments = self._get_config_option("increments", None)
        self.filler_task = None

        if self.max <= 0 or self.rate <= 0 or self.increments <= 0:
            warnings.warn("TokenBucketThrottle is disabled. Check configuration for valid values.")

    async def bucket_filler(self):
        while True:
            await asyncio.sleep(self.rate)
            for client_id in self.buckets.keys():
                self.buckets[client_id] = min(self.max, self.buckets[client_id] + self.increments)

    async def on_broker_pre_start(self) -> None:

        if not self.filler_task:
            self.filler_task = asyncio.create_task(self.bucket_filler())


    async def topic_filtering(
            self, *, session: Session | None = None, topic: str | None = None, action: Action | None = None
    ) -> bool | None:

        if not self.filler_task:
            return True

        if not session or not session.client_id:
            return True

        if self.max <= 0 or self.rate <= 0 or self.increments <= 0:
            return True

        # new client, create a new bucket
        if session.client_id not in self.buckets:
            self.buckets[session.client_id] = 0

        # client is allowed to publish only if there are tokens in the bucket
        if self.buckets[session.client_id] < 1:
            return False

        # allow the client to publish, decrement the bucket
        self.buckets[session.client_id] -= 1
        return True

    @dataclass
    class Config:
        """Size of the bucket and the rate at which tokens are added to the bucket."""
        max: int = 0
        """Size of the bucket"""
        increments: int = 0
        """Number of tokens added to the bucket each time"""
        rate: int = 0
        """Rate (per seconds) at which tokens are added to the bucket"""