"""
scripts/init_database.py
---------------------------
Creates all tables and loads fake seed data. Safe to re-run - seed_data()
no-ops if users already exist.

Usage (from project root):
    python scripts/init_database.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from database.db import db
from database.seed import seed_data
from config import config
from routes.training.scenario_manager import get_active_scenarios

app = create_app()

with app.app_context():
    os.makedirs(os.path.dirname(os.path.join(os.path.dirname(__file__), "..", config.DATABASE_PATH)), exist_ok=True)
    db.create_all()
    seed_data()

    if config.TRAINING_MODE:
        # Roll (or re-roll) the active scenario set for this fresh build.
        active = get_active_scenarios(force_reroll=True)
        print(f"\nTraining mode is ON. {len(active)} scenario(s) selected for this build.")
        print("Scenario details are intentionally not printed here.")
        print("See docs/developer-remediation-guide.md AFTER you finish manual testing.\n")
    else:
        print("\nTraining mode is OFF. Only the secure API surface is active.\n")

    print("Database initialized successfully.")
