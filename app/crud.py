from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.exceptions import BadRequestError, ConflictError, DuplicateError, NotFoundError


# ---------- Category ----------
def _get_category_or_404(db: Session, category_id: int) -> models.Category:
    category = db.get(models.Category, category_id)
    if category is None:
        raise NotFoundError(f"Category with id {category_id} not found")
    return category


def _ensure_unique_name(db: Session, name: str, exclude_id: int | None = None) -> None:
    stmt = select(models.Category).where(func.lower(models.Category.name) == name.lower())
    existing = db.scalars(stmt).first()
    if existing and existing.id != exclude_id:
        raise DuplicateError(f"Category with name '{name}' already exists")


def create_category(db: Session, data: schemas.CategoryCreate) -> models.Category:
    _ensure_unique_name(db, data.name)
    category = models.Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def list_categories(db: Session) -> list[models.Category]:
    return list(db.scalars(select(models.Category).order_by(models.Category.id)))


def get_category(db: Session, category_id: int) -> models.Category:
    return _get_category_or_404(db, category_id)


def update_category(db: Session, category_id: int, data: schemas.CategoryUpdate) -> models.Category:
    category = _get_category_or_404(db, category_id)
    _ensure_unique_name(db, data.name, exclude_id=category_id)
    category.name = data.name
    category.description = data.description
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = _get_category_or_404(db, category_id)
    in_use = db.scalar(
        select(func.count()).select_from(models.Expense).where(models.Expense.category_id == category_id)
    )
    if in_use:
        raise ConflictError(
            f"Category {category_id} cannot be deleted because it has {in_use} expense(s)"
        )
    db.delete(category)
    db.commit()


# ---------- Expense ----------
def _get_expense_or_404(db: Session, expense_id: int) -> models.Expense:
    expense = db.get(models.Expense, expense_id)
    if expense is None:
        raise NotFoundError(f"Expense with id {expense_id} not found")
    return expense


def _filtered_stmt(
    stmt,
    category_id: int | None,
    status: schemas.ExpenseStatus | None,
    payment_method: schemas.PaymentMethod | None,
    start_date: date | None,
    end_date: date | None,
):
    if start_date and end_date and start_date > end_date:
        raise BadRequestError("start_date cannot be after end_date")
    if category_id is not None:
        stmt = stmt.where(models.Expense.category_id == category_id)
    if status is not None:
        stmt = stmt.where(models.Expense.status == status.value)
    if payment_method is not None:
        stmt = stmt.where(models.Expense.payment_method == payment_method.value)
    if start_date is not None:
        stmt = stmt.where(models.Expense.expense_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(models.Expense.expense_date <= end_date)
    return stmt


def create_expense(db: Session, data: schemas.ExpenseCreate) -> models.Expense:
    _get_category_or_404(db, data.category_id)
    expense = models.Expense(
        **data.model_dump(exclude={"payment_method", "status"}),
        payment_method=data.payment_method.value,
        status=data.status.value,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(db: Session, **filters) -> list[models.Expense]:
    stmt = _filtered_stmt(select(models.Expense), **filters).order_by(models.Expense.id)
    return list(db.scalars(stmt))


def get_expense(db: Session, expense_id: int) -> models.Expense:
    return _get_expense_or_404(db, expense_id)


def update_expense(db: Session, expense_id: int, data: schemas.ExpenseUpdate) -> models.Expense:
    expense = _get_expense_or_404(db, expense_id)
    _get_category_or_404(db, data.category_id)
    expense.employee_name = data.employee_name
    expense.category_id = data.category_id
    expense.amount = data.amount
    expense.description = data.description
    expense.expense_date = data.expense_date
    expense.payment_method = data.payment_method.value
    expense.status = data.status.value
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense_id: int) -> None:
    expense = _get_expense_or_404(db, expense_id)
    db.delete(expense)
    db.commit()


def total_expenses(db: Session, **filters) -> dict:
    stmt = _filtered_stmt(
        select(func.coalesce(func.sum(models.Expense.amount), 0.0), func.count(models.Expense.id)),
        **filters,
    )
    total, count = db.execute(stmt).one()
    return {"total_amount": round(float(total), 2), "expense_count": int(count)}
