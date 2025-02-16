from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redis.asyncio import Redis


class SynchronizationPrimitive(AbstractAsyncContextManager, ABC):
    def __init__(self, client: Redis, name: str) -> None:
        self.client = client
        self.name = name

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    async def _blocking_acquire(self) -> None:
        while True:
            acquired = await self.maybe_acquire()
            if acquired:
                return
            await asyncio.sleep(0.1)

    async def acquire(
        self, *, blocking: bool = False, timeout: float | None = None
    ) -> bool:
        if blocking:
            await asyncio.wait_for(self._blocking_acquire(), timeout=timeout)
            return True
        else:
            return await self.maybe_acquire()

    @abstractmethod
    async def release(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def maybe_acquire(self) -> bool:
        raise NotImplementedError

    async def __aenter__(self) -> bool:
        return await self.acquire(blocking=True)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.release()
