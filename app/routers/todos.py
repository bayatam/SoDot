import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Path

from app.models import TaskCreate, TaskResponse, TaskUpdate
from app.storage.repository import TaskRepository
from app.dependencies import get_repository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/todos",
    tags=["todos"]
)

@router.get("/", response_model=List[TaskResponse])
async def list_todos(
    repo: TaskRepository = Depends(get_repository)
):
    """
    Retrieve all to-do items.
    """
    tasks = await repo.get_all()
    logger.info(f"Fetched {len(tasks)} tasks")
    return tasks

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    task_data: TaskCreate,
    repo: TaskRepository = Depends(get_repository)
):
    """
    Create a new to-do item.
    """
    logger.info(f"Request to create task: {task_data.title}")
    created_task = await repo.create(task_data)
    logger.info(f"Successfully created task ID: {created_task.id}")
    return created_task

@router.get("/{task_id}", response_model=TaskResponse)
async def get_todo(
    task_id: str = Path(..., description="The ID of the task to retrieve"),
    repo: TaskRepository = Depends(get_repository)
):
    """
    Retrieve a specific to-do item by ID.
    """
    task = await repo.get_by_id(task_id)
    if not task:
        logger.warning(f"Get Task failed: ID {task_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_todo(
    task_update: TaskUpdate,
    task_id: str = Path(..., description="The ID of the task to update"),
    repo: TaskRepository = Depends(get_repository)
):
    """
    Update a to-do item (partial update).
    Modify title, description, due date, or status.
    """
    logger.info(f"Request to update task ID: {task_id}")
    updated_task = await repo.update(task_id, task_update)
    if not updated_task:
        logger.warning(f"Update Task failed: ID {task_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    logger.info(f"Successfully updated task ID: {task_id}")
    return updated_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    task_id: str = Path(..., description="The ID of the task to delete"),
    repo: TaskRepository = Depends(get_repository)
):
    """
    Delete a to-do item.
    """
    logger.info(f"Request to delete task ID: {task_id}")
    deleted = await repo.delete(task_id)
    if not deleted:
        logger.warning(f"Delete Task failed: ID {task_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    logger.info(f"Successfully deleted task ID: {task_id}")
    return None

@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_todo(
    task_id: str = Path(..., description="The ID of the task to mark as complete"),
    repo: TaskRepository = Depends(get_repository)
):
    """
    Mark a specific to-do item as completed.
    """
    # Reuse generic update logic with hardcoded status
    update_payload = TaskUpdate(isCompleted=True)
    
    updated_task = await repo.update(task_id, update_payload)
    if not updated_task:
        logger.warning(f"Complete Task failed: ID {task_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    logger.info(f"Successfully marked task {task_id} as complete")
    return updated_task

@router.post("/{task_id}/incomplete", response_model=TaskResponse)
async def incomplete_todo(
    task_id: str = Path(..., description="The ID of the task to mark as incomplete"),
    repo: TaskRepository = Depends(get_repository)
):
    """
    Mark a specific to-do item as not completed.
    """
    # Reuse generic update logic with hardcoded status
    update_payload = TaskUpdate(isCompleted=False)
    
    updated_task = await repo.update(task_id, update_payload)
    if not updated_task:
        logger.warning(f"Incomplete Task failed: ID {task_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    logger.info(f"Successfully marked task {task_id} as incomplete")
    return updated_task