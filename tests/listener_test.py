import asyncio
import unittest
from typing import cast
from unittest import mock

import asyncpg
from mock.database import MockConnection, MockPool  # type: ignore

from apl_listener import EventListener  # pylint: disable=import-error


class Test(unittest.IsolatedAsyncioTestCase):

    async def test_test(self) -> None:
        # Mock objects
        pool = MockPool()

        listener = EventListener('s:example', cast(asyncpg.pool.Pool, pool))

        asyncio.get_running_loop().create_task(listener.connect())
        await asyncio.sleep(5)

        pool.raise_fk_violations = True
        with self.assertRaises(asyncpg.exceptions.ForeignKeyViolationError):
            await asyncio.sleep(1)
        await listener.close()
