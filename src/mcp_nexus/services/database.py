"""Async SQLite persistence for MCP Nexus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import aiosqlite


class Database:
    """Small async SQLite repository for settings, templates, and events."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS prompt_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                body TEXT NOT NULL,
                variables TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS protocol_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                direction TEXT NOT NULL,
                method TEXT,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await self._connection.commit()

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    def _require_connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("Database is not connected")
        return self._connection

    async def set_setting(self, key: str, value: Any) -> None:
        connection = self._require_connection()
        encoded = json.dumps(value)
        await connection.execute(
            """
            INSERT INTO settings(key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value,
            updated_at=CURRENT_TIMESTAMP
            """,
            (key, encoded),
        )
        await connection.commit()

    async def get_setting(self, key: str, default: Any = None) -> Any:
        connection = self._require_connection()
        async with connection.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
        return default if row is None else json.loads(row["value"])

    async def record_event(self, direction: str, payload: dict[str, Any], method: str | None = None) -> int:
        connection = self._require_connection()
        cursor = await connection.execute(
            "INSERT INTO protocol_events(direction, method, payload) VALUES (?, ?, ?)",
            (direction, method, json.dumps(payload)),
        )
        await connection.commit()
        return int(cursor.lastrowid)

    async def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        connection = self._require_connection()
        async with connection.execute(
            "SELECT id, direction, method, payload, created_at "
            "FROM protocol_events ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 1000)),),
        ) as cursor:
            rows = await cursor.fetchall()
        return [
            {
                "id": row["id"],
                "direction": row["direction"],
                "method": row["method"],
                "payload": json.loads(row["payload"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    async def save_template(self, name: str, body: str, variables: list[str]) -> int:
        connection = self._require_connection()
        cursor = await connection.execute(
            """
            INSERT INTO prompt_templates(name, body, variables)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET body=excluded.body,
            variables=excluded.variables, updated_at=CURRENT_TIMESTAMP
            RETURNING id
            """,
            (name, body, json.dumps(variables)),
        )
        row = await cursor.fetchone()
        await connection.commit()
        return int(row["id"])

    async def get_template(self, name: str) -> dict[str, Any] | None:
        connection = self._require_connection()
        async with connection.execute(
            "SELECT id, name, body, variables, created_at, updated_at "
            "FROM prompt_templates WHERE name = ?",
            (name,),
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "body": row["body"],
            "variables": json.loads(row["variables"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    async def list_templates(self) -> list[dict[str, Any]]:
        connection = self._require_connection()
        async with connection.execute(
            "SELECT name, body, variables, created_at, updated_at "
            "FROM prompt_templates ORDER BY name"
        ) as cursor:
            rows = await cursor.fetchall()
        return [
            {
                "name": row["name"],
                "body": row["body"],
                "variables": json.loads(row["variables"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
