import os

APP_TITLE = "Expense Management API"
APP_VERSION = "1.0.0"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./expense_management.db")
