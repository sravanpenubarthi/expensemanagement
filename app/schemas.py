from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PaymentMethod(str, Enum):
    CASH = "Cash"
    CARD = "Card"
    UPI = "UPI"
    BANK_TRANSFER = "Bank Transfer"


class ExpenseStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


# ---------- Category ----------
class CategoryBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100, examples=["Travel"])
    description: str | None = Field(
        None, max_length=255, examples=["Travel and commute expenses"]
    )


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ---------- Expense ----------
class ExpenseBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    employee_name: str = Field(..., min_length=1, max_length=100, examples=["Ravi Kumar"])
    category_id: int = Field(..., gt=0, examples=[1])
    amount: float = Field(..., gt=0, examples=[1250.50])
    description: str = Field(..., min_length=1, max_length=255, examples=["Client visit cab fare"])
    expense_date: date = Field(..., examples=["2026-10-05"])
    payment_method: PaymentMethod
    status: ExpenseStatus = ExpenseStatus.PENDING


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(ExpenseBase):
    pass


class ExpenseResponse(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_date: datetime


class ExpenseTotalResponse(BaseModel):
    total_amount: float
    expense_count: int
