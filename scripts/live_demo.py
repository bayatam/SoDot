import json
import urllib.request
import urllib.error
import time
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000/todos"

def print_step(step: str):
    print(f"\n{step}")

def print_step_result(message: str, payload: Dict[str, Any] = None, success: bool = True):
    if success:
        print(f"SUCCESS\t-- {message}")
    else:
        print(f"ERROR\t-- {message}")
    if payload:
        print("\tResponse Payload:")
        print(json.dumps(payload, indent=2))

def make_request(method: str, url: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Helper to make HTTP requests using standard library."""
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    
    if data:
        json_data = json.dumps(data).encode('utf-8')
        req.data = json_data

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                return {}
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"ERROR\t-- HTTP Error {e.code}: {e.read().decode()}")
        return None
    except urllib.error.URLError as e:
        print(f"ERROR\t-- Connection Failed: {e.reason}")
        print("\t(Is the server running? Try: uvicorn app.main:app --reload)")
        exit(1)

def run_demo():
    print("STARTING -- Live API Demo against http://127.0.0.1:8000")

    print_step("1. Creating a new Task")
    payload = {
        "title": "Save the world",
        "description": "Just another tuesday",
        "dueDate": "2025-01-01"
    }
    task = make_request("POST", f"{BASE_URL}/", payload)
    if not task:
        print_step_result("Failed to create task, exiting...", False)
        exit(1)
    task_id = task['id']
    print_step_result(f"Created Task: {task['title']} (ID: {task_id})", payload=task)

    print_step("2. Fetching All Tasks")
    tasks = make_request("GET", f"{BASE_URL}/")
    print_step_result(f"Fetched {len(tasks)} tasks", payload=tasks)

    print_step("3. Updating Task (Renaming)")
    update_payload = {"title": "Save a cat"}
    updated_task = make_request("PATCH", f"{BASE_URL}/{task_id}", update_payload)
    print_step_result(f"Updated Title: {updated_task['title']}", payload=updated_task)

    print_step("4. Mark as Complete (Action Endpoint)")
    completed = make_request("POST", f"{BASE_URL}/{task_id}/complete")
    print_step_result(f"Task Completed: {completed['isCompleted']}", payload=completed)

    print_step("5. Deleting Task")
    make_request("DELETE", f"{BASE_URL}/{task_id}")
    print_step_result("Task Deleted", payload={})

    print_step("6. Verifying Deletion")
    try:
        urllib.request.urlopen(f"{BASE_URL}/{task_id}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print_step_result("Verified: Task is 404 Not Found")
        else:
            print_step_result(f"Unexpected Error: {e.code}", success=False)

    print_step("Live Demo Completed")

if __name__ == "__main__":
    run_demo()