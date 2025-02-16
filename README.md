![Tests](https://github.com/asynq-io/redguard/workflows/Tests/badge.svg)
![Build](https://github.com/asynq-io/redguard/workflows/Publish/badge.svg)
![License](https://img.shields.io/github/license/asynq-io/redguard)
![Python](https://img.shields.io/pypi/pyversions/redguard)
![Format](https://img.shields.io/pypi/format/redguard)
![PyPi](https://img.shields.io/pypi/v/redguard)
![Mypy](https://img.shields.io/badge/mypy-checked-blue)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

# redguard

Distributed synchronization primitives buit on top of Redis

## Installation

```shell
pip install redguard
```

## Available primitives

- `Lock` - distributed mutex
- `Semaphore` - distributed semaphore
- `RateLimiter` - distributed rate limiter

## Helpers

- `RedGuard` - factory for creating primitives
- `SharedResourcePool` - factory for creating shared resources

## Usage

The api is similar to built-in `asyncio` module primitives.

```python
from redguard import RedGuard
from redguard.lock import Lock

guard = RedGuard.from_url("redis://localhost:6379")

async def lock_example():
    lock = guard.new(Lock, "my-lock")

    async with lock:
        print("Locked")

async def semaphore_example():
    semaphore = guard.new(Semaphore, "my-semaphore", capacity=2)

    async with semaphore:
        print("Acquired")

async def rate_limiter_example():
    rate_limiter = guard.new(RateLimiter, "my-rate-limiter", limit=2, window=1)

    async with rate_limiter:
        print("Rate limited")

```

### Lower level api

Each primitve can be used as async context manager, but also provides `acquire` and `release` methods.

```python

semaphore = guard.new(Semaphore, "my-semaphore", capacity=2)

acquired = await semaphore.acquire(blocking=True, timeout=None) # returns True if acquired (useful for blocking=False)

if acquired:
    await semaphore.release()

```
