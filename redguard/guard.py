from __future__ import annotations

from typing import Any, Callable, TypeVar

from redis.asyncio import Redis
from typing_extensions import Self

from .abc import SynchronizationPrimitive
from .limiter import RateLimiter
from .lock import Lock
from .pool import SharedResourcePool, T
from .semaphore import Semaphore

P = TypeVar("P", bound=SynchronizationPrimitive)


class RedGuard:
    """
    Helper class implementing factory pattern for synchronization primitives
    """

    def __init__(self, client: Redis, namespace: str | None = None) -> None:
        self.client = client
        self.namespace = namespace

    @classmethod
    def from_url(cls, url: str, namespace: str | None = None, **client_options) -> Self:
        return cls(Redis.from_url(url, **client_options), namespace=namespace)

    def format(self, name: str) -> str:
        if self.namespace is None:
            return name
        return f"{self.namespace}:{name}"

    def new(self, cls: type[P], name: str, **kwargs: Any) -> P:
        return cls(self.client, self.format(name), **kwargs)

    def lock(self, name: str, *, ttl: int) -> Lock:
        return self.new(Lock, name, ttl=ttl)

    def semaphore(
        self,
        name: str,
        *,
        capacity: int,
        ttl: int,
    ) -> Semaphore:
        return self.new(Semaphore, name, capacity=capacity, ttl=ttl)

    def limiter(self, name: str, *, limit: int, window: int = 1) -> RateLimiter:
        return self.new(RateLimiter, name, limit=limit, window=window)

    def pool(
        self,
        cls: type[P],
        name: str,
        factory: Callable[[], T],
        timeout: float | None = None,
        **kwargs: Any,
    ) -> SharedResourcePool[T]:
        return SharedResourcePool(
            self.new(cls, name, **kwargs), factory=factory, timeout=timeout
        )
