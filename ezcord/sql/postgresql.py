from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import asyncpg


def _process_args(args) -> tuple:
    """If SQL query parameters are passed as a tuple instead of single values,
    the tuple will be unpacked.
    """

    if len(args) == 1 and isinstance(args, tuple):
        if isinstance(args[0], tuple):
            args = args[0]

    # convert dict to str
    return tuple(json.dumps(arg) if isinstance(arg, dict) else arg for arg in args)


def _process_one_result(row: asyncpg.Record, default: Any):
    row = row[0] if row is not None and len(row) == 1 else row
    return row if row is not None else default


def _process_exec_status(status: str) -> QueryStatus:
    status_list = status.split(" ")
    if len(status_list) > 1 and not status_list[1].isdigit():
        status_list[0] += " " + status_list[1]
        status_list.pop(1)

    query_type = status_list[0]
    if len(status_list) == 2:
        return QueryStatus(type=query_type, rowcount=int(status_list[1]))
    elif len(status_list) == 3:
        return QueryStatus(
            type=query_type, rowcount=int(status_list[1]), inserts=int(status_list[2])
        )
    else:
        return QueryStatus(type=query_type)


@dataclass
class QueryStatus:
    """A class to access the status of a :meth:`PGHandler.exec` call."""

    type: str
    rowcount: int = 0
    inserts: int = 0


class EzConnection(asyncpg.Connection):
    """A subclass of :class:`asyncpg.Connection` that adds aliases
    to be compatible with the sqlite handler.
    """

    async def one(self, sql: str, *args, default=None, **kwargs):
        row = await super().fetchrow(sql, *_process_args(args), **kwargs)
        return _process_one_result(row, default)

    async def all(self, sql: str, *args, **kwargs) -> list:
        result = await super().fetch(sql, *_process_args(args), **kwargs)
        if result and len(result[0]) == 1:
            return [row[0] for row in result]
        return result

    async def exec(self, sql: str, *args, **kwargs) -> QueryStatus:
        status = await super().execute(sql, *_process_args(args), **kwargs)
        return _process_exec_status(status)

    async def execute(self, *args, **kwargs) -> QueryStatus:
        """Alias for :meth:`exec`."""
        return await self.exec(*args, **kwargs)

    async def fetchval(self, sql: str, *args, default=None, **kwargs):
        value = await super().fetchval(sql, *_process_args(args), **kwargs)
        return value or default


class PGHandler:
    """A class that provides helper methods for PostgreSQL databases.

    .. note::

            It's recommended to set the database connection parameters in the.env file.
            Reference: https://www.postgresql.org/docs/current/libpq-envars.html

    Parameters
    ----------
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
        auto_setup: bool = True,
        **kwargs,
    ):
        self.kwargs = kwargs

        if auto_setup and self not in self._auto_setup:
            PGHandler._auto_setup.append(self)

    async def _check_pool(self) -> asyncpg.Pool:
        """Create a new connection pool. If the class instance has an active connection pool,
        that pool will be returned instead.
        """

        if PGHandler.pool is not None:
            return PGHandler.pool

        PGHandler.pool = await asyncpg.create_pool(connection_class=EzConnection, **self.kwargs)
        return PGHandler.pool

    async def one(self, sql: str, *args, default=None, **kwargs):
        """Returns one result record. If no record is found, ``None`` is returned.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            Arguments for the query.
        default:
            When the query returns no results, this value will be returned instead of ``None``.

        Returns
        -------
        The result record or ``None``.
        """
        args = _process_args(args)
        pool = await self._check_pool()

        async with pool.acquire() as con:
            row = await con.fetchrow(sql, *args, **kwargs)

        return _process_one_result(row, default)

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

    async def fetchval(self, sql: str, *args, default=None, **kwargs):
        """Returns one value.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            Arguments for the query.
        default:
            When the query returns no results, this value will be returned instead of ``None``.

        Returns
        -------
        The value or ``None``.
        """
        args = _process_args(args)
        pool = await self._check_pool()

        async with pool.acquire() as con:
            value = await con.fetchval(sql, *args, **kwargs)

        return value or default

    async def exec(self, sql: str, *args, **kwargs) -> QueryStatus:
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

    async def execute(self, sql: str, *args, **kwargs) -> QueryStatus:
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
            return await con.executemany(sql, args, **kwargs)
