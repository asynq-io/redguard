from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from .abc import SynchronizationPrimitive

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from redis.commands.core import AsyncScript


class RateLimiter(SynchronizationPrimitive):
    """
    Rate limiter implementing sliding window algorithm.
    Allows up to limit operations over window (in seconds) period.
    """

    LUA_SCRIPT = """
    local key = KEYS[1]
    local token = ARGV[1]
    local limit = tonumber(ARGV[2])
    local window_size = tonumber(ARGV[3])
    local current_time = redis.call('TIME')
    local current_time_micro = tonumber(current_time[1]) * 1000000 + tonumber(current_time[2])
    local trim_time_micro = current_time_micro - (window_size  * 1000000)

    redis.call('ZREMRANGEBYSCORE', key, 0, trim_time_micro)
    local current_count = redis.call('ZCARD', key)

    if current_count < limit then
        redis.call('ZADD', key, current_time_micro, token)

        if current_count == 0 then
            redis.call('PEXPIRE', key, window_size * 1000)
        end

        return true
    end
    return false
    """

    script: AsyncScript

    def __init__(
        self, client: Redis, name: str, *, limit: int, window: int = 1
    ) -> None:
        super().__init__(client, name)
        if window <= 0:
            raise ValueError("Window must be greater than 0")
        if limit < 1:
            raise ValueError("Limit must be greater than 0")
        self.window = window
        self.limit = limit

        if not hasattr(self, "script"):
            type(self).script = self.client.register_script(self.LUA_SCRIPT)

    async def maybe_acquire(self) -> bool:
        token = uuid4().bytes
        result = await self.script([self.name], [token, self.limit, self.window])
        return bool(result)

    async def release(self) -> None:
        pass
