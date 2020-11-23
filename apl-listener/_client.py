"""Event listening client definition."""

import asyncio
import logging

import asyncpg
import auraxium

from ._dispatch import facility_control, player_blip, relative_player_blip
from ._events import FacilityCapture, PlayerBlip, RelativePlayerBlip

log = logging.getLogger('listener')


_WORLDS = [
    1,  # Connery
    10,  # Miller
    13,  # Cobalt
    17,   # Emerald
    25,  # Briggs
    40  # SolTech
]


class EventListener:
    """The APL event listener instance.

    This class wraps an auraxium client to provide additional logging
    information and define any event types required.

    """

    def __init__(self, service_id: str, conn: asyncpg.Connection) -> None:
        self._arx_client = auraxium.EventClient(service_id=service_id)
        self._db_conn = conn
        self._db_lock = asyncio.Lock()

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
            action=self.facility_control,
            name='FacilityControl',
            # NOTE: Implicitly subscribing to all worlds is not permitted, so
            # we must subscribe to all of them individually.
            worlds=_WORLDS))

    async def facility_control(self, event: auraxium.Event) -> None:
        """Validate and dispatch facility captures.

        :param event: The event received.

        """
        try:
            blip = FacilityCapture(
                event.timestamp,
                int(event.payload['facility_id']),
                # int(event.payload['duration_held']),
                int(event.payload['new_faction_id']),
                int(event.payload['old_faction_id']),
                # int(event.payload['outfit_id']),
                int(event.payload['world_id']),
                int(event.payload['zone_id']))
        except ValueError as err:
            log.exception('Ignoring %s in facility_control action', type(err))
            return
        async with self._db_lock:
            await facility_control(blip, self._db_conn)

    async def player_blip(self, event: auraxium.Event) -> None:
        """Validate and dispatch a :class:`PlayerBlip`.

        :param event: The event received.

        """
        try:
            blip = PlayerBlip(
                event.timestamp,
                int(event.payload['character_id']),
                int(event.payload['facility_id']),
                int(event.payload['world_id']),
                int(event.payload['zone_id']))
        except ValueError as err:
            log.exception('Ignoring %s in facility_control action', type(err))
            return
        if blip.character_id == 0:
            log.warning('Unexpected character ID 0 in facility_control action')
            return
        async with self._db_lock:
            await player_blip(blip, self._db_conn)

    async def relative_player_blip(self, event: auraxium.Event) -> None:
        """Validate and dispatch a :class:`RelativePlayerBlip`.

        :param event: The event received.

        """
        if event.type == auraxium.EventType.DEATH:
            try:
                blip = RelativePlayerBlip(
                    event.timestamp,
                    int(event.payload['attacker_character_id']),
                    int(event.payload['character_id']),
                    int(event.payload['world_id']),
                    int(event.payload['zone_id']))
            except ValueError as err:
                log.exception('Ignoring %s in relative_player_blip action',
                              type(err))
                return
        else:
            try:
                blip = RelativePlayerBlip(
                    event.timestamp,
                    int(event.payload['character_id']),
                    int(event.payload['other_id']),
                    int(event.payload['world_id']),
                    int(event.payload['zone_id']))
            except ValueError as err:
                log.exception(
                    'Ignoring %s in relative_player_blip action', type(err))
                return

        if (blip.character_a_id == 0
                or blip.character_b_id == 0
                or blip.character_a_id == blip.character_b_id):
            # For death events, it is common for the attacker (A) to be
            # identical to the victim (B), or for the attacker (A) to be 0.
            #
            # These are therefore silently ignored without a log message as
            # they point to regular, common ingame events like killing oneself
            # or dying to spawn room pain fields.
            if (not event.payload['event_name'] == 'Death'
                    or blip.character_b_id == 0):
                log.warning(
                    'Unexpected character ID 0 in relative_player_blip action')
            return
        async with self._db_lock:
            await relative_player_blip(blip, self._db_conn)
