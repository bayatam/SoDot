from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class TodoItem(BaseModel):
    """Base model for a to-do item."""
    title: str = Field(..., description="A short description of the task")
    description: Optional[str] = Field(None, description="A longer explanation")
    dueDate: Optional[date] = Field(None, description="Date when the task should be completed (YYYY-MM-DD)")
    isCompleted: bool = Field(default=False, description="Completion status flag")
    createdAt: datetime = Field(default_factory=datetime.now, description="Timestamp when the item was created")


class TodoItemCreate(BaseModel):
    """Model for creating a new to-do item (without createdAt, which is auto-generated)."""
    title: str = Field(..., description="A short description of the task")
    description: Optional[str] = Field(None, description="A longer explanation")
    dueDate: Optional[date] = Field(None, description="Date when the task should be completed (YYYY-MM-DD)")
    isCompleted: bool = Field(default=False, description="Completion status flag")


class TodoItemUpdate(BaseModel):
    """Model for updating an existing to-do item (all fields optional)."""
    title: Optional[str] = Field(None, description="A short description of the task")
    description: Optional[str] = Field(None, description="A longer explanation")
    dueDate: Optional[date] = Field(None, description="Date when the task should be completed (YYYY-MM-DD)")
    isCompleted: Optional[bool] = Field(None, description="Completion status flag")


class TodoItemResponse(BaseModel):
    """Model for API responses, includes an ID field."""
    id: str = Field(..., description="Unique identifier for the to-do item")
    title: str = Field(..., description="A short description of the task")
    description: Optional[str] = Field(None, description="A longer explanation")
    dueDate: Optional[date] = Field(None, description="Date when the task should be completed (YYYY-MM-DD)")
    isCompleted: bool = Field(..., description="Completion status flag")
    createdAt: datetime = Field(..., description="Timestamp when the item was created")

