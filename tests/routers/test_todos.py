import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, date

from app.main import app
from app.dependencies import get_service
from app.models import TaskRecord
from app.services.tasks import TaskService

# Initialize TestClient
client = TestClient(app)

@pytest.fixture
def mock_service():
    """
    Create a mock Service.
    We mock the business logic methods to return expected Pydantic objects or None.
    """
    service = MagicMock(spec=TaskService)
    service.list_tasks = AsyncMock()
    service.create_task = AsyncMock()
    service.get_task = AsyncMock()
    service.update_task = AsyncMock()
    service.delete_task = AsyncMock()
    return service

@pytest.fixture(autouse=True)
def override_dependency(mock_service):
    """
    Automatically override the real 'get_service' dependency
    with our 'mock_service' for every test in this file.
    """
    app.dependency_overrides[get_service] = lambda: mock_service
    yield
    # Cleanup: remove override after test finishes
    app.dependency_overrides = {}

# --- Tests ---

def test_list_todos_empty(mock_service):
    """Test fetching tasks when DB is empty."""
    mock_service.list_tasks.return_value = []
    
    response = client.get("/todos/")
    
    assert response.status_code == 200
    assert response.json() == []

def test_list_todos_populated(mock_service):
    """Test fetching tasks returns correct data structure."""
    mock_data = [
        TaskRecord(id="1", title="Task A", isCompleted=False, createdAt=datetime.now()),
        TaskRecord(id="2", title="Task B", isCompleted=True, createdAt=datetime.now())
    ]
    mock_service.list_tasks.return_value = mock_data
    
    response = client.get("/todos/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Task A"
    assert data[1]["isCompleted"] is True

def test_create_todo(mock_service):
    """Test creating a task returns 201 and the created object."""
    payload = {
        "title": "New Task",
        "description": "Test Desc",
        "dueDate": "2025-01-01"
    }
    
    # Mock what the service returns after creation
    created_record = TaskRecord(
        id="new-id",
        title="New Task",
        description="Test Desc",
        dueDate=date(2025, 1, 1),
        isCompleted=False,
        createdAt=datetime.now()
    )
    mock_service.create_task.return_value = created_record
    
    response = client.post("/todos/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "new-id"
    assert data["title"] == "New Task"
    
    # Verify service was called correctly
    mock_service.create_task.assert_called_once()

def test_create_todo_min_length_validation(mock_service):
    """Test that empty title triggers 422 validation error."""
    payload = {"title": "", "description": "Fail me"}
    
    response = client.post("/todos/", json=payload)
    
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["loc"] == ["body", "title"]
    assert "at least 1 character" in data["detail"][0]["msg"]
    mock_service.create_task.assert_not_called()

def test_create_todo_max_length_validation(mock_service):
    """Test that title > 100 chars triggers 422 validation error."""
    long_title = "a" * 101 # 101 characters
    payload = {"title": long_title}
    
    response = client.post("/todos/", json=payload)
    
    assert response.status_code == 422
    assert "at most 100 characters" in response.json()["detail"][0]["msg"]
    mock_service.create_task.assert_not_called()

def test_create_todo_strip_whitespace(mock_service):
    """Test that whitespace is automatically stripped from inputs."""
    payload = {"title": "  Clean Me  ", "description": "  I am covered in whitespace  "}
    
    # We need the mock to return something valid so 201 passes
    mock_service.create_task.return_value = TaskRecord(
        id="1", title="Clean Me", description="I am covered in whitespace", 
        createdAt=datetime.now()
    )

    response = client.post("/todos/", json=payload)
    assert response.status_code == 201
    
    call_args = mock_service.create_task.call_args
    # call_args[0][0] is the first positional arg (task_create object)
    task_create_obj = call_args[0][0]
    
    assert task_create_obj.title == "Clean Me"
    assert task_create_obj.description == "I am covered in whitespace"

def test_get_todo_found(mock_service):
    """Test retrieving a single task by ID."""
    mock_record = TaskRecord(id="1", title="Task 1", isCompleted=False, createdAt=datetime.now())
    mock_service.get_task.return_value = mock_record
    
    response = client.get("/todos/1")
    
    assert response.status_code == 200
    assert response.json()["id"] == "1"

def test_get_todo_not_found(mock_service):
    """Test retrieving a non-existent ID returns 404."""
    mock_service.get_task.return_value = None
    
    response = client.get("/todos/999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

def test_update_todo_success(mock_service):
    """Test generic patch update."""
    payload = {"title": "Updated", "isCompleted": True}
    
    updated_record = TaskRecord(
        id="1", 
        title="Updated", 
        isCompleted=True, 
        createdAt=datetime.now()
    )
    mock_service.update_task.return_value = updated_record
    
    response = client.patch("/todos/1", json=payload)
    
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["isCompleted"] is True

def test_update_todo_not_found(mock_service):
    """Test updating a non-existent task returns 404."""
    mock_service.update_task.return_value = None
    
    response = client.patch("/todos/999", json={"title": "Ghost"})
    
    assert response.status_code == 404

def test_delete_todo_success(mock_service):
    """Test deleting a task returns 204 No Content."""
    mock_service.delete_task.return_value = True
    
    response = client.delete("/todos/1")
    
    assert response.status_code == 204
    # 204 responses have no body
    assert response.text == ""

def test_delete_todo_not_found(mock_service):
    """Test deleting non-existent task returns 404."""
    mock_service.delete_task.return_value = False
    
    response = client.delete("/todos/999")
    
    assert response.status_code == 404

def test_complete_todo_endpoint(mock_service):
    """Test the specific 'complete' action endpoint."""
    updated_record = TaskRecord(id="1", title="Task", isCompleted=True, createdAt=datetime.now())
    mock_service.update_task.return_value = updated_record
    
    response = client.post("/todos/1/complete")
    
    assert response.status_code == 200
    assert response.json()["isCompleted"] is True
    
    # Check that service.update_task was called with isCompleted=True
    call_args = mock_service.update_task.call_args
    # call_args[0] are positional args: (task_id, update_payload)
    assert call_args[0][1].isCompleted is True

def test_incomplete_todo_endpoint(mock_service):
    """Test the specific 'incomplete' action endpoint."""
    updated_record = TaskRecord(id="1", title="Task", isCompleted=False, createdAt=datetime.now())
    mock_service.update_task.return_value = updated_record
    
    response = client.post("/todos/1/incomplete")
    
    assert response.status_code == 200
    assert response.json()["isCompleted"] is False
    
    # Check that service.update_task was called with isCompleted=False
    call_args = mock_service.update_task.call_args
    assert call_args[0][1].isCompleted is False