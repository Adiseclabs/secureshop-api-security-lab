"""
database/db.py
---------------
SQLAlchemy database instance, shared across the whole app.
Kept in its own module (rather than app.py) to avoid circular imports
between models and routes.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
