"""
routes/health_routes.py
--------------------------
Simple liveness endpoint. Deliberately returns the minimum possible
information (no version numbers, no stack, no environment details) -
avoids giving an attacker free reconnaissance data.
"""

from flask import Blueprint, jsonify
from config import config

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": 200,
        "message": "SecureShop API is running.",
        "data": {
            "training_mode": config.TRAINING_MODE,  # visible so you always know the app's current mode
        },
    }), 200
