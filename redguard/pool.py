from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Callable, Generic, TypeVar

if TYPE_CHECKING:
    from .abc import SynchronizationPrimitive

T = TypeVar("T")

logger = getLogger(__name__)


class SharedResourcePool(Generic[T]):
    def __init__(
        self,
        primitive: SynchronizationPrimitive,
        factory: Callable[[], T],
        *,
        timeout: float | None = None,
    ) -> None:
        self.primitive = primitive
        self.factory = factory
        self.timeout = timeout

    async def __aenter__(self) -> T:
        logger.debug("Acquiring rate limiter %s", self.primitive)
        await self.primitive.acquire(blocking=True, timeout=self.timeout)
        return self.factory()

    async def __aexit__(self, *exc) -> None:
        logger.debug("Releasing rate limiter %s", self.primitive)
        await self.primitive.release()
