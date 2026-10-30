import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app(Settings(storage_backend="memory"))
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_storage_backend(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "storage": "memory"}


def test_counter_starts_at_zero(client: TestClient) -> None:
    response = client.get("/api/counter")

    assert response.status_code == 200
    assert response.json() == {"value": 0}


def test_increment_returns_new_value(client: TestClient) -> None:
    assert client.post("/api/counter/increment").json() == {"value": 1}
    assert client.post("/api/counter/increment").json() == {"value": 2}
    assert client.get("/api/counter").json() == {"value": 2}


def test_decrement_is_not_implemented_yet(client: TestClient) -> None:
    response = client.post("/api/counter/decrement")

    assert response.status_code == 501
    assert response.json()["detail"] == "Decrement is not implemented yet."
