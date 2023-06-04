from __future__ import annotations

from collections.abc import AsyncIterator

import aiosqlite


class DBHandler:
    """A class to handle database connections.

    Parameters
    ----------
    path:
        The path to the database file.
    """

    def __init__(self, path: str):
        self.DB = path

    @staticmethod
    def _process_args(args) -> tuple:
        """If SQL query parameters are passed as a tuple instead of single values,
        the tuple will be unpacked.
        """
        if len(args) == 1 and isinstance(args, tuple):
            return args[0]
        return args

    async def one(self, sql: str, *args, **kwargs):
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

        Returns
        -------
        The result row or ``None``. A result row is either a tuple or a single value.
        """
        args = self._process_args(args)
        async with aiosqlite.connect(self.DB, **kwargs) as db:
            async with db.execute(sql, args) as cursor:
                result = await cursor.fetchone()
                if result is None:
                    return None
                if len(result) == 1:
                    return result[0]
                return result

    async def all(self, sql: str, *args, **kwargs) -> list:
        """Returns all result rows.

        If the query returns only one column, the values of that column are returned.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            The arguments to pass to the query.
        **kwargs:
            Keyword arguments for the connection.

        Returns
        -------
        A list of result rows. A result row is either a tuple or a single value.
        """
        args = self._process_args(args)
        async with aiosqlite.connect(self.DB, **kwargs) as db:
            async with db.execute(sql, args) as cursor:
                result = await cursor.fetchall()
            if len(result) == 0 or len(result[0]) == 1:
                return [row[0] for row in result]
            return result

    async def getall(self, sql: str, *args, **kwargs) -> AsyncIterator:
        """Returns an :class:`~collections.abc.AsyncIterator` that yields all result rows.

        If the query returns only one column, the values of that column are returned.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            The arguments to pass to the query.
        **kwargs:
            Keyword arguments for the connection.
        """
        args = self._process_args(args)
        async with aiosqlite.connect(self.DB, **kwargs) as db:
            async with db.execute(sql, args) as cursor:
                async for row in cursor:
                    yield row if len(row) > 1 else row[0]

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
        args = self._process_args(args)
        async with aiosqlite.connect(self.DB, **kwargs) as db:
            await db.execute(sql, args)
            await db.commit()
