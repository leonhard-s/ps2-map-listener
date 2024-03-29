"""Event listening client definition."""

import datetime
import logging
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar, cast

import auraxium
from auraxium import event

from ._db import Connection, Pool, Row
from ._dispatch import (base_control, player_blip, player_logout,
                        relative_player_blip)
from ._sql import BASE_ID_SQL

T = TypeVar('T')
P = ParamSpec('P')

log = logging.getLogger('listener')

_facility_base_cache: dict[int, int] = {}


async def _base_from_facility(facility_id: int, conn: Connection[Row]) -> int:
    """Get the base ID associated with a given facility.

    Args:
        facility_id (int): The facility ID received via the event
            client.
        conn (Connection): A preexisting database connection to use for
            the conversion.
    """
    if facility_id not in _facility_base_cache:
        log.debug('Cache miss: Querying base ID for facility %d', facility_id)
        async with conn.cursor() as cursor:
            await cursor.execute(BASE_ID_SQL, (facility_id,))
            row = await cursor.fetchone()
        if row is None:
            raise ValueError(f'Invalid facility ID {facility_id}')
        base_id = int(tuple(cast(Any, row))[0])
        _facility_base_cache[facility_id] = base_id
    return _facility_base_cache[facility_id]


def _log_errors(func: Callable[P, Coroutine[Any, Any, T]]
                ) -> Callable[P, Coroutine[Any, Any, T | None]]:
    """Error handler for event handling coroutines.

    Any exceptions raised within the given function will be suppressed
    and logged. On error, ``None`` will be returned.

    Args:
        func (Coroutine): The function to wrap.

    Returns:
        Coroutine function: Wrapped version of `func`.
    """

    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
        try:
            return await func(*args, **kwargs)
        except ValueError:
            log.exception('Argument conversion error in \'%s\':\n'
                          '  Args: %s\n'
                          '  Kwargs: %s',
                          func.__name__, args, kwargs)
        except BaseException as err:  # pylint: disable=broad-except
            log.exception('Ignoring generic exception in \'%s\': %s',
                          func.__name__, type(err))
        return None

    return wrapper


class EventListener:
    """Main event listener instance.

    This class wraps an Auraxium event client, processes the responses
    received and dispatches the corresponding Blips to the database.

    Run :meth:`connect()` to run the event client. It is recommended to
    do this via :meth:`asyncio.AbstractEventLoop.create_task()` as this
    method will never return without error if awaited.

    The event client can be shut down using the :meth:`close()`.

    Args:
        service_id (str): The Census API service ID to use for the
            WebSocket connection.
        pool (Pool): A preexisting connection pool to use for database
            interaction.
    """

    def __init__(self, service_id: str, pool: Pool) -> None:
        self._arx_client = auraxium.EventClient(
            service_id=service_id, no_ssl_certs=True)
        self._db_pool = pool
        # This dictionary is used to keep track of the number of events
        # received
        self._dispatch_cache: dict[str, int] = {}
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
        # # Absolute player blips
        # self._arx_client.add_trigger(auraxium.Trigger(
        #     event.PlayerFacilityCapture,
        #     event.PlayerFacilityDefend,
        #     action=self.player_blip,
        #     name='AbsolutePlayerBlip'))
        # # Relative player blip
        # self._arx_client.add_trigger(auraxium.Trigger(
        #     event.Death,
        #     event.GainExperience.filter_experience(4),  # Heal Player
        #     event.GainExperience.filter_experience(36),  # Spotting bonus
        #     event.GainExperience.filter_experience(54),  # Squad spotting bonus
        #     action=self.relative_player_blip,
        #     name='RelativePlayerBlip'))
        # FacilityCapture
        self._arx_client.add_trigger(auraxium.Trigger(
            auraxium.event.FacilityControl,
            action=self.base_control,
            name='FacilityControl'))
        # # PlayerLogout
        # self._arx_client.add_trigger(auraxium.Trigger(
        #     auraxium.event.PlayerLogout,
        #     action=self.player_logout,
        #     name='PlayerLogout'))

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
        if now >= self._dispatch_last_update + datetime.timedelta(seconds=30.0):
            if log.getEffectiveLevel() <= logging.INFO:
                data = sorted((f'{k}: {v}' for k, v in cache.items()))
                total = sum(cache.values())
                log.info('Sent %d events over the last 30 seconds:\n\t%s',
                         total, '\n\t'.join(data))
            cache.clear()
            self._dispatch_last_update = now

    @_log_errors
    async def base_control(self, evt: event.Event) -> None:
        """Validate and dispatch facility captures.

        Args:
            event (event.Event): The event received.
        """
        if not isinstance(evt, auraxium.event.FacilityControl):
            return
        async with self._db_pool.connection() as conn:
            try:
                base_id = await _base_from_facility(evt.facility_id, conn)
            except ValueError:
                log.debug('Ignoring invalid facility ID %d', evt.facility_id)
                return
            blip_data = (
                evt.timestamp,
                base_id,
                evt.new_faction_id,
                evt.old_faction_id,
                evt.world_id,
                evt.zone_id)
            if await base_control(*blip_data, conn=conn):
                self._push_dispatch('base_control')

    @_log_errors
    async def player_blip(self, evt: event.Event) -> None:
        """Validate and dispatch a ``PlayerBlip``.

        Args:
            event (event.Event): The event received.
        """
        if not isinstance(evt, (event.PlayerFacilityCapture,
                                event.PlayerFacilityDefend)):
            return
        blip_data = (
            evt.timestamp,
            evt.character_id,
            evt.facility_id,
            evt.world_id,
            evt.zone_id)
        if evt.character_id == 0:
            log.warning('Unexpected character ID 0 in base_control action')
            return
        async with self._db_pool.connection() as conn:
            if await player_blip(*blip_data, conn=conn):
                self._push_dispatch('player_blip')

    @_log_errors
    async def player_logout(self, evt: event.Event) -> None:
        """Validate and dispatch a ``PlayerLogout`` Blip.

        Args:
            event (event.Event): The event received.
        """
        if not isinstance(evt, auraxium.event.PlayerLogout):
            return
        blip_data = (
            evt.timestamp,
            evt.character_id)
        if evt.character_id == 0:
            log.warning('Unexpected character ID 0 in player_logout action')
            return
        async with self._db_pool.connection() as conn:
            if await player_logout(*blip_data, conn=conn):
                self._push_dispatch('player_logout')

    @_log_errors
    async def relative_player_blip(self, evt: event.Event) -> None:
        """Validate and dispatch a ``RelativePlayerBlip``.

        Args:
            evt (event.Event): The event received.
        """
        if not isinstance(evt, (event.Death, event.GainExperience)):
            return
        if isinstance(evt, event.Death):
            player_a_id = evt.attacker_character_id
            player_b_id = evt.character_id
        else:
            player_a_id = evt.character_id
            player_b_id = evt.other_id
        blip_data = (
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
        async with self._db_pool.connection() as conn:
            if await relative_player_blip(*blip_data, conn=conn):
                self._push_dispatch('relative_player_blip')
