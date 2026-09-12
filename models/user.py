"""
models/user.py
---------------
User model.

Security notes:
  * Passwords are never stored in plaintext - only a salted hash
    (Werkzeug's PBKDF2-SHA256 via generate_password_hash).
  * `role` is restricted to "user" or "admin" at the application layer
    (see utils/validators.py) - never trust a role value coming from
    client input.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # "user" | "admin"
    # Extra profile fields - used to demonstrate "excessive data exposure"
    # findings in training mode if that scenario is enabled.
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def to_public_dict(self) -> dict:
        """Minimal, safe representation - used by SECURE routes."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
        }

    def to_admin_dict(self) -> dict:
        """Fuller representation - only ever returned to an authenticated admin."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "phone": self.phone,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
