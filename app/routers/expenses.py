from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/expenses", tags=["Expenses"])


def filter_params(
    category_id: int | None = Query(None, gt=0, description="Filter by category ID"),
    status: schemas.ExpenseStatus | None = Query(None, description="Filter by status"),
    payment_method: schemas.PaymentMethod | None = Query(None, description="Filter by payment method"),
    start_date: date | None = Query(None, description="Expense date >= start_date (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="Expense date <= end_date (YYYY-MM-DD)"),
) -> dict:
    return {
        "category_id": category_id,
        "status": status,
        "payment_method": payment_method,
        "start_date": start_date,
        "end_date": end_date,
    }


@router.post("", response_model=schemas.ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(data: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    return crud.create_expense(db, data)


@router.get("", response_model=list[schemas.ExpenseResponse])
def get_expenses(filters: dict = Depends(filter_params), db: Session = Depends(get_db)):
    return crud.list_expenses(db, **filters)


# Must be declared before /{expense_id} so "total" is not parsed as an ID.
@router.get("/total", response_model=schemas.ExpenseTotalResponse)
def get_total_expenses(filters: dict = Depends(filter_params), db: Session = Depends(get_db)):
    return crud.total_expenses(db, **filters)


@router.get("/{expense_id}", response_model=schemas.ExpenseResponse)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    return crud.get_expense(db, expense_id)


@router.put("/{expense_id}", response_model=schemas.ExpenseResponse)
def update_expense(expense_id: int, data: schemas.ExpenseUpdate, db: Session = Depends(get_db)):
    return crud.update_expense(db, expense_id, data)


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    crud.delete_expense(db, expense_id)
    return {"message": f"Expense {expense_id} deleted successfully"}
