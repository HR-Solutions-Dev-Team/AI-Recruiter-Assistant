from fastapi.testclient import TestClient

from app.main import app


def test_healthcheck_returns_200() -> None:
    """Проверка, что health endpoint возвращает 200 OK."""
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # Статус может быть "ok" или "degraded" в зависимости от доступности Redis
    assert data["status"] in ["ok", "degraded"]
