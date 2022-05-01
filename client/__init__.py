"""Event listener for the map API stack.

This component handles the real-time WebSocket connection to the
PlanetSide 2 API. It also filters the events, handles basic errors, and
ensures the rest of the stack only sees tidy, sanitized data.

The :class:`EventListener` class is exported from this module, though
the recommended way to use it is to call ``python -m client`` from the
project directory.
"""

from ._client import EventListener

__all__ = [
    'EventListener'
]

__version__ = '0.0.1a1'
