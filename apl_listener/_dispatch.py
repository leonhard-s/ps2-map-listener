"""Utility functions for all database interactions.

None of the functions defined herein are "connection safe", and may
cause issues when asynchronously called in rapid succession.

Be sure to use a pooled connection or guard database access with a
lock. These functions only act as helpers to segregate SQL interactions
and Python objects.

"""

import datetime

import asyncpg



async def base_control(timestamp: datetime.datetime, base_id: int,
                       new_faction_id: int, old_faction_id: int,
                       server_id: int, continent_id: int,
                       conn: asyncpg.Connection) -> None:
    """Dispatch a ``BaseControl`` blip to the database."""
    await conn.execute(  # type: ignore
        """--sql
        INSERT INTO blips."BaseControl" VALUES (
            $1, $2, $3, $4, $5, $6
        );""",
        timestamp, base_id, new_faction_id, old_faction_id, server_id, zone_id)


async def player_blip(timestamp: datetime.datetime, player_id: int,
                      facility_id: int, server_id: int, zone_id: int,
                      conn: asyncpg.Connection) -> None:
    """Dispatch a ``PlayerBlip`` blip to the database."""
    await conn.execute(  # type: ignore
        """--sql
        INSERT INTO blips."PlayerBlip" VALUES (
            $1, $2, $3, $4, $5
        );""",
        timestamp, player_id, facility_id, server_id, zone_id)


async def relative_player_blip(timestamp: datetime.datetime, player_a_id: int,
                               player_b_id: int, server_id: int, zone_id: int,
                               conn: asyncpg.Connection) -> None:
    """Dispatch a ``RelativePlayerBlip`` blip to the database."""
    await conn.execute(  # type: ignore
        """--sql
        INSERT INTO blips."RelativePlayerBlip" VALUES (
            $1, $2, $3, $4, $5
        );""",
        timestamp, player_a_id, player_b_id, server_id, zone_id)
