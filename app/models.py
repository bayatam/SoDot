from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


# --- Shared Fields (Business Logic) ---
class TaskBase(BaseModel):
    title: str = Field(..., description="A short description of the task")
    description: Optional[str] = Field(None, description="A longer explanation")
    dueDate: Optional[date] = Field(None, description="Date when the task should be completed (YYYY-MM-DD)")
    isCompleted: bool = Field(default=False, description="Completion status flag")


# --- Internal Database Model ---
class TaskRecord(TaskBase):
    """The Source of Truth stored in the DB (includes ID and CreatedAt)."""
    id: str = Field(..., description="Unique identifier for the task")
    createdAt: datetime = Field(..., description="Timestamp when the item was created")


# --- API Input Models ---
class TaskCreate(TaskBase):
    """Model for creating a new task (without createdAt, which is auto-generated)."""
    pass

class TaskUpdate(BaseModel):
    """Model for updating an existing task (all fields optional)."""
    title: Optional[str] = Field(None, description="A short description of the task")
    description: Optional[str] = Field(None, description="A longer explanation")
    dueDate: Optional[date] = Field(None, description="Date when the task should be completed (YYYY-MM-DD)")
    isCompleted: Optional[bool] = Field(None, description="Completion status flag")


# --- API Output Model ---
class TaskResponse(TaskRecord):
    """Model for API responses, includes an ID field. Currently same as Record, but decoupled for safety."""
    pass
