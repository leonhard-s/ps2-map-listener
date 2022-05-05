"""Utility functions for all database interactions.

None of the functions defined herein are "connection safe", and may
cause issues when asynchronously called in rapid succession.

Be sure to use a pooled connection or guard database access with a
lock. These functions only act as helpers to segregate SQL interactions
and Python objects.
"""

import datetime
import logging

from ._db import Connection, ForeignKeyViolation, Row
from ._sql import (SQL_BASE_CONTROL, SQL_PLAYER, SQL_RELATIVE_PLAYER,
                   SQL_PLAYER_LOGOUT)


log = logging.getLogger('listener')


async def base_control(timestamp: datetime.datetime, base_id: int,
                       new_faction_id: int, old_faction_id: int,
                       server_id: int, continent_id: int,
                       conn: Connection[Row]) -> bool:
    """Dispatch a ``BaseControl`` Blip to the database."""
    try:
        await conn.execute(
            SQL_BASE_CONTROL, (timestamp, server_id, continent_id, base_id,
                               old_faction_id, new_faction_id))
    except ForeignKeyViolation as err:
        log.debug('Ignored FK violation: %s', err)
        return False
    return True


async def player_blip(timestamp: datetime.datetime, player_id: int,
                      base_id: int, server_id: int, continent_id: int,
                      conn: Connection[Row]) -> bool:
    """Dispatch a ``PlayerBlip`` to the database."""
    try:
        await conn.execute(
            SQL_PLAYER, (timestamp, server_id, continent_id, player_id,
                         base_id))
    except ForeignKeyViolation as err:
        log.debug('Ignored FK violation: %s', err)
        return False
    return True


async def relative_player_blip(timestamp: datetime.datetime, player_a_id: int,
                               player_b_id: int, server_id: int,
                               continent_id: int, conn: Connection[Row]
                               ) -> bool:
    """Dispatch a ``RelativePlayerBlip`` to the database."""
    try:
        await conn.execute(
            SQL_RELATIVE_PLAYER, (timestamp, server_id, continent_id,
                                  player_a_id, player_b_id))
    except ForeignKeyViolation as err:
        log.debug('Ignored FK violation: %s', err)
        return False
    return True


async def player_logout(timestamp: datetime.datetime, player_id: int,
                        conn: Connection[Row]) -> bool:
    """Dispatch a ``PlayerLogout`` Blip to the database."""
    await conn.execute(SQL_PLAYER_LOGOUT, (timestamp, player_id))
    return True
