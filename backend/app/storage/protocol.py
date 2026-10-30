from typing import Protocol


class CounterStorage(Protocol):
    """Storage contract used by the API.

    Keep the API dependent on this protocol instead of a concrete database
    driver. Swapping in-memory storage for PostgreSQL then only requires a new
    implementation of these methods.
    """

    async def initialize(self) -> None:
        """Prepare the storage (create tables, open connections, ...)."""
        ...

    async def close(self) -> None:
        """Release resources on application shutdown."""
        ...

    async def get_value(self) -> int:
        """Return the current counter value."""
        ...

    async def increment(self) -> int:
        """Increase the counter by one and return the new value."""
        ...
