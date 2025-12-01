import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_repository
from app.storage.engine import JsonStorageEngine
from app.storage.repository import TaskRepository

# Use TestClient as a context manager to handle startup/shutdown events if any
client = TestClient(app)

@pytest.fixture
def temporary_repo(tmp_path):
    """
    Creates a real Repository and Engine, but points them to a 
    temporary file in the pytest temp directory.
    """
    # tmp_path is a built-in pytest fixture that creates a unique folder per test
    temp_db_file = tmp_path / "test_integration_db.json"
    
    # Initialize the real engine with the temp path
    engine = JsonStorageEngine(db_path=temp_db_file)
    
    # Initialize the real repository
    return TaskRepository(db=engine)

@pytest.fixture(autouse=True)
def override_dependency(temporary_repo):
    """
    Overrides the app's dependency to use our temporary repository.
    This ensures API calls hit our temp file, not the real 'data/database.json'.
    """
    app.dependency_overrides[get_repository] = lambda: temporary_repo
    yield
    # Cleanup overrides after test
    app.dependency_overrides = {}

def test_full_task_lifecycle():
    """
    Scenario: User creates a task, reads it, updates it, and deletes it.
    Verifies the entire data flow works.
    """
    # 1. Create
    payload = {
        "title": "Integration Task",
        "description": "Testing the whole stack",
        "dueDate": "2025-12-31"
    }
    response = client.post("/todos/", json=payload)
    assert response.status_code == 201
    data = response.json()
    task_id = data["id"]
    
    assert data["title"] == "Integration Task"
    assert data["isCompleted"] is False

    # 2. Get (Read)
    get_response = client.get(f"/todos/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == task_id

    # 3. Update (Patch)
    update_payload = {"title": "Updated Title", "isCompleted": True}
    patch_response = client.patch(f"/todos/{task_id}", json=update_payload)
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "Updated Title"
    assert patch_response.json()["isCompleted"] is True

    # 4. Verify Update Persisted
    get_response_2 = client.get(f"/todos/{task_id}")
    assert get_response_2.json()["title"] == "Updated Title"

    # 5. Delete
    delete_response = client.delete(f"/todos/{task_id}")
    assert delete_response.status_code == 204

    # 6. Verify Gone
    get_response_3 = client.get(f"/todos/{task_id}")
    assert get_response_3.status_code == 404

def test_specific_actions_workflow():
    """
    Scenario: User completes and incompletes a task using specific endpoints.
    """
    # Create
    response = client.post("/todos/", json={"title": "Action Test"})
    task_id = response.json()["id"]

    # Mark Complete
    complete_response = client.post(f"/todos/{task_id}/complete")
    assert complete_response.status_code == 200
    assert complete_response.json()["isCompleted"] is True

    # Mark Incomplete
    incomplete_response = client.post(f"/todos/{task_id}/incomplete")
    assert incomplete_response.status_code == 200
    assert incomplete_response.json()["isCompleted"] is False

def test_error_handling_real_stack():
    """
    Scenario: Operations on non-existent IDs.
    """
    # Get Missing
    response = client.get("/todos/missing-id-123")
    assert response.status_code == 404
    
    # Delete Missing
    response = client.delete("/todos/missing-id-123")
    assert response.status_code == 404
    
    # Update Missing
    response = client.patch("/todos/missing-id-123", json={"title": "New"})
    assert response.status_code == 404