from app.config import Settings

from .memory import InMemoryCounterStorage
from .postgres import PostgresCounterStorage
from .protocol import CounterStorage

__all__ = [
    "CounterStorage",
    "InMemoryCounterStorage",
    "PostgresCounterStorage",
    "create_storage",
]


def create_storage(settings: Settings) -> CounterStorage:
    """Return the storage implementation selected by ``STORAGE_BACKEND``."""
    if settings.storage_backend == "postgres":
        return PostgresCounterStorage(settings.database_url)
    return InMemoryCounterStorage()
