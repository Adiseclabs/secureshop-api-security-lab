"""
scripts/reset_database.py
----------------------------
Deletes the local SQLite database file and any persisted training-mode
scenario state, then re-initializes everything from scratch (fresh fake
data, and - if TRAINING_MODE=true - a freshly randomized scenario set).

Usage (from project root):
    python scripts/reset_database.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import config

db_file = os.path.join(os.path.dirname(__file__), "..", config.DATABASE_PATH)
db_file = os.path.abspath(db_file)

if os.path.exists(db_file):
    os.remove(db_file)
    print(f"Removed existing database: {db_file}")
else:
    print("No existing database file found.")

if os.path.exists(config.TRAINING_STATE_FILE):
    os.remove(config.TRAINING_STATE_FILE)
    print("Cleared previous training-mode scenario state.")

print("Re-initializing...")
os.system(f'"{sys.executable}" "{os.path.join(os.path.dirname(__file__), "init_database.py")}"')
