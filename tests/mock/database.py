"""Mock database."""

from types import TracebackType
from typing import Any, Literal, Optional, Type, cast
from unittest import mock

import asyncpg


class MockConnection:

    side_effects = None

    def __init__(self, side_effects: Any) -> None:
        self.side_effects = side_effects

    execute = mock.AsyncMock(side_effects=side_effects)

    fetchrow = mock.AsyncMock(return_value=(0,), side_effects=side_effects)


class MockPoolContext:

    def __init__(self, pool: 'MockPool') -> None:
        self.pool = pool

    async def __aenter__(self) -> asyncpg.Connection:
        if self.pool.raise_fk_violations:
            side_effects = [asyncpg.exceptions.ForeignKeyViolationError]
        else:
            side_effects = []
        return cast(asyncpg.Connection, MockConnection(side_effects))

    async def __aexit__(self, exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> Literal[False]:
        return False


class MockPool:

    def __init__(self, fk_violations: bool = True) -> None:
        self.raise_fk_violations = fk_violations

    def acquire(self) -> MockPoolContext:
        return MockPoolContext(self)
