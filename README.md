# SoDot To-Do API Service

SoDot is a RESTful API for managing tasks, built in Python 3.12, with FastAPI, Pydantic.

This project serves to provide insight into my approach to software development, design, and architecture. 

## Setup

#### Clone the repository

```
git clone https://github.com/bayatam/SoDot.git
cd SoDot
```

#### Create and activate a virtual environment

```
# Linux/MacOS
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

#### Install dependencies

```
pip install -r requirements.txt
```

## Running the Project

Start the server using Uvicorn:
```
uvicorn app.main:app --reload
```
The API will be available at http://127.0.0.1:8000.

I also added a demo script that can be ran in a separate terminal, it runs a full lifecycle (create, read, update, delete) over HTTP:
```
python scripts/live_demo.py
```


## Running the Tests
The project includes unit tests for all major classes, and integration tests (against a temporary db file)

Run the full test suite with:

```
pytest
```

Of note, I did not include unit tests for the JsonStorageEngine (app/storage/engine.py), as I considered it seperate from the main project, given that it would be a real DB in a real project.

## Design Choices
I split the architecture into:
- API Endpoints under routers/, this handles http concerns, like input validation and status codes.
- Business Logic under services/, this is somewhat empty now, doing only id generation and timestamping, but if we were to expand to add the optional functionality (such as filtering), they would all fall here.
- Data Access under storage/, this is split between the engine, which interacts with the database.json file, and is intended to let me abstract away its fake nature, and the repository, which manages reading/writing, and connecting to the database.

Of note about the Update in CRUD:

- Contrary to the example given, I used PATCH instead of PUT. PATCH felt like it fit better for record updates, while PUT feels like it is more about replacing a record.
- `PATCH /todos/{task_id}` technically allows for modifying the task completion. This was not in the specification, but a byproduct of my TaskUpdate pydantic model. I could have blocked using PATCH to modify the completion state, but I thought allowing the isCompleted field, but ignoring its value made for poor API design, so I left that loophole in. Given more time I would split TaskUpdate to separate this.

#### Testing
Each class has its unit tests, I added integration tests somewhat early, when I had all the functionality. This let me be confident when separating the Business Logic layer from the API Endpoints, as I could check whether the end-to-end functionality was unaltered.

#### Structure

```
|-- app/
|   |-- routers/        # API Endpoints
|   |-- services/       # Business Logic
|   |-- storage/        # Data Access
|   |-- models.py       # Pydantic Schemas
|   |-- dependencies.py # Dependency Injection wiring
|   |-- main.py         # App Entrypoint
|-- data/               # Local JSON storage location
|-- scripts/            # Helper scripts (Live Demo)
|-- tests/              # Pytest Suite
|   |-- integration/    # Full-stack tests
|   |-- routers/        # Unit tests for Endpoints
|   |-- services/       # Unit tests for Business Logic
|   |-- storage/        # Unit tests for Repository
+-- requirements.txt
```

## Assumptions
- I assumed we do not mind anyone being able to modify any note. I could not have added Auth given the time limit, but I'd have added a `x-user-id` header to requests and used that to simulate authentication. I could have added a `user-id` field to the records and only allow interaction with the tasks that have a matching user-id.

## Future Work / Time Limitation Tradeoffs

- I did not track time closely, but I believe I went a bit over time to add a bit of input validation, this would be the main thing that I would expand on given more time.
- I wanted to rename `app/routers/todos.py` to tasks.py to match the naming under `app/services/`. I thought against renaming the file when doing the original renaming, but for consistency sake, tasks.py is a better name.
- Auth as stated in the assumptions, if I had extra time after all the optional tasks.
- The `INFO:     127.0.0.1:50469 - "GET /favicon.ico HTTP/1.1" 404 Not Found` in the logs is annoying and fixable with only a tiny change, I would add this to main.py
```
# Favicon endpoint to suppress browser requests
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Suppress favicon 404 errors"""
    return Response(status_code=204)
```

#### Note on the file-storage refactor (commit id b73de9fbd934a4e41195827608b5a28bbe00e6b5)
This was a calculated risk to save time in the long run. I wanted the simulated data access layer to eventually have a separation between the functions that touch the JSON datafile directly (app/storage/engine.py), and those that provide manage data access (app/storage/repository.py). I thought doing this earlier would speed up the rest of the development, as I'd have a proper interface between service code and the JSON database. But the refactor took much longer than I expected, in part because I got nerdsniped by adding concurrency.

If this were to be done again, I might still try to do this refactor, as separating the Repository and Engine is key for fast future refactoring, but keep any concurrency stuff out, as it is not worth much in terms of what we care to show for the project.

