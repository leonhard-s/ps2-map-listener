# APL Listener

This component is responsible for listening to websocket events received from the API and preparing the data for use in other components.

More specific requirements:

- Maintain one or more websocket connections
  - Monitoring event frequency to detect dead subscriptions
  - Detecting downtime
  - Restarting from bad states
- Validating and processing the JSON payloads received
- Updating the database whenever the map changes
  - Continent locks/unlocks
  - API or server maintenance
  - Unstable continents
- Updating the database whenever population shifts
  - Most population inferrence will be done through base captures/defences
  - Vehicle destruction events provide extra position information
  - If a player is killed by another player who has recently been seen in another hex, that hex is now the position of the current player (maybe split player positions evenly between "last confirmed" and "last seen"? testing required!)
