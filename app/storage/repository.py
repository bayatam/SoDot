import uuid
from datetime import datetime
from typing import List, Optional

from app.models import TaskCreate, TaskUpdate, TaskRecord
from app.storage.engine import JsonStorageEngine

class TaskRepository:
    def __init__(self, db: JsonStorageEngine):
        self.db = db

    async def get_all(self) -> List[TaskRecord]:
        """Fetch all tasks as Internal Records."""
        data = await self.db.read()
        return [TaskRecord(**item) for item in data.values()]

    async def get_by_id(self, task_id: str) -> Optional[TaskRecord]:
        """Fetch a single task by ID."""
        data = await self.db.read()
        item = data.get(task_id)
        return TaskRecord(**item) if item else None

    async def create(self, task_create: TaskCreate) -> TaskRecord:
        """
        Creates a new record.
        """
        new_id = str(uuid.uuid4())
        timestamp = datetime.now()

        # Combine input data with system-generated fields
        record = TaskRecord(
            id=new_id,
            createdAt=timestamp,
            **task_create.model_dump()
        )

        data = await self.db.read()
        
        # model_dump(mode='json') ensures datetimes are serialized to ISO strings
        data[new_id] = record.model_dump(mode='json')
        
        await self.db.write(data)
        return record

    async def update(self, task_id: str, task_update: TaskUpdate) -> Optional[TaskRecord]:
        """Updates an existing record."""
        data = await self.db.read()
        
        if task_id not in data:
            return None
            
        # Load existing record
        existing_record = TaskRecord(**data[task_id])
        
        # Merge updates
        # exclude_unset=True ensures we don't overwrite existing data with None
        update_data = task_update.model_dump(exclude_unset=True)
        updated_record = existing_record.model_copy(update=update_data)
        
        # Save back to DB
        data[task_id] = updated_record.model_dump(mode='json')
        await self.db.write(data)
        
        return updated_record

    async def delete(self, task_id: str) -> bool:
        """Remove a task by ID. Returns True if deleted, False if not found."""
        data = await self.db.read()
        if task_id in data:
            del data[task_id]
            await self.db.write(data)
            return True
        return False