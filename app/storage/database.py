import json
from pathlib import Path
from typing import Dict

# JSON database file - located in project root
DB_FILE = Path(__file__).parent.parent / "data/database.json"


def load_db(db_path: Path = None) -> Dict[str, dict]:
    """Load database from JSON file. Mimics database connection read operation."""
    db_path = db_path or DB_FILE
    
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create empty database if it doesn't exist
    if not db_path.exists():
        save_db({}, db_path)
        return {}
    
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        # If file is corrupted or can't be read, return empty database
        return {}


def save_db(data: Dict[str, dict], db_path: Path = None) -> None:
    """Save database to JSON file. Mimics database connection write operation."""
    db_path = db_path or DB_FILE
    
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
