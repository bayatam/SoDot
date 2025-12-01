import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.storage.repository import TaskRepository
from app.models import TaskRecord
from app.storage.engine import JsonStorageEngine

class TestTaskRepository:

    @pytest.fixture
    def mock_engine(self):
        """Create a mock JsonStorageEngine."""
        engine = MagicMock(spec=JsonStorageEngine)
        engine.read = AsyncMock()
        engine.write = AsyncMock()
        return engine

    @pytest.fixture
    def repository(self, mock_engine):
        """Create a TaskRepository instance injected with the mock engine."""
        return TaskRepository(mock_engine)

    @pytest.fixture
    def sample_record(self):
        """A valid domain record."""
        return TaskRecord(
            id="task-1",
            title="Test Task",
            description="Test Description",
            dueDate="2024-12-31",
            isCompleted=False,
            createdAt=datetime(2024, 1, 1, 0, 0, 0)
        )

    @pytest.fixture
    def sample_json_data(self, sample_record):
        """What that record looks like inside the JSON file (serialized)."""
        return {
            "id": "task-1",
            "title": "Test Task",
            "description": "Test Description",
            "dueDate": "2024-12-31",
            "isCompleted": False,
            "createdAt": "2024-01-01T00:00:00"
        }

    # --- Test Save ---

    @pytest.mark.asyncio
    async def test_save_persists_record(self, repository, mock_engine, sample_record):
        """Test that save() writes the record to the engine."""
        mock_engine.read.return_value = {}
        
        result = await repository.save(sample_record)
        
        assert result == sample_record
        mock_engine.write.assert_called_once()
        
        # Verify persistence format
        saved_data = mock_engine.write.call_args[0][0]
        assert "task-1" in saved_data
        assert saved_data["task-1"]["title"] == "Test Task"
        assert saved_data["task-1"]["id"] == "task-1"

    @pytest.mark.asyncio
    async def test_save_overwrites_existing(self, repository, mock_engine, sample_record, sample_json_data):
        """Test that save() overwrites an existing ID."""
        mock_engine.read.return_value = {"task-1": sample_json_data}
        
        updated_record = sample_record.model_copy(update={"title": "New Title"})
        
        await repository.save(updated_record)
        
        saved_data = mock_engine.write.call_args[0][0]
        assert saved_data["task-1"]["title"] == "New Title"

    # --- Test Read ---

    @pytest.mark.asyncio
    async def test_get_all_returns_records(self, repository, mock_engine, sample_json_data):
        """Test fetching all tasks converts dicts to TaskRecords."""
        mock_engine.read.return_value = {
            "task-1": sample_json_data,
            "task-2": {**sample_json_data, "id": "task-2", "title": "Second Task"}
        }
        
        result = await repository.get_all()
        
        assert len(result) == 2
        assert isinstance(result[0], TaskRecord)
        assert result[0].id == "task-1"
        assert result[1].title == "Second Task"

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository, mock_engine, sample_json_data):
        mock_engine.read.return_value = {"task-1": sample_json_data}
        
        result = await repository.get_by_id("task-1")
        
        assert isinstance(result, TaskRecord)
        assert result.title == "Test Task"
        assert result.id == "task-1"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_engine):
        mock_engine.read.return_value = {}
        result = await repository.get_by_id("missing-id")
        assert result is None

    # --- Test Delete ---

    @pytest.mark.asyncio
    async def test_delete_removes_item(self, repository, mock_engine, sample_json_data):
        mock_engine.read.return_value = {
            "task-1": sample_json_data,
            "task-2": {**sample_json_data, "id": "task-2"}
        }
        
        result = await repository.delete("task-1")
        
        assert result is True
        mock_engine.write.assert_called_once()
        
        remaining_data = mock_engine.write.call_args[0][0]
        assert "task-1" not in remaining_data
        assert "task-2" in remaining_data

    @pytest.mark.asyncio
    async def test_delete_returns_false_if_missing(self, repository, mock_engine):
        mock_engine.read.return_value = {}
        
        result = await repository.delete("missing-id")
        
        assert result is False
        mock_engine.write.assert_not_called()