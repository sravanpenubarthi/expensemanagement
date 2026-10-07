from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  (registers tables)
from app.config import APP_TITLE, APP_VERSION
from app.database import Base, engine
from app.exceptions import register_exception_handlers
from app.routers import categories, expenses


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Manage employee expenses and expense categories.",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(categories.router)
app.include_router(expenses.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": f"{APP_TITLE} is running", "docs": "/docs"}
