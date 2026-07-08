from app.schemas.operations import OperationResult


class InMemoryOperationLog:
    """Temporary operation log for milestone 1.

    This will be replaced with SQLModel/SQLite once the operation schema is stable.
    """

    def __init__(self) -> None:
        self._items: list[OperationResult] = []

    def add(self, result: OperationResult) -> None:
        self._items.append(result)

    def list(self) -> list[OperationResult]:
        return list(self._items)
