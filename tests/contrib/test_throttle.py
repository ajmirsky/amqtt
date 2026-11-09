import asyncio
import pytest

from amqtt.contrib.throttle import RateLimiter


class MyTestRateLimiter(RateLimiter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rate = 10

    def allow(self, client_id: str, *args, **kwargs) -> bool:
        return True


@pytest.mark.asyncio
async def test_window_limiter_single_client_allow():
    """0 seconds - no tokens in bucket
4 seconds - 10 tokens in bucket
8 seconds - 20 tokens in bucket
client1, sent 20 messages, all would be approved
12 seconds - 20 tokens in bucket
16 seconds - 20 tokens in bucket
20 seconds - 20 tokens in bucket
"""



    rate_limiter = MyTestRateLimiter()

    for i in range(10):
        assert rate_limiter.allow("client1")
        await asyncio.sleep(0.1)

@pytest.mark.asyncio
async def test_window_limiter_multiple_client_allow():
    """
    0 seconds - no tokens in bucket
4 seconds - 10 tokens in bucket
8 seconds - 20 tokens in bucket
client1, sent 20 messages, all would be approved
client2, sent 20 messages, all would be approved
12 seconds - 20 tokens in bucket
16 seconds - 20 tokens in bucket
20 seconds - 20 tokens in bucket
    """

    rate_limiter = WindowRateLimiter(...)

    for i in range(10):
        assert rate_limiter.allow("client1")
        await asyncio.sleep(0.1)
        assert rate_limiter.allow("client2")
        await asyncio.sleep(0.1)

# additional test scenarios...
"""
0 seconds - 0 messages
4 seconds - 0 messages
8 seconds - 10 messages get sent, then 10 messages get denied
12 seconds - 0 messages
16 seconds - 0 messages
20 seconds - 0 messages
"""
