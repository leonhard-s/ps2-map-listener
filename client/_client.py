"""Event listening client definition."""

import datetime
import logging
from typing import Any, Callable, Coroutine, Dict, TypeVar, Union, cast

import asyncpg
import auraxium
from auraxium import event

from ._dispatch import (base_control, player_blip, player_logout,
                        relative_player_blip)

# Type aliases
_ActionT = TypeVar('_ActionT', bound=Callable[..., Coroutine[Any, Any, None]])

log = logging.getLogger('listener')


async def _base_from_facility(facility_id: int,
                              conn: asyncpg.Connection) -> int:
    """Get the base ID associated with a given facility.

    Args:
        facility_id (int): The facility ID received via the event
            client.
        conn (asyncpg.Connection): A preexisting database connection to
            use for the conversion.
    """
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

    Args:
        func (Coroutine): The function to wrap.

    Returns:
        Coroutine: Wrapper version of `func`.
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

    This class wraps an Auraxium event client, processes the responses
    received and dispatches the corresponding Blips to the database.

    Run :meth:`connect()` to run the event client. It is recommended to
    do this via :meth:`asyncio.AbstractEventLoop.create_task()` as this
    method will never return without error if awaited.

    The event client can be shut down using the :meth:`close()`.

    Args:
        service_id (str): The Census API service ID to use for the
            WebSocket connection.
        pool (asyncpg.pool.Pool): A preexisting connection pool to use
            for database interaction.
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
        """Start the listener and keep it running.

        Please note that this method does not return until the event
        client encounters an exception or is closed via
        :meth:`close()`.
        """
        self._arx_client.triggers.clear()
        self._create_triggers()
        await self._arx_client.connect()

    def _create_triggers(self) -> None:
        """Create and register all event triggers for the listener."""
        # Absolute player blips
        self._arx_client.add_trigger(auraxium.Trigger(
            event.PlayerFacilityCapture,
            event.PlayerFacilityDefend,
            action=self.player_blip,  # type: ignore
            name='AbsolutePlayerBlip'))
        # Relative player blip
        self._arx_client.add_trigger(auraxium.Trigger(
            event.Death,
            event.GainExperience.filter_experience(4),  # Heal Player
            event.GainExperience.filter_experience(36),  # Spotting bonus
            event.GainExperience.filter_experience(54),  # Squad spotting bonus
            action=self.relative_player_blip,  # type: ignore
            name='RelativePlayerBlip'))
        # FacilityCapture
        self._arx_client.add_trigger(auraxium.Trigger(
            auraxium.event.FacilityControl,
            action=self.base_control,  # type: ignore
            name='FacilityControl'))
        # PlayerLogout
        self._arx_client.add_trigger(auraxium.Trigger(
            auraxium.event.PlayerLogout,
            action=self.player_logout,  # type: ignore
            name='PlayerLogout'))

    def _push_dispatch(self, event_name: str) -> None:
        """Utility method to collect debug information.

        This groups events by name and logs the number of times each
        has been encountered in the last five seconds.

        Args:
            event_name (str): The name of the event received.
        """
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
    async def base_control(self, evt: event.FacilityControl) -> None:
        """Validate and dispatch facility captures.

        Args:
            event (event.FacilityControl): The event received.
        """
        conn: asyncpg.Connection
        async with self._db_pool.acquire() as conn:  # type: ignore
            try:
                base_id = await _base_from_facility(evt.facility_id, conn)
            except ValueError:
                log.debug('Ignoring invalid facility ID %d', evt.facility_id)
                return
            blip = (
                evt.timestamp,
                base_id,
                evt.new_faction_id,
                evt.old_faction_id,
                evt.world_id,
                evt.zone_id)
            if await base_control(*blip, conn=conn):
                self._push_dispatch('base_control')

    @_log_errors
    async def player_blip(
            self,
            evt: Union[event.PlayerFacilityCapture, event.PlayerFacilityDefend]
    ) -> None:
        """Validate and dispatch a ``PlayerBlip``.

        Args:
            event (event.Event): The event received.
        """
        blip = (
            evt.timestamp,
            evt.character_id,
            evt.facility_id,
            evt.world_id,
            evt.zone_id)
        if evt.character_id == 0:
            log.warning('Unexpected character ID 0 in base_control action')
            return
        conn: asyncpg.Connection
        async with self._db_pool.acquire() as conn:  # type: ignore
            if await player_blip(*blip, conn=conn):
                self._push_dispatch('player_blip')

    @_log_errors
    async def player_logout(self, evt: event.PlayerLogout) -> None:
        """Validate and dispatch a ``PlayerLogout`` Blip.

        Args:
            event (event.PlayerLogout): The event received.
        """
        blip = (
            evt.timestamp,
            evt.character_id)
        if evt.character_id == 0:
            log.warning('Unexpected character ID 0 in player_logout action')
            return
        conn: asyncpg.Connection
        async with self._db_pool.acquire() as conn:  # type: ignore
            if await player_logout(*blip, conn=conn):
                self._push_dispatch('player_logout')

    @_log_errors
    async def relative_player_blip(
            self, evt: Union[event.Death, event.GainExperience]) -> None:
        """Validate and dispatch a ``RelativePlayerBlip``.

        Args:
            evt (event.Event): The event received.
        """
        if isinstance(evt, event.Death):
            player_a_id = evt.attacker_character_id
            player_b_id = evt.character_id
        else:
            player_a_id = evt.character_id
            player_b_id = evt.other_id
        blip = (
            evt.timestamp,
            player_a_id,
            player_b_id,
            evt.world_id,
            evt.zone_id)
        if (player_a_id == 0 or player_b_id == 0 or player_a_id == player_b_id):
            # For death events, it is common for the attacker (A) to be
            # identical to the victim (B), or for the attacker (A) to be 0.
            #
            # These are therefore silently ignored without a log message as
            # they point to regular, common ingame events like killing oneself
            # or dying to spawn room pain fields.
            if (not isinstance(evt, event.Death)) or player_b_id == 0:
                log.warning(
                    'Unexpected character ID 0 in relative_player_blip action')
            return
        conn: asyncpg.Connection
        async with self._db_pool.acquire() as conn:  # type: ignore
            if await relative_player_blip(*blip, conn=conn):
                self._push_dispatch('relative_player_blip')
