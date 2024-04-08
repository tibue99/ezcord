from __future__ import annotations

from collections.abc import Iterable
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

    pool: asyncpg.Pool | None = None
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

    async def _check_pool(self, **kwargs) -> asyncpg.Pool:
        """Create a new connection pool. If the class instance has an active connection,
        that connection will be returned instead.
        """

        if self.pool is not None:
            return self.pool

        con_args = {**kwargs, **self.kwargs}
        self.pool = await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            database=self.dbname,
            user=self.user,
            password=self.password,
            command_timeout=30,
            **con_args,
        )

        return self.pool

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
        pool = await self._check_pool(**kwargs)

        async with pool.acquire() as con:
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
        pool = await self._check_pool(**kwargs)

        async with pool.acquire() as con:
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
        pool = await self._check_pool(**kwargs)

        async with pool.acquire() as con:
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
        pool = await self._check_pool(**kwargs)

        async with pool.acquire() as con:
            return await con.executemany(sql, args)
