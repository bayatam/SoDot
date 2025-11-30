import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date, datetime, timedelta

from app.storage.repository import TaskRepository
from app.models import TaskCreate, TaskUpdate, TaskRecord
from app.storage.engine import JsonStorageEngine

class TestTaskRepository:
    """Unit tests for TaskRepository using the final architecture."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock JsonStorageEngine."""
        # We mock the engine so we don't actually touch the file system
        engine = MagicMock(spec=JsonStorageEngine)
        engine.read = AsyncMock()
        engine.write = AsyncMock()
        return engine

    @pytest.fixture
    def repository(self, mock_engine):
        """Create a TaskRepository instance injected with the mock engine."""
        return TaskRepository(mock_engine)

    @pytest.fixture
    def sample_record_data(self):
        """
        Raw JSON data as it would look stored in the file.
        Note the camelCase fields matching your models.
        """
        return {
            "id": "task-1",
            "title": "Test Task",
            "description": "Test Description",
            "dueDate": "2024-12-31",
            "isCompleted": False,
            "createdAt": "2024-01-01T00:00:00"
        }

    # --- Test Create ---
    @pytest.mark.asyncio
    async def test_create_generates_id_and_timestamp(self, repository, mock_engine):
        """Test that create() adds system fields (id, createdAt)."""
        mock_engine.read.return_value = {}
        
        # Input: Simple TaskCreate (User Input)
        payload = TaskCreate(
            title="Buy Milk",
            description="2% Fat",
            dueDate=date(2025, 1, 1),
            isCompleted=False
        )
        
        # Action
        result = await repository.create(payload)
        
        # Assert: Returns a full TaskRecord
        assert isinstance(result, TaskRecord)
        assert result.title == "Buy Milk"
        assert result.id is not None           # UUID generated
        assert isinstance(result.createdAt, datetime) # Timestamp generated
        
        # Verify Persistence
        mock_engine.write.assert_called_once()
        saved_data = mock_engine.write.call_args[0][0]
        
        # Check that the key in the dict matches the ID
        assert result.id in saved_data
        assert saved_data[result.id]["title"] == "Buy Milk"
        assert saved_data[result.id]["id"] == result.id

    # --- Test Read ---
    @pytest.mark.asyncio
    async def test_get_all_returns_records(self, repository, mock_engine, sample_record_data):
        """Test fetching all tasks converts dicts to TaskRecords."""
        mock_engine.read.return_value = {
            "task-1": sample_record_data,
            "task-2": {
                **sample_record_data, 
                "id": "task-2", 
                "title": "Second Task"
            }
        }
        
        result = await repository.get_all()
        
        assert len(result) == 2
        assert isinstance(result[0], TaskRecord)
        assert isinstance(result[1], TaskRecord)
        assert result[0].id == "task-1"
        assert result[1].title == "Second Task"

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository, mock_engine, sample_record_data):
        mock_engine.read.return_value = {"task-1": sample_record_data}
        
        result = await repository.get_by_id("task-1")
        
        assert isinstance(result, TaskRecord)
        assert result.title == "Test Task"
        assert result.id == "task-1"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_engine):
        mock_engine.read.return_value = {}
        result = await repository.get_by_id("missing-id")
        assert result is None

    # --- Test Update ---
    @pytest.mark.asyncio
    async def test_update_merges_fields(self, repository, mock_engine, sample_record_data):
        """Test that update() only changes provided fields."""
        # Setup existing data
        mock_engine.read.return_value = {"task-1": sample_record_data}
        
        # Input: Partial update (only changing title and isCompleted)
        update_payload = TaskUpdate(
            title="Updated Title",
            isCompleted=True
        )
        
        result = await repository.update("task-1", update_payload)
        
        # Assert return value
        assert result.title == "Updated Title"     # Changed
        assert result.isCompleted is True          # Changed
        assert result.description == "Test Description" # Preserved (Not None)
        assert result.createdAt == datetime(2024, 1, 1) # Preserved
        
        # Assert persistence
        mock_engine.write.assert_called_once()
        written_record = mock_engine.write.call_args[0][0]["task-1"]
        assert written_record["title"] == "Updated Title"
        assert written_record["description"] == "Test Description"

    @pytest.mark.asyncio
    async def test_update_returns_none_if_missing(self, repository, mock_engine):
        mock_engine.read.return_value = {}
        update_payload = TaskUpdate(title="Ghost Task")
        
        result = await repository.update("missing-id", update_payload)
        
        assert result is None
        mock_engine.write.assert_not_called()

    # --- Test Delete ---
    @pytest.mark.asyncio
    async def test_delete_removes_item(self, repository, mock_engine, sample_record_data):
        mock_engine.read.return_value = {
            "task-1": sample_record_data,
            "task-2": {**sample_record_data, "id": "task-2"}
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
