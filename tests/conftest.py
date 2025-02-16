import asyncio

import pytest
from redis.asyncio import Redis
from testcontainers.redis import RedisContainer

from redguard import RedGuard


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.stop()


@pytest.fixture(scope="session")
def redis():
    with RedisContainer() as container:
        url = f"redis://{container.get_container_host_ip()}:{container.get_exposed_port(container.port)}/0"
        client = Redis.from_url(url)
        yield client


@pytest.fixture(scope="session")
def guard(redis):
    return RedGuard(redis, namespace="test")
