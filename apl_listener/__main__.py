"""Main script for launching the APL listener component.

This script sets up logging, connects to the database and instantiates
the event listening client.

For a list of command line arguments and their purpose, run this script
with the ``--help`` flag set.
"""

import argparse
import asyncio
import logging

import asyncpg

from ._client import EventListener

log = logging.getLogger('listener')

# Default database configuration
DEFAULT_DB_HOST = '127.0.0.1'
DEFAULT_DB_NAME = 'postgres'
DEFAULT_DB_USER = 'postgres'

# Logging configuration
fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
fh_ = logging.FileHandler(filename='debug.log', encoding='utf-8', mode='w+')
sh_ = logging.StreamHandler()
fh_.setFormatter(fmt)
sh_.setFormatter(fmt)


async def main(service_id: str, db_host: str, db_user: str,
               db_pass: str, db_name: str) -> None:
    """Asynchronous component of the main listener script.

    This coroutine acts much like the ``if __name__ == '__main__':``
    clause below, but supports asynchronous methods.

    Args:
        service_id (str): The census API service ID to use.
        db_host (str): Host address of the PostgreSQL server.
        db_user (str): Login user for the database server.
        db_pass (str): Login password for the database server.
        db_name (str): Name of the database to access.
    """
    # Create database connection
    log.info('Connecting to database \'%s\' at %s as user \'%s\'...',
             db_name, db_host, db_user)
    pool: asyncpg.pool.Pool = asyncpg.create_pool(  # type: ignore
        user=db_user, password=db_pass, database=db_name, host=db_host)
    await pool  # Initialise the pool
    log.info('Database connection successful')
    # Set up event client
    log.info('Preparing event listener...')
    client = EventListener(service_id=service_id, pool=pool)
    # This try block catches any interrupts and ensures all of the components
    # are exited gracefully before the error gets thrown at the user's screen.
    try:
        await client.connect()
    except BaseException:
        log.exception('An exception has occurred; closing connections...')
    finally:
        log.info('Closing database connection...')
        await pool.close()  # type: ignore
        log.info('Shutting down event listener...')
        await client.close()


if __name__ == '__main__':
    # Define command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--service-id', '-S', default='s:example',
        help='The service ID used to access the PS2 API')
    parser.add_argument(
        '--db-user', '-U', default=DEFAULT_DB_USER,
        help='The user account to use when connecting to the database')
    parser.add_argument(
        '--db-pass', '-P', required=True,
        help='The password to use when connecting to the database')
    parser.add_argument(
        '--db-host', '-H', default=DEFAULT_DB_HOST,
        help='The address of the database host')
    parser.add_argument(
        '--db-name', '-N', default=DEFAULT_DB_NAME,
        help='The name of the database to access')
    parser.add_argument(
        '--log-level', '-L', default='INFO',
        choices=['DISABLE', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
        help='The log level to use; for levels greater than "DEBUG", '
             'the logging input from Auraxium will also be included')
    # Parse arguments from sys.argv
    kwargs = vars(parser.parse_args())
    # Optioanlly set up logging
    if kwargs['log_level'] != 'DISABLE':
        log_level = getattr(logging, kwargs.pop('log_level'))
        log.setLevel(log_level)
        log.addHandler(fh_)
        log.addHandler(sh_)
        # Add another logger for auraxium
        arx_log = logging.getLogger('auraxium')
        # The following will exclude auraxium's DEBUG spam from this logger
        arx_log.setLevel(max(log_level, logging.INFO))
        arx_log.addHandler(fh_)
        arx_log.addHandler(sh_)
    # Run utility
    try:
        asyncio.run(main(**kwargs))
    except InterruptedError:
        log.info('The application has been shut down by an external signal')
    except KeyboardInterrupt:
        log.info('The application has been shut down by the user')
    except BaseException as err:
        log.exception('An unhandled exception occurred:')
        raise err from err
