import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE_PATH = BASE_DIR / "data" / "database.json"