"""Utility functions for all database interactions.

None of the functions defined herein are "connection safe", and may
cause issues when asynchronously called in rapid succession.

Be sure to use a pooled connection or guard database access with a
lock. These functions only act as helpers to segregate SQL interactions
and Python objects.

"""

import datetime
import logging

import asyncpg

log = logging.getLogger('listener')


async def base_control(timestamp: datetime.datetime, base_id: int,
                       new_faction_id: int, old_faction_id: int,
                       server_id: int, continent_id: int,
                       conn: asyncpg.Connection) -> None:
    """Dispatch a ``BaseControl`` blip to the database."""
    try:
        await conn.execute(  # type: ignore
            """--sql
            INSERT INTO "event"."BaseControl" (
                "timestamp", "server_id", "continent_id", "base_id",
                "old_faction_id", "new_faction_id"
            )
            VALUES (
                $1, $2, $3, $4, $5, $6
            );""",
            timestamp, server_id, continent_id, base_id,
            old_faction_id, new_faction_id)
    except asyncpg.exceptions.ForeignKeyViolationError as err:
        log.info('Ignored FK violation: %s', err)
        return False
    return True


async def player_blip(timestamp: datetime.datetime, player_id: int,
                      base_id: int, server_id: int, continent_id: int,
                      conn: asyncpg.Connection) -> None:
    """Dispatch a ``PlayerBlip`` to the database."""
    try:
        await conn.execute(  # type: ignore
            """--sql
            INSERT INTO "event"."PlayerBlip" (
                "timestamp", "server_id", "continent_id", "player_id", "base_id"
            )
            VALUES (
                $1, $2, $3, $4, $5
            );""",
            timestamp, server_id, continent_id, player_id, base_id)
    except asyncpg.exceptions.ForeignKeyViolationError as err:
        log.info('Ignored FK violation: %s', err)
        return False
    return True


async def relative_player_blip(timestamp: datetime.datetime, player_a_id: int,
                               player_b_id: int, server_id: int,
                               continent_id: int, conn: asyncpg.Connection
                               ) -> None:
    """Dispatch a ``RelativePlayerBlip`` to the database."""
    try:
        await conn.execute(  # type: ignore
            """--sql
            INSERT INTO "event"."RelativePlayerBlip" (
                "timestamp", "server_id", "continent_id",
                "player_a_id", "player_b_id"
            )
            VALUES (
                $1, $2, $3, $4, $5
            );""",
            timestamp, server_id, continent_id, player_a_id, player_b_id)
    except asyncpg.exceptions.ForeignKeyViolationError as err:
        log.info('Ignored FK violation: %s', err)
        return False
    return True


async def player_logout(timestamp: datetime.datetime, player_id: int,
                        conn: asyncpg.Connection) -> None:
    """Dispatch a ``PlayerLogout`` blip to the database."""
    await conn.execute(  # type: ignore
        """--sql
        INSERT INTO "event"."PlayerLogout" (
            "timestamp", "player_id"
        )
        VALUES (
            $1, $2
        );""",
        timestamp, player_id)
    return True
