# Expense Management API

REST API built with **FastAPI**, **SQLAlchemy 2.0**, **Pydantic v2** and **SQLite** to manage employee expenses and expense categories.

## Project Structure

```
expense_management/
├── app/
│   ├── main.py          # FastAPI app, startup, router registration
│   ├── config.py        # App settings (DATABASE_URL)
│   ├── database.py      # Engine, session, Base, get_db dependency
│   ├── models.py        # SQLAlchemy models (Category, Expense)
│   ├── schemas.py       # Pydantic schemas + enums
│   ├── crud.py          # Business logic / DB operations
│   ├── exceptions.py    # Custom exceptions + global handlers
│   └── routers/
│       ├── categories.py
│       └── expenses.py
├── tests/test_api.py    # Automated tests (pytest)
├── schema.sql           # SQLite schema
├── postman_collection.json
├── requirements.txt
└── README.md
```

## Setup & Run

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

The SQLite file `expense_management.db` and its tables are created automatically on first start.

## Run Automated Tests

```bash
pytest -v
```

## Endpoints

### Categories
| Method | Endpoint | Description | Success |
|--------|----------|-------------|---------|
| POST | `/categories` | Create category | 201 |
| GET | `/categories` | List categories | 200 |
| GET | `/categories/{category_id}` | Get category | 200 |
| PUT | `/categories/{category_id}` | Update category | 200 |
| DELETE | `/categories/{category_id}` | Delete category | 200 |

### Expenses
| Method | Endpoint | Description | Success |
|--------|----------|-------------|---------|
| POST | `/expenses` | Create expense | 201 |
| GET | `/expenses` | List expenses (with filters) | 200 |
| GET | `/expenses/total` | Total of expenses (accepts same filters) | 200 |
| GET | `/expenses/{expense_id}` | Get expense | 200 |
| PUT | `/expenses/{expense_id}` | Update expense | 200 |
| DELETE | `/expenses/{expense_id}` | Delete expense | 200 |

### Query Filters (`GET /expenses` and `GET /expenses/total`)
| Param | Example |
|-------|---------|
| `category_id` | `/expenses?category_id=1` |
| `status` | `/expenses?status=Approved` |
| `payment_method` | `/expenses?payment_method=UPI` |
| `start_date`, `end_date` | `/expenses?start_date=2026-10-01&end_date=2026-10-06` |

Filters can be combined, e.g. `/expenses/total?status=Approved&payment_method=UPI`.

## Validation Rules

- Category name: required, unique (case-insensitive)
- Employee name, description: required, cannot be blank
- Category ID: required, category must exist
- Amount: must be greater than 0
- Expense date: must be a valid date (`YYYY-MM-DD`)
- Payment method: `Cash`, `Card`, `UPI`, `Bank Transfer`
- Status: `Pending`, `Approved`, `Rejected` (defaults to `Pending`)

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 400 | Invalid date range (`start_date` after `end_date`) |
| 404 | Category or expense not found |
| 409 | Duplicate category name, or deleting a category that still has expenses |
| 422 | Pydantic validation error (amount, enums, date, blank fields) |
| 500 | Unexpected database error |

## Sample Request

```json
POST /expenses
{
  "employee_name": "Ravi Kumar",
  "category_id": 1,
  "amount": 1250.50,
  "description": "Client visit cab fare",
  "expense_date": "2026-10-05",
  "payment_method": "UPI",
  "status": "Pending"
}
```

## Testing with Postman

1. Delete `expense_management.db` (if it exists) and start the server.
2. Import `postman_collection.json`.
3. Run the collection folders in order (1 to 5). Each request includes a status-code test, and the collection covers every scenario in the assignment:
   CRUD for both resources, all four filters, the total, non-existing category on create, amount `0`/negative, invalid payment method/status, duplicate category and not-found lookups.

## Design Notes

- Deleting a category that still has expenses is blocked with `409` so no expense is left pointing to a missing category.
- `/expenses/total` is declared before `/expenses/{expense_id}` so the route is not mistaken for an ID.
- Updates (`PUT`) replace all editable fields and re-check that the category exists.
