"""
routes/user_routes.py
-----------------------
User profile endpoint. Demonstrates object-level authorization: a user can
only ever retrieve THEIR OWN profile - g.current_user comes from the
verified JWT, never from a client-supplied id.
"""

from flask import Blueprint, jsonify, g

from utils.auth import token_required

user_bp = Blueprint("user", __name__)


@user_bp.route("/api/profile", methods=["GET"])
@token_required
def profile():
    # Note: we intentionally return the PUBLIC dict, not the admin dict,
    # to avoid exposing phone/address to the profile endpoint itself.
    return jsonify({
        "status": 200,
        "message": "Profile retrieved successfully.",
        "data": g.current_user.to_public_dict(),
    }), 200
