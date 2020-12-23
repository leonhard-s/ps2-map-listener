"""Event listening client definition."""

import datetime
import logging
from typing import Any, Callable, Coroutine, Dict, TypeVar, cast

import asyncpg
import auraxium

from ._dispatch import (base_control, player_blip, player_logout,
                        relative_player_blip)

# Type aliases
_ActionT = TypeVar('_ActionT', bound=Callable[..., Coroutine[Any, Any, None]])

# The list of world IDs to be tracked. See the base_control handler for
# details.
_WORLDS = [
    1,  # Connery
    10,  # Miller
    13,  # Cobalt
    17,   # Emerald
    25,  # Briggs
    40  # SolTech
]

log = logging.getLogger('listener')


async def _base_from_facility(facility_id: int,
                              conn: asyncpg.Connection) -> int:
    row: Any = await conn.fetchrow(  # type: ignore
        """--sql
        SELECT
            ("id")
        FROM
            "autopl"."Base"
        WHERE
            "facility_id" = $1
        ;""", facility_id)
    if row is None:
        raise ValueError(f'Invalid facility ID {facility_id}')
    return int(tuple(row)[0])


def _log_errors(func: _ActionT) -> _ActionT:
    """Error handler for the decorated function.

    Any exceptions raised within the given function will be suppressed
    and logged.

    """

    async def wrapper(*args: Any, **kwargs: Any) -> None:
        try:
            return await func(*args, **kwargs)
        except ValueError as err:
            log.exception('Argument conversion error in \'%s\':\n'
                          '  Args: %s\n'
                          '  Kwargs: %s',
                          func.__name__, args, kwargs)
        except BaseException as err:
            # Fallback clause for generic exceptions
            log.exception('Ignoring generic exception in \'%s\':', type(err))

    return cast(_ActionT, wrapper)  # type: ignore


