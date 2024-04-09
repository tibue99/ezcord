from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import asyncpg


class EzConnection(asyncpg.Connection):
    async def one(self, sql: str, *args, **kwargs) -> asyncpg.Record | None:
        return await super().fetchrow(sql, *args, **kwargs)

    async def all(self, sql: str, *args, **kwargs) -> list:
        return await super().fetch(sql, *args, **kwargs)

    async def exec(self, sql: str, *args, **kwargs) -> str:
        return await super().execute(sql, *args, **kwargs)

    async def executemany(self, sql: str, args: Iterable[Iterable[Any]], **kwargs) -> str:
        return await super().executemany(sql, *args, **kwargs)


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
        auto_setup: bool = True,
        **kwargs,
    ):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.kwargs = kwargs

        if auto_setup and self not in self._auto_setup:
            PGHandler._auto_setup.append(self)

    async def __aenter__(self):
        return self.pool or await self._check_pool()

    def _process_args(self, args) -> tuple:
        """If SQL query parameters are passed as a tuple instead of single values,
        the tuple will be unpacked.

        If ``conv_json`` is ``True``, all dicts will be converted to JSON strings.
        """

        if len(args) == 1 and isinstance(args, tuple):
            if isinstance(args[0], tuple):
                args = args[0]

        return args

    async def _check_pool(self) -> asyncpg.Pool:
        """Create a new connection pool. If the class instance has an active connection,
        that connection will be returned instead.
        """

        if self.pool is not None:
            return self.pool

        self.pool = await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            database=self.dbname,
            user=self.user,
            password=self.password,
            command_timeout=30,
            connection_class=EzConnection,
            **self.kwargs,
        )
        return self.pool

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
            Keyword arguments for the query.

        Returns
        -------
        The result row or ``None``. A result row is either a tuple or a single value.
        """
        args = self._process_args(args)
        pool = await self._check_pool()

        async with pool.acquire() as con:
            return await con.fetchrow(sql, *args, **kwargs)

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
            Keyword arguments for the query.

        Returns
        -------
        A list of result rows. A result row is either a tuple or a single value.
        """
        args = self._process_args(args)
        pool = await self._check_pool()

        async with pool.acquire() as con:
            return await con.fetch(sql, *args, **kwargs)

    async def exec(self, sql: str, *args, **kwargs) -> str:
        """Executes a SQL query.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            Arguments for the query.
        **kwargs:
            Keyword arguments for the query.
        """
        args = self._process_args(args)
        pool = await self._check_pool()

        async with pool.acquire() as con:
            return await con.execute(sql, *args, **kwargs)

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
            Keyword arguments for the query.
        """
        pool = await self._check_pool()

        async with pool.acquire() as con:
            return await con.executemany(sql, *args, **kwargs)
