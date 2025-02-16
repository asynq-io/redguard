import asyncio

from redguard import Lock, RateLimiter, RedGuard, Semaphore


async def test_lock(guard: RedGuard):
    lock = guard.new(Lock, "test-lock", ttl=10)
    acquired = await lock.acquire()
    assert acquired is True
    acquired = await lock.acquire()
    assert acquired is False
    await lock.release()
    acquired = await lock.acquire()
    assert acquired is True
    await lock.release()


async def test_semaphore(guard: RedGuard):
    capacity = 3
    semaphore = guard.new(Semaphore, "test-sem", capacity=capacity, ttl=10)

    for i in range(capacity + 1):
        acquired = await semaphore.acquire()
        assert acquired is (i < capacity)

    for _ in range(capacity + 1):
        await semaphore.release()


async def test_rate_limiter(guard: RedGuard):
    await asyncio.sleep(1)
    limiter = guard.new(RateLimiter, "test-limiter", limit=3, window=1)
    for _ in range(3):
        assert await limiter.acquire() is True
    assert await limiter.acquire() is False

    await limiter.release()
