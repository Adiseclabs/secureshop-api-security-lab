"""
utils/auth.py
--------------
JWT creation/validation and auth decorators.

Security controls implemented here:
  * JWT signing with a server-side secret (HS256).
  * Expiration ("exp") claim enforced on every token.
  * Signature + expiry verification on every protected request
    (jwt.decode with verify_signature/verify_exp implicitly enabled).
  * Role-based access control decorator (`admin_required`).
  * Object-level helper (`current_user_id`) so routes can check that the
    resource being accessed belongs to the caller (prevents IDOR/BOLA).
"""

from functools import wraps
from datetime import datetime, timedelta, timezone

import jwt
from flask import request, jsonify, g

from config import config
from models.user import User


def generate_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=config.JWT_EXP_MINUTES),
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Raises jwt.InvalidTokenError (or a subclass) on any problem:
    bad signature, expired token, malformed token, etc.
    Signature and expiration verification are ON by default in PyJWT
    unless explicitly disabled - we never disable them here.
    """
    return jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])


def _extract_token_from_header() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def token_required(f):
    """Require a valid, non-expired JWT. Populates g.current_user."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token_from_header()
        if not token:
            return jsonify({
                "status": 401,
                "message": "Authentication token is missing.",
                "data": None,
            }), 401

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"status": 401, "message": "Token has expired.", "data": None}), 401
        except jwt.InvalidTokenError:
            return jsonify({"status": 401, "message": "Token is invalid.", "data": None}), 401

        user = User.query.get(payload.get("sub"))
        if not user:
            return jsonify({"status": 401, "message": "User no longer exists.", "data": None}), 401

        g.current_user = user
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Require a valid JWT AND role == 'admin'.

    Implemented as a single self-contained decorator (rather than stacking
    two decorators) so the auth check and the role check cannot accidentally
    be applied out of order.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token_from_header()
        if not token:
            return jsonify({"status": 401, "message": "Authentication token is missing.", "data": None}), 401

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"status": 401, "message": "Token has expired.", "data": None}), 401
        except jwt.InvalidTokenError:
            return jsonify({"status": 401, "message": "Token is invalid.", "data": None}), 401

        user = User.query.get(payload.get("sub"))
        if not user:
            return jsonify({"status": 401, "message": "User no longer exists.", "data": None}), 401

        # Role-based access control: the role is re-checked against the
        # database record, not just trusted from the JWT claim, so a role
        # change takes effect immediately rather than waiting for token expiry.
        if user.role != "admin":
            return jsonify({
                "status": 403,
                "message": "Administrator privileges are required for this action.",
                "data": None,
            }), 403

        g.current_user = user
        return f(*args, **kwargs)

    return decorated


def current_user_id() -> int:
    return g.current_user.id
