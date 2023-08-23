from __future__ import annotations

from copy import deepcopy

import aiosqlite


class DBHandler:
    """A class that provides helper methods for SQLite databases.

    Parameters
    ----------
    path:
        The path to the database file.
    transaction:
        Automatically create a new connection that will be used for all queries.
        A transaction must be closed with :meth:`close` or by using ``end=True`` in :meth:`exec`.
    connection:
        A connection to the database. If not provided, a new connection will be created.
        If ``transaction`` is ``True``, this will be ignored.
    auto_setup:
        Whether to call :meth:`setup` when the first instance of this class is created. Defaults to ``True``.
        This is called in the ``on_ready`` event of the bot.
    **kwargs:
        Keyword arguments for :func:`aiosqlite.connect`.
    """

    _auto_setup: dict[type[DBHandler], DBHandler] = {}

    def __init__(
        self,
        path: str,
        connection: aiosqlite.Connection | None = None,
        transaction: bool = False,
        auto_setup: bool = True,
        **kwargs,
    ):
        self.DB = path
        self.connection = connection
        self.transaction = transaction
        self.kwargs = kwargs

        if auto_setup and self.__class__ not in DBHandler._auto_setup:
            DBHandler._auto_setup[self.__class__] = self

    @staticmethod
    def _process_args(args) -> tuple:
        """If SQL query parameters are passed as a tuple instead of single values,
        the tuple will be unpacked.
        """
        if len(args) == 1 and isinstance(args, tuple):
            if isinstance(args[0], tuple):
                return args[0]
        return args

    def start(self):
        """Returns an instance of :class:`.DBHandler` with the current settings
        and ``transaction=True``.
        """
        cls = deepcopy(self)
        cls.transaction = True
        return cls

    async def _connect(self, **kwargs) -> aiosqlite.Connection:
        """Connect to an SQLite database. This is useful for transactions."""

        if self.connection is not None:
            return self.connection

        con_args = {**kwargs, **self.kwargs}

        if self.transaction:
            self.connection = await aiosqlite.connect(self.DB, **con_args)
            return self.connection

        db = await aiosqlite.connect(self.DB, **con_args)
        return db

    async def close(self):
        """Close the current connection to the database."""
        if self.connection is not None:
            await self.connection.commit()
            await self.connection.close()

    async def _close(self, db):
        if not self.connection:
            await db.close()

    async def one(self, sql: str, *args, **kwargs):
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
        db = await self._connect(**kwargs)
        try:
            async with db.execute(sql, args) as cursor:
                result = await cursor.fetchone()
        except Exception as e:
            await self._close(db)
            raise e

        await self._close(db)

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
            Arguments for the query.
        **kwargs:
            Keyword arguments for the connection.

        Returns
        -------
        A list of result rows. A result row is either a tuple or a single value.
        """
        args = self._process_args(args)
        db = await self._connect(**kwargs)
        try:
            async with db.execute(sql, args) as cursor:
                result = await cursor.fetchall()
        except Exception as e:
            await self._close(db)
            raise e

        await self._close(db)
        if len(result) == 0 or len(result[0]) == 1:
            return [row[0] for row in result]

        return result

    async def exec(self, sql: str, *args, end: bool = False, **kwargs) -> None:
        """Executes a SQL query.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        end:
            Whether to commit and close the connection after executing the query.
            This is only needed for transactions.
        *args:
            Arguments for the query.
        **kwargs:
            Keyword arguments for the connection.
        """
        args = self._process_args(args)
        db = await self._connect(**kwargs)
        try:
            await db.execute(sql, args)
        except Exception as e:
            if end or not self.connection:
                await db.commit()
                await db.close()
            raise e
        if end or not self.connection:
            await db.commit()
            await db.close()
