import pytest


@pytest.mark.django_db
def test_liveness_returns_ok(api_client):
    response = api_client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readiness_returns_ok_when_database_is_reachable(api_client):
    response = api_client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["checks"]["database"] is True


def test_readiness_returns_503_when_database_is_unreachable(api_client, monkeypatch):
    from apps.health import views

    monkeypatch.setattr(views.ReadinessView, "_check_database", staticmethod(lambda: False))

    response = api_client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"
