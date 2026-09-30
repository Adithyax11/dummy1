import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import Product


@pytest.fixture()
def client():
    # In-memory SQLite stands in for Postgres
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    with Session() as db:
        db.add_all([
            Product(sku="APPLE-001", name="Apple", price_cents=120, stock=10),
            Product(sku="CHOC-001", name="Chocolate", price_cents=349, stock=5),
        ])
        db.commit()

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").status_code == 200


def test_list_products(client):
    r = client.get("/products")
    assert r.status_code == 200
    assert [p["sku"] for p in r.json()] == ["APPLE-001", "CHOC-001"]


def test_get_stock(client):
    r = client.get("/stock/APPLE-001")
    assert r.status_code == 200
    assert r.json()["stock"] == 10


def test_get_stock_unknown_sku(client):
    assert client.get("/stock/NOPE").status_code == 404


def test_reserve_success(client):
    r = client.post("/reserve", json={"sku": "CHOC-001", "quantity": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["remaining"] == 3
    assert body["total_cents"] == 698


def test_reserve_insufficient_stock(client):
    r = client.post("/reserve", json={"sku": "CHOC-001", "quantity": 10})
    assert r.status_code == 409
    assert client.get("/stock/CHOC-001").json()["stock"] == 5  # unchanged


def test_reserve_unknown_sku(client):
    r = client.post("/reserve", json={"sku": "NOPE", "quantity": 1})
    assert r.status_code == 404


def test_release_restores_stock(client):
    client.post("/reserve", json={"sku": "APPLE-001", "quantity": 4})
    r = client.post("/release", json={"sku": "APPLE-001", "quantity": 4})
    assert r.status_code == 200
    assert client.get("/stock/APPLE-001").json()["stock"] == 10