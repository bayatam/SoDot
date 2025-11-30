from app.storage.engine import JsonStorageEngine
from app.storage.repository import TaskRepository
from app.config import DB_FILE_PATH

_db_engine = JsonStorageEngine(db_path=DB_FILE_PATH)

def get_repository() -> TaskRepository:
    """
    FastAPI dependency that provides a repository instance.
    The engine is a singleton, so the lock is shared.
    """
    return TaskRepository(db=_db_engine)