from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from .abc import SynchronizationPrimitive

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from redis.commands.core import AsyncScript


class Lock(SynchronizationPrimitive):
    """
    Distributed mutex.
    Grants exclusive access to resource.
    """

    LUA_RELEASE_SCRIPT = """
    local key = KEYS[1]
    local client_token = ARGV[1]
    local actual_token = redis.call('GET', key)
    if actual_token and actual_token == client_token then
        redis.call('DEL', key)
    end
    """

    script: AsyncScript

    def __init__(
        self,
        client: Redis,
        name: str,
        *,
        ttl: int,
    ) -> None:
        super().__init__(client, name)
        self.ttl = ttl * 1000
        self.token: bytes | None = None

        if not hasattr(self, "script"):
            type(self).script = self.client.register_script(self.LUA_RELEASE_SCRIPT)

    async def maybe_acquire(self) -> bool:
        token = uuid4().bytes
        result = await self.client.set(self.name, token, nx=True, px=self.ttl)
        acquired = bool(result)
        if acquired:
            self.token = token
        return acquired

    async def release(self) -> None:
        if self.token:
            await self.script([self.name], [self.token])
