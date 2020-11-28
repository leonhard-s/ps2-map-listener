"""Utility functions for all database interactions.

None of the functions defined herein are "connection safe", and may
cause issues when asynchronously called in rapid succession.

Be sure to use a pooled connection or guard database access with a
lock. These functions only act as helpers to segregate SQL interactions
and Python objects.

"""

from typing import Any

import asyncpg


async def facility_control(*args: Any, conn: asyncpg.Connection) -> None:
    """Dispatch a ``FacilityCapture`` blip to the database."""
    await conn.execute(  # type: ignore
        """--sql
        INSERT INTO blips."FacilityCapture" VALUES (
            $1, $2, $3, $4, $5, $6
        );""", *args)


async def player_blip(*args: Any, conn: asyncpg.Connection) -> None:
    """Dispatch a ``PlayerBlip`` blip to the database."""
    await conn.execute(  # type: ignore
        """--sql
        INSERT INTO blips."PlayerBlip" VALUES (
            $1, $2, $3, $4, $5
        );""", *args)


async def relative_player_blip(
        *args: Any, conn: asyncpg.Connection) -> None:
    """Dispatch a ``RelativePlayerBlip`` blip to the database."""
    await conn.execute(  # type: ignore
        """--sql
        INSERT INTO blips."RelativePlayerBlip" VALUES (
            $1, $2, $3, $4, $5
        );""", *args)
