from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING
from uuid import uuid4

from .abc import SynchronizationPrimitive

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from redis.commands.core import AsyncScript


class Semaphore(SynchronizationPrimitive):
    """
    Distributed semaphore.
    Allows up to 'capacity' operations at the same time.
    timeout is required to avoid deadlocks
    """

    LUA_SCRIPT = """
    local key = KEYS[1]
    local capacity = tonumber(ARGV[1])
    local token = ARGV[2]
    local ttl = tonumber(ARGV[3])
    local current_time = redis.call('TIME')
    local current_time_micro = tonumber(current_time[1]) * 1000000 + tonumber(current_time[2])
    local token_expiration = current_time_micro + (ttl  * 1000000)

    redis.call('ZREMRANGEBYSCORE', key, 0, current_time_micro)
    if redis.call('ZSCORE', key, token) then
        return true -- token already acquired so return true
    end

    local current_count = redis.call('ZCARD', key)

    if current_count < capacity then
        redis.call('ZADD', key, token_expiration, token)

        if current_count == 0 then
            redis.call('PEXPIRE', key, ttl * 1000)
        end

        return true
    end
    return false
    """

    script: AsyncScript

    def __init__(
        self,
        client: Redis,
        name: str,
        *,
        capacity: int,
        ttl: int,
    ):
        super().__init__(client, name)
        if capacity <= 1:
            raise ValueError("capacity must be greater than 1")
        if ttl <= 0:
            raise ValueError("ttl must be greater than 1")
        self.capacity = capacity
        self.ttl = ttl
        self.tokens: deque[bytes] = deque()

        if not hasattr(self, "script"):
            type(self).script = self.client.register_script(self.LUA_SCRIPT)

    async def maybe_acquire(self) -> bool:
        token = uuid4().bytes
        result = await self.script([self.name], [self.capacity, token, self.ttl])
        acquired = bool(result)
        if acquired:
            self.tokens.append(token)
        return acquired

    async def release(self) -> None:
        if len(self.tokens) > 0:
            token = self.tokens.popleft()
            await self.client.zrem(self.name, token)
