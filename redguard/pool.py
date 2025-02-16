from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Generic, TypeVar

if TYPE_CHECKING:
    from .abc import SynchronizationPrimitive

T = TypeVar("T")


class SharedResourcePool(Generic[T]):
    def __init__(
        self,
        primitive: SynchronizationPrimitive,
        *,
        factory: Callable[[], T],
        timeout: float | None = None,
    ) -> None:
        self.primitive = primitive
        self.factory = factory
        self.timeout = timeout

    async def acquire(self) -> T:
        await self.primitive.acquire(blocking=True, timeout=self.timeout)
        return self.factory()

    async def release(self) -> None:
        await self.primitive.release()

    async def __aenter__(self) -> T:
        return await self.acquire()

    async def __aexit__(self, *exc) -> None:
        await self.release()
