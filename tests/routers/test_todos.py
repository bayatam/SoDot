import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, date

from app.main import app
from app.dependencies import get_repository
from app.models import TaskRecord
from app.storage.repository import TaskRepository

# Initialize TestClient
client = TestClient(app)

@pytest.fixture
def mock_repo():
    """
    Create a mock repository.
    We mock the methods so they return expected Pydantic objects or None.
    """
    repo = MagicMock(spec=TaskRepository)
    repo.get_all = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo

@pytest.fixture(autouse=True)
def override_dependency(mock_repo):
    """
    Automatically override the real 'get_repository' dependency
    with our 'mock_repo' for every test in this file.
    """
    app.dependency_overrides[get_repository] = lambda: mock_repo
    yield
    # Cleanup: remove override after test finishes
    app.dependency_overrides = {}

# --- Tests ---

def test_list_todos_empty(mock_repo):
    """Test fetching tasks when DB is empty."""
    mock_repo.get_all.return_value = []
    
    response = client.get("/todos/")
    
    assert response.status_code == 200
    assert response.json() == []

def test_list_todos_populated(mock_repo):
    """Test fetching tasks returns correct data structure."""
    mock_data = [
        TaskRecord(id="1", title="Task A", isCompleted=False, createdAt=datetime.now()),
        TaskRecord(id="2", title="Task B", isCompleted=True, createdAt=datetime.now())
    ]
    mock_repo.get_all.return_value = mock_data
    
    response = client.get("/todos/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Task A"
    assert data[1]["isCompleted"] is True

def test_create_todo(mock_repo):
    """Test creating a task returns 201 and the created object."""
    payload = {
        "title": "New Task",
        "description": "Test Desc",
        "dueDate": "2025-01-01"
    }
    
    # Mock what the repo returns after creation
    created_record = TaskRecord(
        id="new-id",
        title="New Task",
        description="Test Desc",
        dueDate=date(2025, 1, 1),
        isCompleted=False,
        createdAt=datetime.now()
    )
    mock_repo.create.return_value = created_record
    
    response = client.post("/todos/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "new-id"
    assert data["title"] == "New Task"
    
    # Verify repo was called correctly
    mock_repo.create.assert_called_once()

def test_get_todo_found(mock_repo):
    """Test retrieving a single task by ID."""
    mock_record = TaskRecord(id="1", title="Task 1", isCompleted=False, createdAt=datetime.now())
    mock_repo.get_by_id.return_value = mock_record
    
    response = client.get("/todos/1")
    
    assert response.status_code == 200
    assert response.json()["id"] == "1"

def test_get_todo_not_found(mock_repo):
    """Test retrieving a non-existent ID returns 404."""
    mock_repo.get_by_id.return_value = None
    
    response = client.get("/todos/999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

def test_update_todo_success(mock_repo):
    """Test generic patch update."""
    payload = {"title": "Updated", "isCompleted": True}
    
    updated_record = TaskRecord(
        id="1", 
        title="Updated", 
        isCompleted=True, 
        createdAt=datetime.now()
    )
    mock_repo.update.return_value = updated_record
    
    response = client.patch("/todos/1", json=payload)
    
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["isCompleted"] is True

def test_update_todo_not_found(mock_repo):
    """Test updating a non-existent task returns 404."""
    mock_repo.update.return_value = None
    
    response = client.patch("/todos/999", json={"title": "Ghost"})
    
    assert response.status_code == 404

def test_delete_todo_success(mock_repo):
    """Test deleting a task returns 204 No Content."""
    mock_repo.delete.return_value = True
    
    response = client.delete("/todos/1")
    
    assert response.status_code == 204
    # 204 responses have no body
    assert response.text == ""

def test_delete_todo_not_found(mock_repo):
    """Test deleting non-existent task returns 404."""
    mock_repo.delete.return_value = False
    
    response = client.delete("/todos/999")
    
    assert response.status_code == 404

def test_complete_todo_endpoint(mock_repo):
    """Test the specific 'complete' action endpoint."""
    updated_record = TaskRecord(id="1", title="Task", isCompleted=True, createdAt=datetime.now())
    mock_repo.update.return_value = updated_record
    
    response = client.post("/todos/1/complete")
    
    assert response.status_code == 200
    assert response.json()["isCompleted"] is True
    
    # Check that repo.update was called with isCompleted=True
    call_args = mock_repo.update.call_args
    assert call_args[0][1].isCompleted is True

def test_incomplete_todo_endpoint(mock_repo):
    """Test the specific 'incomplete' action endpoint."""
    updated_record = TaskRecord(id="1", title="Task", isCompleted=False, createdAt=datetime.now())
    mock_repo.update.return_value = updated_record
    
    response = client.post("/todos/1/incomplete")
    
    assert response.status_code == 200
    assert response.json()["isCompleted"] is False
    
    # Check that repo.update was called with isCompleted=False
    call_args = mock_repo.update.call_args
    assert call_args[0][1].isCompleted is False