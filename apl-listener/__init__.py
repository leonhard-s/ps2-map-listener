"""Event listener component of APL.

This module exports the :class:`EventListener` class, which will listen
for websocket events sent by the PS2 event streaming endpoints and
parse them for use in APL.

Additionally, it includes a command line interface that will create and
launch the listener. See its documentation for details.

"""

from ._client import EventListener
from ._events import PlayerBlip, RelativePlayerBlip

__all__ = [
    'EventListener',
    'PlayerBlip',
    'RelativePlayerBlip'
]

__version__ = '0.0.1a0'
