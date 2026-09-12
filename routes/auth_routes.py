"""
routes/auth_routes.py
-----------------------
Registration and login. This is the security-critical entry point of the
whole app, so every control listed in docs/secure-controls.md around
authentication and rate limiting is anchored here.
"""

from flask import Blueprint, request, jsonify

from database.db import db
from models.user import User
from utils.validators import is_valid_email, is_valid_password, is_valid_name
from utils.auth import generate_token
from utils.security import is_rate_limited, rate_limit_response, audit_log, error_response

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not is_valid_name(name):
        return error_response(400, "A valid name is required.")
    if not is_valid_email(email):
        return error_response(400, "A valid email address is required.")
    ok, reason = is_valid_password(password)
    if not ok:
        return error_response(400, reason)

    # Role is ALWAYS forced to "user" here - client input can never grant
    # admin at registration time (prevents privilege-escalation via signup).
    if User.query.filter_by(email=email).first():
        # Same generic message as any other failure to avoid confirming
        # which emails are registered (user-enumeration hardening).
        return error_response(400, "Registration could not be completed with the provided details.")

    user = User(name=name, email=email, role="user")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    audit_log("user_registered", user_id=user.id, email=email)

    return jsonify({
        "status": 201,
        "message": "Registration successful.",
        "data": user.to_public_dict(),
    }), 201


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    rate_key = f"login:{request.remote_addr}:{email}"
    if is_rate_limited(rate_key):
        audit_log("login_rate_limited", email=email)
        return rate_limit_response()

    if not email or not password:
        return error_response(400, "Email and password are required.")

    user = User.query.filter_by(email=email).first()

    # Same generic error whether the email doesn't exist or the password is
    # wrong - prevents user enumeration via distinct error messages.
    if not user or not user.check_password(password):
        audit_log("login_failed", email=email)
        return error_response(401, "Invalid email or password.")

    token = generate_token(user)
    audit_log("login_success", user_id=user.id, email=email)

    return jsonify({
        "status": 200,
        "message": "Login successful.",
        "data": {
            "token": token,
            "user": user.to_public_dict(),
        },
    }), 200
