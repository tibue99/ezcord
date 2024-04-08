from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from typing import Any

import asyncpg


class PGHandler:
    """A class that provides helper methods for PostgreSQL databases.

    Parameters
    ----------
    host:
        The host of the database.
    port:
        The port of the database.
    dbname:
        The name of the database.
    user:
        The user of the database.
    password:
        The password of the database.
    connection:
        A connection to the database. If not provided, a new connection will be created.
        If ``auto_connect`` is ``True``, this will be ignored.
    auto_setup:
        Whether to call :meth:`setup` when the first instance of this class is created. Defaults to ``True``.
        This is called in the ``on_ready`` event of the bot.
    retries:
        The number of times to retry connecting to the database. Defaults to ``2``.

    **kwargs:
        Keyword arguments for :func:`asyncpg.connect`.
    """

    _auto_setup: list[PGHandler] = []

    def __init__(
        self,
        *,
        host: str,
        port: str,
        dbname: str,
        user: str,
        password: str,
        connection: asyncpg.Connection | None = None,
        auto_setup: bool = True,
        retries: int = 2,
        **kwargs,
    ):
        self.connection = connection
        self.retries = retries
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.connection = connection
        self.kwargs = kwargs

        if auto_setup and self not in self._auto_setup:
            PGHandler._auto_setup.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return await self.close()

    def _process_args(self, args) -> tuple:
        """If SQL query parameters are passed as a tuple instead of single values,
        the tuple will be unpacked.

        If ``conv_json`` is ``True``, all dicts will be converted to JSON strings.
        """

        if len(args) == 1 and isinstance(args, tuple):
            if isinstance(args[0], tuple):
                args = args[0]

        return args

    def start(self, **kwargs) -> PGHandler:
        """Opens a new connection with the current DB settings. Additional settings can
        be provided as keyword arguments.

        This should be used as an asynchronous context manager. The connection will commit
        automatically after exiting the context manager.

        Parameters
        ----------
        **kwargs:
            Additional keyword arguments for :func:`asyncpg.connect`.

        Example
        -------
        .. code-block:: python3

            class VipDB(DBHandler):
                def __init__(self):
                    super().__init__("ezcord.db")

                async def setup(self):
                    async with self.start() as db:
                        await db.exec(
                            "CREATE TABLE IF NOT EXISTS vip (id INTEGER PRIMARY KEY, name TEXT)"
                        )
                        await db.exec("INSERT INTO vip (name) VALUES (?)", "Timo")
        """
        cls = deepcopy(self)
        cls.kwargs = {**self.kwargs, **kwargs}

        return cls

    async def connect(self, **kwargs) -> PGHandler:
        """Alias for :meth:`start`."""

        return self.start(**kwargs)

    async def _connect(self, **kwargs) -> asyncpg.Connection:
        """Connect to a database. If the class instance has an active connection,
        that connection will be returned instead.
        """

        if self.connection is not None:
            return self.connection

        con_args = {**kwargs, **self.kwargs}
        self.connection = await asyncpg.connect(
            host=self.host,
            port=self.port,
            database=self.dbname,
            user=self.user,
            password=self.password,
            **con_args,
        )

        return self.connection

    async def close(self):
        """Commits and closes the current connection to the database.

        This is called automatically when using :meth:`start` as a context manager.
        """
        if self.connection is not None:
            await self.connection.close()

    async def _close(self, db: asyncpg.Connection):
        if not self.connection:
            await db.close()

    async def one(self, sql: str, *args, **kwargs) -> asyncpg.Record | None:
        """Returns one result row. If no row is found, ``None`` is returned.

        If the query returns only one column, the value of that column is returned.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            Arguments for the query.
        **kwargs:
            Keyword arguments for the connection.

        Returns
        -------
        The result row or ``None``. A result row is either a tuple or a single value.
        """
        args = self._process_args(args)
        con = await self._connect(**kwargs)

        result = await con.fetchrow(sql, *args)

        # if len(result) == 1:
        #     return result[0]

        return result

    async def all(self, sql: str, *args, **kwargs) -> list:
        """Returns all result rows.

        If the query returns only one column, the values of that column are returned.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            Arguments for the query.
        **kwargs:
            Keyword arguments for the connection.

        Returns
        -------
        A list of result rows. A result row is either a tuple or a single value.
        """
        args = self._process_args(args)
        con = await self._connect(**kwargs)

        result = await con.fetch(sql, *args)

        # if len(result) == 0 or len(result[0]) == 1:
        #     return [row[0] for row in result]

        return result

    async def exec(self, sql: str, *args, **kwargs) -> str:
        """Executes a SQL query.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            Arguments for the query.
        **kwargs:
            Keyword arguments for the connection.
        """
        args = self._process_args(args)
        con = await self._connect(**kwargs)
        return await con.execute(sql, *args)

    async def execute(self, sql: str, *args, **kwargs) -> str:
        """Alias for :meth:`exec`."""
        return await self.exec(sql, *args, **kwargs)

    async def executemany(self, sql: str, args: Iterable[Iterable[Any]], **kwargs) -> str:
        """Executes a SQL multiquery.

        Parameters
        ----------
        sql:
            The mutliquery to execute.
        *args:
            Arguments for the mutliquery.
        **kwargs:
            Keyword arguments for the connection.
        """
        con = await self._connect(**kwargs)
        return await con.executemany(sql, args)
