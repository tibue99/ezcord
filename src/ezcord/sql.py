from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import aiosqlite


class DBHandler:
    """A class to handle database connections.

    Parameters
    ----------
    path:
        The path to the database file."""

    def __init__(self, path: str):
        self.DB = path

    async def one(self, sql: str, *args, **kwargs) -> tuple | None | Any:
        """Returns one result row. If no row is found, ``None`` is returned.

        If the query returns only one column, the value of that column is returned.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            The arguments to pass to the query.
        **kwargs:
            Keyword arguments for the connection.
        """
        async with aiosqlite.connect(self.DB, **kwargs) as db:
            async with db.execute(sql, args) as cursor:
                result = await cursor.fetchone()
                if result is None:
                    return None
                if len(result) == 1:
                    return result[0]
                return result

    async def all(self, sql: str, *args, **kwargs) -> list[tuple]:
        """Returns all result rows.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            The arguments to pass to the query.
        **kwargs:
            Keyword arguments for the connection.
        """
        async with aiosqlite.connect(self.DB, **kwargs) as db:
            async with db.execute(sql, args) as cursor:
                return await cursor.fetchall()

    async def getall(self, sql: str, *args, **kwargs) -> AsyncIterator:
        """Returns an :class:`~collections.abc.AsyncIterator` that yields all result rows.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            The arguments to pass to the query.
        **kwargs:
            Keyword arguments for the connection.
        """
        async with aiosqlite.connect(self.DB, **kwargs) as db:
            async with db.execute(sql, args) as cursor:
                async for row in cursor:
                    yield row

    async def exec(self, sql: str, *args, **kwargs) -> None:
        """Executes a SQL query.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            The arguments to pass to the query.
        **kwargs:
            Keyword arguments for the connection.
        """
        async with aiosqlite.connect(self.DB, **kwargs) as db:
            await db.execute(sql, args)
            await db.commit()
