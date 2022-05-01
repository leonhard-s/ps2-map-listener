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

from ._typing import Connection

log = logging.getLogger('listener')

# Load SQL commands from file
with open('sql/insertBlip_BaseControl.sql', encoding='utf-8') as sql_file:
    _SQL_BASE_CONTROL = sql_file.read()
with open('sql/insertBlip_Player.sql', encoding='utf-8') as sql_file:
    _SQL_PLAYER = sql_file.read()
with open('sql/insertBlip_RelativePlayer.sql', encoding='utf-8') as sql_file:
    _SQL_RELATIVE_PLAYER = sql_file.read()
with open('sql/insertBlip_PlayerLogout.sql', encoding='utf-8') as sql_file:
    _SQL_PLAYER_LOGOUT = sql_file.read()


async def base_control(timestamp: datetime.datetime, base_id: int,
                       new_faction_id: int, old_faction_id: int,
                       server_id: int, continent_id: int,
                       conn: Connection) -> bool:
    """Dispatch a ``BaseControl`` Blip to the database."""
    try:
        await conn.execute(_SQL_BASE_CONTROL, timestamp, server_id,
                           continent_id, base_id, old_faction_id,
                           new_faction_id)
    except asyncpg.exceptions.ForeignKeyViolationError as err:
        log.debug('Ignored FK violation: %s', err)
        return False
    return True


async def player_blip(timestamp: datetime.datetime, player_id: int,
                      base_id: int, server_id: int, continent_id: int,
                      conn: Connection) -> bool:
    """Dispatch a ``PlayerBlip`` to the database."""
    try:
        await conn.execute(_SQL_PLAYER, timestamp, server_id, continent_id,
                           player_id, base_id)
    except asyncpg.exceptions.ForeignKeyViolationError as err:
        log.debug('Ignored FK violation: %s', err)
        return False
    return True


async def relative_player_blip(timestamp: datetime.datetime, player_a_id: int,
                               player_b_id: int, server_id: int,
                               continent_id: int, conn: Connection
                               ) -> bool:
    """Dispatch a ``RelativePlayerBlip`` to the database."""
    try:
        await conn.execute(_SQL_RELATIVE_PLAYER, timestamp, server_id,
                           continent_id, player_a_id, player_b_id)
    except asyncpg.exceptions.ForeignKeyViolationError as err:
        log.debug('Ignored FK violation: %s', err)
        return False
    return True


async def player_logout(timestamp: datetime.datetime, player_id: int,
                        conn: Connection) -> bool:
    """Dispatch a ``PlayerLogout`` Blip to the database."""
    await conn.execute(_SQL_PLAYER_LOGOUT, timestamp, player_id)
    return True
