from __future__ import annotations

import json
from collections.abc import Iterable
from copy import deepcopy
from typing import Any

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

    Example
    -------
    You can use this class with an asynchronous context manager:

    .. code-block:: python3

            async with DBHandler("ezcord.db") as db:
                await db.exec("CREATE TABLE IF NOT EXISTS vip (id INTEGER PRIMARY KEY, name TEXT)")
                await db.exec("INSERT INTO vip (name) VALUES (?)", "Timo")
    """

    _auto_setup: list[DBHandler] = []

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

        if auto_setup and self not in self._auto_setup:
            DBHandler._auto_setup.append(self)

    async def __aenter__(self):
        self.auto_connect = True
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

        if self.conv_json:
            json_args: tuple = ()
            for arg in args:
                if isinstance(arg, dict):
                    json_args = json_args + (json.dumps(arg),)
                else:
                    json_args = json_args + (arg,)
            args = json_args

        return args

    def start(
        self, *, conv_json: bool | None = None, foreign_keys: bool | None = None, **kwargs
    ) -> DBHandler:
        """Opens a new connection with the current DB settings. Additional settings can
        be provided as keyword arguments.

        This should be used as an asynchronous context manager. The connection will commit
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
        cls.auto_connect = True
        cls.kwargs = {**self.kwargs, **kwargs}

        # override settings if provided
        if conv_json is not None:
            cls.conv_json = conv_json
        if foreign_keys is not None:
            cls.foreign_keys = foreign_keys

        return cls

    async def connect(self, **kwargs) -> DBHandler:
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

        if "conv_json" in kwargs:
            self.conv_json = kwargs.pop("conv_json")
        if "foreign_keys" in kwargs:
            self.foreign_keys = kwargs.pop("foreign_keys")

        con_args = {**kwargs, **self.kwargs}
        con = await aiosqlite.connect(self.DB, **con_args)

        if self.auto_connect:
            self.connection = con

        if self.foreign_keys:
            await con.execute("PRAGMA foreign_keys = ON")

        return con

    async def close(self):
        """Commits and closes the current connection to the database.

        This is called automatically when using :meth:`start` as a context manager.
        """
        if self.connection is not None:
            await self.connection.commit()
            await self.connection.close()

    async def _close(self, db: aiosqlite.Connection):
        if not self.connection:
            await db.close()

    async def _commit_and_close(self, db: aiosqlite.Connection, end: bool = False):
        if not self.connection or end:
            await db.commit()
            await db.close()

    @staticmethod
    def _convert_tuple_json(result: tuple) -> tuple:
        if not isinstance(result, tuple):
            result = (result,)

        new_result: tuple = ()
        for value in result:
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass
            new_result = new_result + (value,)

        return new_result

    def _convert_json_one(self, result: tuple) -> tuple:
        """Converts all JSON strings from :meth:`one` to dicts (if enabled)."""

        if not self.conv_json or not result:
            return result

        return self._convert_tuple_json(result)

    def _convert_json_all(self, result: list) -> list:
        """Converts all JSON strings from :meth:`all` to dicts (if enabled)."""

        if self.conv_json:
            return [self._convert_tuple_json(row) for row in result]
        return result

    async def one(self, sql: str, *args, fill: bool = False, **kwargs):
        """Returns one result row. If no row is found, ``None`` is returned.

        If the query returns only one column, the value of that column is returned.

        Parameters
        ----------
        sql:
            The SQL query to execute.
        *args:
            Arguments for the query.
        fill:
            Whether to return ``None`` for all selected values if no row is found.
            Defaults to ``False``.
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
            if fill:
                return (None,) * len(cursor.description)
            return None

        result = self._convert_json_one(result)
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

        result = self._convert_json_all(result)
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
            await self._commit_and_close(db, end)
            raise e
        await self._commit_and_close(db, end)
        return cursor

    async def execute(self, sql: str, *args, end: bool = False, **kwargs) -> aiosqlite.Cursor:
        """Alias for :meth:`exec`."""
        return await self.exec(sql, *args, end=end, **kwargs)

    async def executemany(
        self, sql: str, args: Iterable[Iterable[Any]], **kwargs
    ) -> aiosqlite.Cursor:
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
        db = await self._connect(**kwargs)
        try:
            cursor = await db.executemany(sql, args)
        except Exception as e:
            await self._commit_and_close(db)
            raise e
        await self._commit_and_close(db)
        return cursor
