"""Utility functions for all database interactions.

None of the functions defined herein are "connection safe", and may
cause issues when asynchronously called in rapid succession.

Be sure to use a pooled connection or guard database access with a
lock. These functions only act as helpers to segregate SQL interactions
and Python objects.

"""

import dataclasses

import asyncpg

from ._events import FacilityCapture, PlayerBlip, RelativePlayerBlip


async def facility_control(
        blip: FacilityCapture, conn: asyncpg.Connection) -> None:
    """Dispatch a :class:`FacilityCapture` blip to the database."""
    await conn.execute(  # type: ignore
        """--sql
        INSERT INTO blips."FacilityCapture" VALUES (
            $1, $2, $3, $4, $5, $6
        );""", *dataclasses.astuple(blip))


async def player_blip(
        blip: PlayerBlip, conn: asyncpg.Connection) -> None:
    """Dispatch a :class:`PlayerBlip` blip to the database."""
    await conn.execute(  # type: ignore
        """--sql
        INSERT INTO blips."PlayerBlip" VALUES (
            $1, $2, $3, $4, $5
        );""", *dataclasses.astuple(blip))


async def relative_player_blip(
        blip: RelativePlayerBlip, conn: asyncpg.Connection) -> None:
    """Dispatch a :class:`RelativePlayerBlip` blip to the database."""
    await conn.execute(  # type: ignore
        """--sql
        INSERT INTO blips."RelativePlayerBlip" VALUES (
            $1, $2, $3, $4, $5
        );""", *dataclasses.astuple(blip))
