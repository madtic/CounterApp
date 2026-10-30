import asyncio
import logging

from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS counter (
    id SMALLINT PRIMARY KEY,
    value BIGINT NOT NULL DEFAULT 0
);

INSERT INTO counter (id, value)
VALUES (1, 0)
ON CONFLICT (id) DO NOTHING;
"""

# Upserting a single row makes both operations atomic without an explicit
# transaction: concurrent increments cannot lose an update.
GET_VALUE = """
INSERT INTO counter (id, value)
VALUES (1, 0)
ON CONFLICT (id) DO UPDATE SET value = counter.value
RETURNING value;
"""

INCREMENT = """
INSERT INTO counter (id, value)
VALUES (1, 1)
ON CONFLICT (id) DO UPDATE SET value = counter.value + 1
RETURNING value;
"""


class PostgresCounterStorage:
    """Counter persisted in PostgreSQL.

    ``psycopg[binary]`` ships a self-contained libpq build, which is why this
    also works in a minimal distroless image without a system libpq.
    """

    def __init__(
        self,
        database_url: str,
        *,
        max_attempts: int = 10,
        retry_delay_seconds: float = 2.0,
    ) -> None:
        self._database_url = database_url
        self._max_attempts = max_attempts
        self._retry_delay_seconds = retry_delay_seconds
        self._pool: AsyncConnectionPool | None = None

    async def initialize(self) -> None:
        self._pool = AsyncConnectionPool(
            conninfo=self._database_url,
            min_size=1,
            max_size=10,
            open=False,
        )

        # Docker Compose can start this container before PostgreSQL accepts
        # connections, so retry the first connection a few times.
        for attempt in range(1, self._max_attempts + 1):
            try:
                await self._pool.open(wait=True, timeout=5)
                async with self._pool.connection() as connection:
                    await connection.execute(SCHEMA)
                logger.info("Connected to PostgreSQL")
                return
            except Exception:
                if attempt == self._max_attempts:
                    await self._pool.close()
                    raise
                logger.warning(
                    "PostgreSQL not ready (attempt %s/%s), retrying in %.1fs",
                    attempt,
                    self._max_attempts,
                    self._retry_delay_seconds,
                )
                await asyncio.sleep(self._retry_delay_seconds)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def get_value(self) -> int:
        pool = self._require_pool()
        async with pool.connection() as connection:
            cursor = await connection.execute(GET_VALUE)
            row = await cursor.fetchone()
        return int(row[0])

    async def increment(self) -> int:
        pool = self._require_pool()
        async with pool.connection() as connection:
            cursor = await connection.execute(INCREMENT)
            row = await cursor.fetchone()
        return int(row[0])

    def _require_pool(self) -> AsyncConnectionPool:
        if self._pool is None:
            raise RuntimeError("Storage is not initialized")
        return self._pool
