
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routers import auth, notes, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FastAPI Authentication Assignment",
    description="Authentication, user management, and notes API",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(notes.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to the FastAPI Authentication and Notes API"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
