import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_category(client, name="Travel", description="Travel expenses"):
    return client.post("/categories", json={"name": name, "description": description})


def expense_payload(category_id=1, **overrides):
    payload = {
        "employee_name": "Ravi Kumar",
        "category_id": category_id,
        "amount": 1500.0,
        "description": "Client visit cab",
        "expense_date": "2026-10-05",
        "payment_method": "UPI",
        "status": "Pending",
    }
    payload.update(overrides)
    return payload


# ---------- Categories ----------
def test_create_category(client):
    r = make_category(client)
    assert r.status_code == 201
    assert r.json() == {"id": 1, "name": "Travel", "description": "Travel expenses"}


def test_get_all_categories(client):
    make_category(client, "Travel")
    make_category(client, "Food")
    r = client.get("/categories")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_category_by_id(client):
    make_category(client)
    r = client.get("/categories/1")
    assert r.status_code == 200
    assert r.json()["name"] == "Travel"


def test_update_category(client):
    make_category(client)
    r = client.put("/categories/1", json={"name": "Travel & Stay", "description": "Updated"})
    assert r.status_code == 200
    assert r.json()["name"] == "Travel & Stay"


def test_delete_category(client):
    make_category(client)
    assert client.delete("/categories/1").status_code == 200
    assert client.get("/categories/1").status_code == 404


def test_delete_category_with_expenses_is_blocked(client):
    make_category(client)
    client.post("/expenses", json=expense_payload())
    assert client.delete("/categories/1").status_code == 409


def test_duplicate_category(client):
    make_category(client, "Travel")
    assert make_category(client, "Travel").status_code == 409
    assert make_category(client, "travel").status_code == 409  # case-insensitive


def test_update_category_to_duplicate_name(client):
    make_category(client, "Travel")
    make_category(client, "Food")
    r = client.put("/categories/2", json={"name": "Travel"})
    assert r.status_code == 409


def test_get_non_existing_category(client):
    r = client.get("/categories/999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"]


# ---------- Expenses ----------
def test_create_expense(client):
    make_category(client)
    r = client.post("/expenses", json=expense_payload())
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["status"] == "Pending"
    assert body["created_date"]


def test_status_defaults_to_pending(client):
    make_category(client)
    payload = expense_payload()
    del payload["status"]
    r = client.post("/expenses", json=payload)
    assert r.status_code == 201
    assert r.json()["status"] == "Pending"


def test_get_all_expenses(client):
    make_category(client)
    client.post("/expenses", json=expense_payload())
    client.post("/expenses", json=expense_payload(amount=200))
    r = client.get("/expenses")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_expense_by_id(client):
    make_category(client)
    client.post("/expenses", json=expense_payload())
    r = client.get("/expenses/1")
    assert r.status_code == 200
    assert r.json()["employee_name"] == "Ravi Kumar"


def test_update_expense(client):
    make_category(client)
    client.post("/expenses", json=expense_payload())
    r = client.put("/expenses/1", json=expense_payload(amount=999, status="Approved"))
    assert r.status_code == 200
    assert r.json()["amount"] == 999
    assert r.json()["status"] == "Approved"


def test_update_expense_with_missing_category(client):
    make_category(client)
    client.post("/expenses", json=expense_payload())
    r = client.put("/expenses/1", json=expense_payload(category_id=77))
    assert r.status_code == 404


def test_delete_expense(client):
    make_category(client)
    client.post("/expenses", json=expense_payload())
    assert client.delete("/expenses/1").status_code == 200
    assert client.get("/expenses/1").status_code == 404


def test_get_non_existing_expense(client):
    r = client.get("/expenses/999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"]


# ---------- Validation ----------
def test_create_expense_with_non_existing_category(client):
    r = client.post("/expenses", json=expense_payload(category_id=99))
    assert r.status_code == 404


@pytest.mark.parametrize("amount", [0, -50])
def test_create_expense_invalid_amount(client, amount):
    make_category(client)
    r = client.post("/expenses", json=expense_payload(amount=amount))
    assert r.status_code == 422


def test_create_expense_invalid_payment_method(client):
    make_category(client)
    r = client.post("/expenses", json=expense_payload(payment_method="Cheque"))
    assert r.status_code == 422


def test_create_expense_invalid_status(client):
    make_category(client)
    r = client.post("/expenses", json=expense_payload(status="Done"))
    assert r.status_code == 422


def test_create_expense_invalid_date(client):
    make_category(client)
    r = client.post("/expenses", json=expense_payload(expense_date="2026-13-45"))
    assert r.status_code == 422


@pytest.mark.parametrize("field", ["employee_name", "description"])
def test_create_expense_blank_mandatory_fields(client, field):
    make_category(client)
    r = client.post("/expenses", json=expense_payload(**{field: "   "}))
    assert r.status_code == 422


def test_create_expense_missing_category_id(client):
    make_category(client)
    payload = expense_payload()
    del payload["category_id"]
    assert client.post("/expenses", json=payload).status_code == 422


# ---------- Filters & total ----------
@pytest.fixture()
def seeded(client):
    make_category(client, "Travel")
    make_category(client, "Food")
    client.post("/expenses", json=expense_payload(1, amount=100, payment_method="UPI", status="Approved", expense_date="2026-10-01"))
    client.post("/expenses", json=expense_payload(1, amount=200, payment_method="Cash", status="Pending", expense_date="2026-10-03"))
    client.post("/expenses", json=expense_payload(2, amount=300, payment_method="Card", status="Rejected", expense_date="2026-10-06"))
    client.post("/expenses", json=expense_payload(2, amount=400, payment_method="UPI", status="Approved", expense_date="2026-10-10"))
    return client


def test_filter_by_category(seeded):
    r = seeded.get("/expenses", params={"category_id": 1})
    assert [e["amount"] for e in r.json()] == [100, 200]


def test_filter_by_status(seeded):
    r = seeded.get("/expenses", params={"status": "Approved"})
    assert [e["amount"] for e in r.json()] == [100, 400]


def test_filter_by_payment_method(seeded):
    r = seeded.get("/expenses", params={"payment_method": "UPI"})
    assert [e["amount"] for e in r.json()] == [100, 400]


def test_filter_by_date_range(seeded):
    r = seeded.get("/expenses", params={"start_date": "2026-10-01", "end_date": "2026-10-06"})
    assert [e["amount"] for e in r.json()] == [100, 200, 300]


def test_invalid_date_range(seeded):
    r = seeded.get("/expenses", params={"start_date": "2026-10-10", "end_date": "2026-10-01"})
    assert r.status_code == 400


def test_invalid_filter_value(seeded):
    assert seeded.get("/expenses", params={"status": "Done"}).status_code == 422


def test_combined_filters(seeded):
    r = seeded.get("/expenses", params={"status": "Approved", "payment_method": "UPI", "category_id": 2})
    assert [e["amount"] for e in r.json()] == [400]


def test_total_expenses(seeded):
    r = seeded.get("/expenses/total")
    assert r.status_code == 200
    assert r.json() == {"total_amount": 1000.0, "expense_count": 4}


def test_total_expenses_with_filter(seeded):
    r = seeded.get("/expenses/total", params={"status": "Approved"})
    assert r.json() == {"total_amount": 500.0, "expense_count": 2}


def test_total_when_empty(client):
    assert client.get("/expenses/total").json() == {"total_amount": 0.0, "expense_count": 0}
