import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def fast_and_reliable(monkeypatch):
    # No sleeping, no random failures unless a test asks for them
    monkeypatch.setattr(settings, "min_latency_ms", 0)
    monkeypatch.setattr(settings, "max_latency_ms", 0)
    monkeypatch.setattr(settings, "failure_rate", 0.0)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "payment-service"


def test_charge_approved():
    r = client.post("/charge", json={"amount_cents": 500})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "approved"
    assert body["amount_cents"] == 500
    assert body["payment_id"]


def test_charge_declined_when_failure_rate_is_one(monkeypatch):
    monkeypatch.setattr(settings, "failure_rate", 1.0)
    r = client.post("/charge", json={"amount_cents": 500})
    assert r.status_code == 402


@pytest.mark.parametrize("body", [{"amount_cents": 0}, {"amount_cents": -5}, {}])
def test_charge_rejects_invalid_amount(body):
    assert client.post("/charge", json=body).status_code == 422