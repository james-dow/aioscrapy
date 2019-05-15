from typing import Optional, Tuple, Iterable

import pytest

from aioscrapy.client import FakeClient, CrawlerClient
from aioscrapy.worker import Dispatcher, SimpleWorker, CrawlerWorker


class ReduceStringClient(CrawlerClient[str, str]):
    async def fetch(self, key: str) -> Optional[Tuple[Iterable[str], str]]:
        if key:
            return [key[:-1]], key
        return None


@pytest.mark.asyncio
async def test_reduce_string_client():
    client = ReduceStringClient()
    assert await client.fetch('123') == (['12'], '123')
    assert await client.fetch('1') == ([''], '1')
    assert await client.fetch('') is None


def test_dispatcher():
    dispatcher = Dispatcher([])
    assert dispatcher.empty() is True
    key1, key2, key3, error_key = 'key1', 'key2', 'key3', 'error_key'

    dispatcher.add(key1)
    assert dispatcher.empty() is False

    key = dispatcher.get()
    assert key == key1
    dispatcher.ack(key)
    assert dispatcher.empty() is True

    dispatcher.add(key2)
    dispatcher.add(key3)

    keys = {dispatcher.get(), dispatcher.get()}
    assert keys == {key2, key3}
    assert dispatcher.empty() is False
    dispatcher.ack(error_key)
    dispatcher.ack(key2)
    assert dispatcher.empty() is False
    dispatcher.ack(key3)
    assert dispatcher.empty() is True


@pytest.mark.asyncio
async def test_simple_worker():
    keys = ['key1', 'key2', 'key3']
    dispatcher = Dispatcher(keys)
    client = FakeClient()
    worker = SimpleWorker(dispatcher, client)
    result = await worker.run()
    assert result == {key: key for key in keys}


@pytest.mark.asyncio
async def test_crawler_worker():
    keys = ['abc', 'asd']
    dispatcher = Dispatcher(keys)
    client = ReduceStringClient()
    worker = CrawlerWorker(dispatcher, client)
    result = await worker.run()
    assert result == {
        'a': 'a',
        'ab': 'ab',
        'abc': 'abc',
        'as': 'as',
        'asd': 'asd',
    }
