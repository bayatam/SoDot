import uuid
from datetime import datetime
from typing import List, Optional

from app.models import TaskCreate, TaskUpdate, TaskRecord
from app.storage.engine import JsonStorageEngine

class TaskRepository:
    """
    Pure Data Access Layer. 
    Handles reading/writing TaskRecords to the DB Engine.
    """
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

    async def save(self, record: TaskRecord) -> TaskRecord:
        """
        Persist a full record. 
        Used for both Creation (new ID) and Updates (existing ID).
        """
        data = await self.db.read()
        # model_dump(mode='json') ensures datetimes are serialized to ISO strings
        data[record.id] = record.model_dump(mode='json')
        await self.db.write(data)
        return record

    async def delete(self, task_id: str) -> bool:
        """Remove a task by ID. Returns True if deleted, False if not found."""
        data = await self.db.read()
        if task_id in data:
            del data[task_id]
            await self.db.write(data)
            return True
        return False