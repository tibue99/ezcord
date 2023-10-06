from __future__ import annotations

import json
from copy import deepcopy

import aiosqlite


class DBHandler:
    """A class that provides helper methods for SQLite databases.

    Parameters
    ----------
    path:
        The path to the database file.
    connection:
        A connection to the database. If not provided, a new connection will be created.
        If ``auto_connect`` is ``True``, this will be ignored.
    auto_connect:
        Automatically create a new connection that will be used for all queries.
        This is used by :meth:`start`.

        When used without a context manager, this must be closed with :meth:`close`
        or by using ``end=True`` in :meth:`exec`.
    auto_setup:
        Whether to call :meth:`setup` when the first instance of this class is created. Defaults to ``True``.
        This is called in the ``on_ready`` event of the bot.
    conv_json:
        Whether to auto-convert JSON. Defaults to ``False``.
    foreign_keys:
        Whether to enforce foreign keys. Defaults to ``False``.
    **kwargs:
        Keyword arguments for :func:`aiosqlite.connect`.
    """

    _auto_setup: dict[type[DBHandler], DBHandler] = {}

    def __init__(
        self,
        path: str,
        *,
        connection: aiosqlite.Connection | None = None,
        auto_connect: bool = False,
        auto_setup: bool = True,
        conv_json: bool = False,
        foreign_keys: bool = False,
        **kwargs,
    ):
        self.DB = path
        self.connection = connection
        self.auto_connect = auto_connect
        self.conv_json = conv_json
        self.foreign_keys = foreign_keys
        self.kwargs = kwargs

        if auto_setup:
            DBHandler._auto_setup[self.__class__] = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return await self.close()

    @staticmethod
    def _process_args(args) -> tuple:
        """If SQL query parameters are passed as a tuple instead of single values,
        the tuple will be unpacked.
        """
        if len(args) == 1 and isinstance(args, tuple):
            if isinstance(args[0], tuple):
                return args[0]
        return args

    def start(
        self, conv_json: bool | None = None, foreign_keys: bool | None = None, **kwargs
    ) -> DBHandler:
        """Returns a new instance of :class:`.DBHandler` with the current settings
        and ``auto_connect=True``.

        This can be used as an asynchronous context manager. The connection will commit
        automatically after exiting the context manager.

        Parameters
        ----------
        conv_json:
            Whether to auto-convert JSON.
        foreign_keys:
            Whether to enforce foreign keys.
        **kwargs:
            Additional keyword arguments for :func:`aiosqlite.connect`.

        Example
        -------
        .. code-block:: python3

            async with DBHandler.start("ezcord.db") as db:
                await db.exec("CREATE TABLE IF NOT EXISTS vip (id INTEGER PRIMARY KEY, name TEXT)")
                await db.exec("INSERT INTO vip (name) VALUES (?)", ("Timo",))
        """
        cls = deepcopy(self)
        cls.auto_connect = True
        cls.kwargs = {**self.kwargs, **kwargs}

        # override settings if provided
        if conv_json is not None:
            cls.conv_json = conv_json
        if foreign_keys is not None:
            cls.foreign_keys = foreign_keys

        return cls

    async def connect(self, **kwargs):
        """Alias for :meth:`start`."""
        return self.start(**kwargs)

    async def _connect(self, **kwargs) -> aiosqlite.Connection:
        """Connect to an SQLite database. If the class instance has an active connection,
        that connection will be returned instead.

        If ``auto_connect`` is ``True``, a connection will be created and stored
        as the instance connection.
        """

        if self.connection is not None:
            return self.connection

        con_args = {**kwargs, **self.kwargs}

        if self.auto_connect:
            self.connection = await aiosqlite.connect(self.DB, **con_args)
            return self.connection

        return await aiosqlite.connect(self.DB, **con_args)

    async def close(self):
        """Commits and closes the current connection to the database.

        This is called automatically when using :meth:`start` as a context manager.
        """
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

    async def exec(self, sql: str, *args, end: bool = False, **kwargs) -> aiosqlite.Cursor:
        """Executes a SQL query.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        end:
            Whether to commit and close the connection after executing the query.
        *args:
            Arguments for the query.
        **kwargs:
            Keyword arguments for the connection.
        """
        args = self._process_args(args)
        db = await self._connect(**kwargs)
        try:
            cursor = await db.execute(sql, args)
        except Exception as e:
            if end or not self.connection:
                await db.commit()
                await db.close()
            raise e
        if end or not self.connection:
            await db.commit()
            await db.close()
        return cursor

    async def execute(self, sql: str, *args, end: bool = False, **kwargs) -> aiosqlite.Cursor:
        """Alias for :meth:`exec`."""
        return await self.exec(sql, *args, end=end, **kwargs)
