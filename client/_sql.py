"""Loads SQL commands from disk and stores them for later access."""

import os

__all__ = [
    'BASE_ID_SQL',
    'SQL_BASE_CONTROL',
    'SQL_DROP_BASE_CONTROL',
    'SQL_PLAYER',
    'SQL_RELATIVE_PLAYER',
    'SQL_PLAYER_LOGOUT',
]

# Relative directory to the SQL files
_PROJECT_DIR = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
_SQL_DIR = os.path.join(_PROJECT_DIR, 'sql')


def _get_sql(filename: str) -> str:
    """Loads a file from disk and returns its contents."""
    with open(os.path.join(_SQL_DIR, filename), encoding='utf-8') as sql_file:
        return sql_file.read()


BASE_ID_SQL = _get_sql('get_BaseIdFromFacilityId.sql')
GET_SERVER_ALL_TRACKED = _get_sql('get_Server_allTracked.sql')
SQL_BASE_CONTROL = _get_sql('insertBlip_BaseControl.sql')
SQL_DROP_BASE_CONTROL = _get_sql('dropBlip_BaseControl.sql')
SQL_PLAYER = _get_sql('insertBlip_Player.sql')
SQL_RELATIVE_PLAYER = _get_sql('insertBlip_RelativePlayer.sql')
SQL_PLAYER_LOGOUT = _get_sql('insertBlip_PlayerLogout.sql')