class EventListener:
    """The APL event listener instance.

    This class wraps an auraxium client to provide additional logging
    information and define any event types required.

    """

    def __init__(self, service_id: str, pool: asyncpg.pool.Pool) -> None:
        self._arx_client = auraxium.EventClient(service_id=service_id)
        self._db_pool = pool
        # This dictionary is used to keep track of the number of events
        # received
        self._dispatch_cache: Dict[str, int] = {}
        self._dispatch_last_update = datetime.datetime.now()

    async def close(self) -> None:
        """Gracefully close the event listener."""
        await self._arx_client.close()
        self._arx_client.triggers.clear()

    async def connect(self) -> None:
        """Start the listener and keep it running."""
        self._arx_client.triggers.clear()
        self._create_triggers()
        await self._arx_client.connect()

    def _create_triggers(self) -> None:
        """Create and register all event triggers for the listener."""
        # Absolute player blips
        self._arx_client.add_trigger(auraxium.Trigger(
            auraxium.EventType.PLAYER_FACILITY_CAPTURE,
            auraxium.EventType.PLAYER_FACILITY_DEFEND,
            action=self.player_blip,
            name='AbsolutePlayerBlip'))
        # Relative player blip
        self._arx_client.add_trigger(auraxium.Trigger(
            auraxium.EventType.DEATH,
            auraxium.EventType.filter_experience(4),  # Heal Player
            auraxium.EventType.filter_experience(36),  # Spotting bonus
            auraxium.EventType.filter_experience(54),  # Squad spotting bonus
            action=self.relative_player_blip,
            name='RelativePlayerBlip'))
        # FacilityCapture
        self._arx_client.add_trigger(auraxium.Trigger(
            auraxium.EventType.FACILITY_CONTROL,
            action=self.base_control,
            name='FacilityControl',
            # NOTE: Implicitly subscribing to all worlds is not permitted, so
            # we must subscribe to all of them individually.
            worlds=_WORLDS))
        # PlayerLogout
        self._arx_client.add_trigger(auraxium.Trigger(
            auraxium.EventType.PLAYER_LOGOUT,
            action=self.player_logout,
            name='PlayerLogout'))

    def _push_dispatch(self, event_name: str) -> None:
        cache = self._dispatch_cache
        # Update dispatch cache
        try:
            cache[event_name] += 1
        except KeyError:
            cache[event_name] = 1
        # Push the current status to the user every 5 seconds
        now = datetime.datetime.now()
        if now >= self._dispatch_last_update + datetime.timedelta(seconds=5.0):
            if log.getEffectiveLevel() <= logging.INFO:
                data = sorted((f'{k}: {v}' for k, v in cache.items()))
                total = sum(cache.values())
                log.info('Sent %d events over the last 5 seconds:\n\t%s',
                         total, '\n\t'.join(data))
            cache.clear()
            self._dispatch_last_update = now

    @_log_errors
    async def base_control(self, event: auraxium.Event) -> None:
        """Validate and dispatch facility captures.

        :param event: The event received.

        """
        facility_id = int(event.payload['facility_id'])
        conn: asyncpg.Connection
        async with self._db_pool.acquire() as conn:  # type: ignore
            try:
                base_id = await _base_from_facility(facility_id, conn)
            except ValueError:
                log.debug('Ignoring invalid facility ID %d', facility_id)
                return
            blip = (
                event.timestamp,
                base_id,
                int(event.payload['new_faction_id']),
                int(event.payload['old_faction_id']),
                int(event.payload['world_id']),
                int(event.payload['zone_id']))
            if await base_control(*blip, conn=conn):
                self._push_dispatch('base_control')

    @_log_errors
    async def player_blip(self, event: auraxium.Event) -> None:
        """Validate and dispatch a ``PlayerBlip``.

        :param event: The event received.

        """
        player_id = int(event.payload['character_id'])
        blip = (
            event.timestamp,
            player_id,
            int(event.payload['facility_id']),
            int(event.payload['world_id']),
            int(event.payload['zone_id']))
        if player_id == 0:
            log.warning('Unexpected character ID 0 in base_control action')
            return
        conn: asyncpg.Connection
        async with self._db_pool.acquire() as conn:  # type: ignore
            if await player_blip(*blip, conn=conn):
                self._push_dispatch('player_blip')

    @_log_errors
    async def player_logout(self, event: auraxium.Event) -> None:
        """Validate and dispatch a ``PlayerLogout`` blip.

        :param event: The event received.

        """
        player_id = int(event.payload['character_id'])
        blip = (
            event.timestamp,
            player_id)
        if player_id == 0:
            log.warning('Unexpected character ID 0 in player_logout action')
            return
        conn: asyncpg.Connection
        async with self._db_pool.acquire() as conn:  # type: ignore
            if await player_logout(*blip, conn=conn):
                self._push_dispatch('player_logout')

    @_log_errors
    async def relative_player_blip(self, event: auraxium.Event) -> None:
        """Validate and dispatch a ``RelativePlayerBlip``.

        :param event: The event received.

        """
        if event.type == auraxium.EventType.DEATH:
            player_a_id = int(event.payload['attacker_character_id'])
            player_b_id = int(event.payload['character_id'])
        else:
            player_a_id = int(event.payload['character_id'])
            player_b_id = int(event.payload['other_id'])
        blip = (
            event.timestamp,
            player_a_id,
            player_b_id,
            int(event.payload['world_id']),
            int(event.payload['zone_id']))
        if (player_a_id == 0 or player_b_id == 0 or player_a_id == player_b_id):
            # For death events, it is common for the attacker (A) to be
            # identical to the victim (B), or for the attacker (A) to be 0.
            #
            # These are therefore silently ignored without a log message as
            # they point to regular, common ingame events like killing oneself
            # or dying to spawn room pain fields.
            if (not event.payload['event_name'] == 'Death'
                    or player_b_id == 0):
                log.warning(
                    'Unexpected character ID 0 in relative_player_blip action')
            return
        conn: asyncpg.Connection
        async with self._db_pool.acquire() as conn:  # type: ignore
            if await relative_player_blip(*blip, conn=conn):
                self._push_dispatch('relative_player_blip')
