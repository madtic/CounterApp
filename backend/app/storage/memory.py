import asyncio


class InMemoryCounterStorage:
    """Counter kept in process memory.

    All state is lost when the process stops. A lock keeps concurrent
    requests from overwriting each other.
    """

    def __init__(self, initial_value: int = 0) -> None:
        self._value = initial_value
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def get_value(self) -> int:
        async with self._lock:
            return self._value

    async def increment(self) -> int:
        async with self._lock:
            self._value += 1
            return self._value
