import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import DB_FILE_PATH

class JsonStorageEngine:
    """
    Handles raw file I/O with concurrency safety.
    Acts as a singleton connection to the JSON file.
    """
    def __init__(self, db_path: Path = DB_FILE_PATH):
        self.db_path = db_path
        self._lock = asyncio.Lock()  # Mutex to prevent race conditions

    async def read(self) -> Dict[str, Any]:
        """
        Thread-safe, non-blocking read.
        """
        async with self._lock:
            # Run the blocking file IO in a separate thread
            return await asyncio.to_thread(self._load_from_disk)

    async def write(self, data: Dict[str, Any]) -> None:
        """
        Thread-safe, non-blocking write.
        """
        async with self._lock:
            await asyncio.to_thread(self._save_to_disk, data)

    # --- Private Synchronous Methods (The "Driver" logic) ---

    def _load_from_disk(self) -> Dict[str, Any]:
        """Internal synchronous method to read the file."""
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.db_path.exists():
            self._save_to_disk({})
            return {}

        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_to_disk(self, data: Dict[str, Any]) -> None:
        """Internal synchronous method to write to file."""
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)