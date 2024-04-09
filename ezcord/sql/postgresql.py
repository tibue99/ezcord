from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import asyncpg


def _process_args(args) -> tuple:
    """If SQL query parameters are passed as a tuple instead of single values,
    the tuple will be unpacked.
    """

    if len(args) == 1 and isinstance(args, tuple):
        if isinstance(args[0], tuple):
            args = args[0]

    return args


class EzConnection(asyncpg.Connection):
    """A subclass of :class:`asyncpg.Connection` that adds aliases
    to be compatible with the sqlite handler.
    """

    async def one(self, sql: str, *args, **kwargs) -> asyncpg.Record | None:
        return await super().fetchrow(sql, *_process_args(args), **kwargs)

    async def all(self, sql: str, *args, **kwargs) -> list:
        return await super().fetch(sql, *_process_args(args), **kwargs)

    async def exec(self, sql: str, *args, **kwargs) -> str:
        return await super().execute(sql, *_process_args(args), **kwargs)


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
    command_timeout:
        The default command timeout for queries. Defaults to ``30 seconds``.
    auto_setup:
        Whether to call :meth:`setup` when the first instance of this class is created.
        Defaults to ``True``.
    **kwargs:
        Keyword arguments for :func:`asyncpg.connect`.
    """

    pool: asyncpg.Pool | None = None
    _auto_setup: list[PGHandler] = []

    def __init__(
        self,
        *,
        host: str | None = None,
        port: str | None = "5432",
        dbname: str | None = None,
        user: str | None = None,
        password: str | None = None,
        command_timeout: int = 30,
        auto_setup: bool = True,
        **kwargs,
    ):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.command_timeout = command_timeout
        self.kwargs = kwargs

        if auto_setup and self not in self._auto_setup:
            PGHandler._auto_setup.append(self)

    async def _check_pool(self) -> asyncpg.Pool:
        """Create a new connection pool. If the class instance has an active connection pool,
        that pool will be returned instead.
        """

        if self.pool is not None:
            return self.pool

        self.pool = await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            database=self.dbname,
            user=self.user,
            password=self.password,
            command_timeout=self.command_timeout,
            connection_class=EzConnection,
            **self.kwargs,
        )
        return self.pool

    async def one(self, sql: str, *args, **kwargs) -> asyncpg.Record | None:
        """Returns one result record. If no record is found, ``None`` is returned.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            Arguments for the query.

        Returns
        -------
        The result record or ``None``.
        """
        args = _process_args(args)
        pool = await self._check_pool()

        async with pool.acquire() as con:
            return await con.fetchrow(sql, *args, **kwargs)

    async def all(self, sql: str, *args, **kwargs) -> list:
        """Returns all result records.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            Arguments for the query.

        Returns
        -------
        A list of result records.
        """
        args = _process_args(args)
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
        """
        args = _process_args(args)
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
            The multiquery to execute.
        *args:
            Arguments for the multiquery.
        """
        pool = await self._check_pool()

        async with pool.acquire() as con:
            return await con.executemany(sql, *args, **kwargs)
