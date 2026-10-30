# Counter Playground

```
┌─────────────────────┐        HTTP /api/*        ┌─────────────────────┐
│  React frontend     │ ────────────────────────▶ │  FastAPI backend    │
│  Vite build         │                           │  uv + uvicorn       │
└─────────────────────┘                           └──────────┬──────────┘
                                                             │ CounterStorage
                                                   ┌─────────┴─────────┐
                                                   ▼                   ▼
                                              in-memory           PostgreSQL
```

## What is included

- **Backend**: uv + FastAPI, async API, storage behind a `Protocol`.
  - in-memory storage (default)
  - PostgreSQL storage
- **Frontend**: React + Vite, current counter value and increment/decrement buttons.

The decrement endpoint is intentionally **not implemented**. It returns `501 Not
Implemented` and is the first exercise.

---

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/routes.py           # HTTP endpoints
│   │   ├── config.py               # environment configuration
│   │   ├── main.py                 # app factory + lifespan
│   │   ├── schemas.py
│   │   └── storage/
│   │       ├── protocol.py         # CounterStorage protocol
│   │       ├── memory.py
│   │       ├── postgres.py
│   │       └── __init__.py         # storage factory
│   ├── tests/
│   ├── pyproject.toml
│   ├── uv.lock
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── package-lock.json
│   └── nginx.conf
```

---

## API

| Method | Path | Result |
| --- | --- | --- |
| `GET` | `/api/counter` | `200 {"value": 0}` |
| `POST` | `/api/counter/increment` | increments by one, returns new value |
| `POST` | `/api/counter/decrement` | `501 Not Implemented` |
| `GET` | `/health` | `200 {"status": "ok", "storage": "postgres"}` |
| `GET` | `/docs` | Swagger UI |

Quick test:

```bash
curl -s http://localhost:8000/api/counter
curl -s -X POST http://localhost:8000/api/counter/increment
```

---

## Storage backends

The API only knows the `CounterStorage` protocol from
[`backend/app/storage/protocol.py`](backend/app/storage/protocol.py):

```python
class CounterStorage(Protocol):
    async def initialize(self) -> None: ...
    async def close(self) -> None: ...
    async def get_value(self) -> int: ...
    async def increment(self) -> int: ...
```

The implementation is selected in `create_storage()` via `STORAGE_BACKEND`:

```bash
# volatile, in-process counter
STORAGE_BACKEND=memory docker compose up --build

# persistent counter in the bundled PostgreSQL container (default)
STORAGE_BACKEND=postgres docker compose up --build
```

`PostgresCounterStorage` creates the `counter` table on startup and uses an atomic
upsert (`INSERT ... ON CONFLICT ... RETURNING`) for increments. It also retries the
first connection, because Compose may start the API before PostgreSQL is ready.

---

## Local development

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

If you want PostgreSQL locally, start only the database and export the URL:

```bash
docker compose up -d db
export STORAGE_BACKEND=postgres
export DATABASE_URL=postgresql://counter:counter@localhost:5432/counter
uv run uvicorn app.main:app --reload
```

Run the checks:

```bash
uv run ruff check .
uv run pytest
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to
`http://localhost:8000`, so no CORS setup is needed for local development.

If the API runs elsewhere:

```bash
BACKEND_PROXY_TARGET=http://192.168.1.20:8000 npm run dev
```
