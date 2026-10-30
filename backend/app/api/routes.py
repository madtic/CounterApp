from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.schemas import CounterResponse, HealthResponse
from app.storage import CounterStorage

router = APIRouter()


def get_storage(request: Request) -> CounterStorage:
    """Expose the storage instance created during application startup."""
    return request.app.state.storage


StorageDep = Annotated[CounterStorage, Depends(get_storage)]


@router.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"name": "Counter API", "docs": "/docs"}


@router.get("/health", response_model=HealthResponse, tags=["ops"])
async def health(request: Request) -> HealthResponse:
    return HealthResponse(
        status="ok",
        storage=request.app.state.settings.storage_backend,
    )


@router.get("/api/counter", response_model=CounterResponse, tags=["counter"])
async def get_counter(storage: StorageDep) -> CounterResponse:
    return CounterResponse(value=await storage.get_value())


@router.post("/api/counter/increment", response_model=CounterResponse, tags=["counter"])
async def increment_counter(storage: StorageDep) -> CounterResponse:
    return CounterResponse(value=await storage.increment())


@router.post(
    "/api/counter/decrement",
    response_model=CounterResponse,
    tags=["counter"],
    responses={status.HTTP_501_NOT_IMPLEMENTED: {"description": "Not implemented yet"}},
)
async def decrement_counter() -> CounterResponse:
    # TODO(exercise): extend CounterStorage with a ``decrement`` method,
    # implement it for both storage backends and call it here.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Decrement is not implemented yet.",
    )
