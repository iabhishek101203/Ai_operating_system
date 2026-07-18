import sqlite3
from pathlib import Path
from uuid import UUID

from app.schemas.operations import OperationResult


class SQLiteOperationLog:
    """Small durable operation journal used for audit history and undo lookup."""

    def __init__(self, database_path: Path) -> None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self._database_path = database_path
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS operation_log (
                    operation_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )

    def add(self, result: OperationResult) -> None:
        payload = result.model_dump_json()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO operation_log (operation_id, payload) VALUES (?, ?)",
                (str(result.operation_id), payload),
            )

    def list(self, limit: int = 50) -> list[OperationResult]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM operation_log ORDER BY rowid DESC LIMIT ?", (limit,)
            ).fetchall()
        return [OperationResult.model_validate_json(row[0]) for row in rows]

    def get(self, operation_id: UUID) -> OperationResult | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM operation_log WHERE operation_id = ?", (str(operation_id),)
            ).fetchone()
        return OperationResult.model_validate_json(row[0]) if row else None

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._database_path)
