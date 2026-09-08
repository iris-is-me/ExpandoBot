from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import Iterable, Sequence

import aiosqlite
import logging

SQLiteParams = Sequence[object] | dict[str, object] | None

class SQLiteDatabase:
    """Async SQLite wrapper with a small, typed API."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._connection: aiosqlite.Connection | None = None
        self.logger: logging.Logger = logging.getLogger(__name__)
        self._in_transaction = False

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("Database is not connected.")
        return self._connection
    
    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.path)
        self.connection.row_factory = aiosqlite.Row
        await self.execute("PRAGMA foreign_keys = ON")
        await self.execute("PRAGMA journal_mode = WAL")
    
    async def close(self) -> None:
        if self._connection is not None:
            self.logger.info("Closing SQLite connection...")
        
            await self._connection.close()
            self._connection = None
            self.logger.info("SQLite connection closed")
        else:
            self.logger.info("SQLite connection already closed")

    async def execute(self, sql: str, params: SQLiteParams = None) -> aiosqlite.Cursor:
        cursor = await self.connection.execute(sql, params or ())
        if not self._in_transaction:
            await self.connection.commit()
        return cursor

    async def executemany(
        self,
        sql: str,
        params: Iterable[Sequence[object] | dict[str, object]],
    ) -> aiosqlite.Cursor:
        cursor = await self.connection.executemany(sql, params)
        if not self._in_transaction:
            await self.connection.commit()
        return cursor

    async def fetch_one(self, sql: str, params: SQLiteParams = None) -> aiosqlite.Row | None:
        cursor = await self.connection.execute(sql, params or ())
        return await cursor.fetchone()
        
    async def fetch_all(self, sql: str, params: SQLiteParams = None) -> list[aiosqlite.Row]:
        cursor = await self.connection.execute(sql, params or ())
        rows = await cursor.fetchall()
        return list(rows)

    def transaction(self) -> DatabaseTransaction:
        return DatabaseTransaction(self)

class DatabaseTransaction:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    async def __aenter__(self) -> aiosqlite.Connection:
        if self.database._in_transaction:
            raise RuntimeError("A transaction is already active.")
        await self.database.connection.execute("BEGIN")
        self.database._in_transaction = True
        return self.database.connection

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        try:
            if exc_type is None:
                await self.database.connection.commit()
            else:
                await self.database.connection.rollback()
        finally:
            self.database._in_transaction = False

        return False
