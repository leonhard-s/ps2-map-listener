# PS2 Map Event Listener

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/leonhard-s/ps2-map-listener/Run%20Python%20unit%20tests)
[![Coveralls github branch](https://img.shields.io/coveralls/github/leonhard-s/ps2-map-listener/master)](https://coveralls.io/github/leonhard-s/ps2-map-listener)
[![CodeFactor Grade](https://img.shields.io/codefactor/grade/github/leonhard-s/auraxium)](https://www.codefactor.io/repository/github/leonhard-s/ps2-map-listener)

This component is responsible for listening to WebSocket events received from the API and preparing the data for use in other components.

## What it does

This script subscribes to events through [Auraxium](https://github.com/leonhard-s/auraxium), which takes care of maintaining the streaming connection and handling disconnects or other API errors.

The events received from the PS2 API are generally too specific for our needs, lack important data and do not match our requirements. They are therefore processed and split up or combined into our own internal event definitions, called "Blips".

These Blips are then inserted into the separate `event` schema of the database, which mostly acts as intermediate storage between components. The relevant database tables are replicated via Python data classes in the backend repository, whose definition can be found [here](https://github.com/auto-pl/ps2-map-controller/blob/main/controller/blips.py).

## Status

The listener is currently stable and ready for development use.

### Implemented Blips

- `PlayerBlip` -- That player is definitely here right now
- `RelativePlayerBlip` -- These two players are close to each other
- `PlayerLogout` -- This player logged out and can be purged from the population tracker
- `BaseControl` -- A base has flipped ownership, for any reason (including unlocks or other non-capture events)

### Missing capability

- Subscription monitoring
  - Check event frequency, detect events going missing
  - Dropping and recreating stale subscriptions
- Detecting API downtime and automatically restarting when it becomes available again
