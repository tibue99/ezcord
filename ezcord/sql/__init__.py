try:
    from .postgresql import PGHandler
except ImportError:
    # Import fake class that throws an error on initialization if asyncpg is not installed.
    try:
        from .fake_pg import PGHandler  # type: ignore
    except ImportError:
        # This will never be executed, but is needed for type hints, TYPE_CHECKING failed me.
        from .postgresql import PGHandler

from .sqlite import DBHandler
