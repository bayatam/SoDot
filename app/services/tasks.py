import uuid
from datetime import datetime
from typing import List, Optional

from app.models import TaskCreate, TaskUpdate, TaskRecord
from app.storage.repository import TaskRepository

class TaskService:
    """
    Business Logic Layer.
    Handles ID generation, timestamps, and data merging.
    """
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    async def list_tasks(self) -> List[TaskRecord]:
        return await self.repo.get_all()

    async def get_task(self, task_id: str) -> Optional[TaskRecord]:
        return await self.repo.get_by_id(task_id)

    async def create_task(self, task_create: TaskCreate) -> TaskRecord:
        new_id = str(uuid.uuid4())
        timestamp = datetime.now()

        record = TaskRecord(
            id=new_id,
            createdAt=timestamp,
            **task_create.model_dump()
        )
        
        return await self.repo.save(record)

    async def update_task(self, task_id: str, update_data: TaskUpdate) -> Optional[TaskRecord]:
        current_record = await self.repo.get_by_id(task_id)
        if not current_record:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        updated_record = current_record.model_copy(update=update_dict)

        return await self.repo.save(updated_record)

    async def delete_task(self, task_id: str) -> bool:
        return await self.repo.delete(task_id)