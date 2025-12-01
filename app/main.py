import logging
from fastapi import FastAPI
from app.routers import todos

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="Sodot To-Do API",
    description="A RESTful API for managing to-do items",
    version="1.0.0"
)


app.include_router(todos.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Sodot To-Do API",
        "docs": "/docs",
        "version": "1.0.0"
    }

