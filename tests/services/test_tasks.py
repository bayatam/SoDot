import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date, datetime

from app.services.tasks import TaskService
from app.storage.repository import TaskRepository
from app.models import TaskCreate, TaskUpdate, TaskRecord

class TestTaskService:
    """Unit tests for the Business Logic Layer."""

    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock(spec=TaskRepository)
        repo.get_all = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.save = AsyncMock()
        repo.delete = AsyncMock()
        return repo

    @pytest.fixture
    def service(self, mock_repo):
        return TaskService(repo=mock_repo)

    @pytest.fixture
    def sample_record(self):
        return TaskRecord(
            id="task-1",
            title="Old Title",
            description="Old Desc",
            dueDate=date(2024, 1, 1),
            isCompleted=False,
            createdAt=datetime(2024, 1, 1, 0, 0, 0)
        )

    # --- Test Creation Logic ---

    @pytest.mark.asyncio
    async def test_create_task_generates_system_fields(self, service, mock_repo):
        """
        Verifies that the Service layer generates:
        1. A UUID (id)
        2. A Timestamp (createdAt)
        """
        input_data = TaskCreate(
            title="Buy Milk", 
            description="2%", 
            dueDate=date(2025, 1, 1)
        )

        mock_repo.save.side_effect = lambda record: record

        result = await service.create_task(input_data)

        assert isinstance(result, TaskRecord)
        assert result.title == "Buy Milk"
        
        assert result.id is not None
        assert isinstance(result.id, str)
        assert len(result.id) > 0  # Likely a UUID
        
        assert result.createdAt is not None
        assert isinstance(result.createdAt, datetime)

        mock_repo.save.assert_called_once()

    # --- Test Update Logic ---

    @pytest.mark.asyncio
    async def test_update_task_merges_partial_fields(self, service, mock_repo, sample_record):
        """
        Verifies that the Service layer correctly merges new fields
        into the existing record without overwriting others with None.
        """
        mock_repo.get_by_id.return_value = sample_record
        mock_repo.save.side_effect = lambda record: record

        # Input: Partial update (only title changes)
        update_payload = TaskUpdate(title="New Title")

        result = await service.update_task("task-1", update_payload)

        assert result.id == "task-1"
        assert result.title == "New Title"       # CHANGED
        assert result.description == "Old Desc"  # PRESERVED
        assert result.isCompleted is False       # PRESERVED
        assert result.createdAt == sample_record.createdAt # PRESERVED

        # Verify repo saved the merged object
        mock_repo.save.assert_called_once()
        saved_record = mock_repo.save.call_args[0][0]
        assert saved_record.title == "New Title"
        assert saved_record.description == "Old Desc"

    @pytest.mark.asyncio
    async def test_update_task_returns_none_if_missing(self, service, mock_repo):
        """Verifies correct handling of non-existent IDs."""
        mock_repo.get_by_id.return_value = None

        result = await service.update_task("ghost-id", TaskUpdate(title="Boo"))

        assert result is None
        mock_repo.save.assert_not_called()

    # --- Test Pass-Throughs (Simple delegation) ---

    @pytest.mark.asyncio
    async def test_list_tasks_delegates_to_repo(self, service, mock_repo):
        mock_repo.get_all.return_value = ["fake-list"]
        result = await service.list_tasks()
        assert result == ["fake-list"]
        mock_repo.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_delegates_to_repo(self, service, mock_repo):
        mock_repo.get_by_id.return_value = "fake-record"
        result = await service.get_task("123")
        assert result == "fake-record"
        mock_repo.get_by_id.assert_called_with("123")

    @pytest.mark.asyncio
    async def test_delete_task_delegates_to_repo(self, service, mock_repo):
        mock_repo.delete.return_value = True
        result = await service.delete_task("123")
        assert result is True
        mock_repo.delete.assert_called_with("123")