# This is used to import PGHandler while asyncpg not installed. Once the class is initialized
# by the user, an error is thrown.


class PGHandler:
    _auto_setup: list = []

    def __init__(self, *args, **kwargs):
        raise ModuleNotFoundError(
            "Please install the 'asyncpg' package to use the PostgreSQL handler."
        )
