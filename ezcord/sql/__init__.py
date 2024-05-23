try:
    from .postgresql import PGHandler
except ImportError:

    class PGHandler:  # type: ignore
        _auto_setup: list = []

        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError(
                "Please install the 'asyncpg' package to use the PostgreSQL handler."
            )


from .sqlite import DBHandler
