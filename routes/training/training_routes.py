"""
routes/training/training_routes.py
--------------------------------------
============================================================================
  TRAINING MODE - INTENTIONALLY VULNERABLE ROUTES - LOCAL LAB USE ONLY
============================================================================

Every route in this file is a DELIBERATELY WEAKENED variant of a route that
already exists, correctly, elsewhere in the app. They exist ONLY so you can
practice discovering real-world API vulnerability patterns against a safe,
local, fictional-data target.

Rules enforced around this blueprint (see app.py and config.py):
  * This blueprint is only registered at all when config.TRAINING_MODE is
    True, which itself requires three independent conditions to hold
    (see config.py's safety interlock) - it cannot be enabled by accident.
  * Every route below is prefixed with /api/training/... so it is clearly
    separated from the real, secure API surface at /api/...
  * A response header + a boot-time console banner both make it obvious
    when training mode is active (see app.py).
  * Which specific scenarios are "live" in a given run is controlled by
    scenario_manager.py and is randomized/config-driven by design - this
    file does not hardcode which vulnerabilities are "on".

Do not point this blueprint at anything other than the local SQLite
database seeded by database/seed.py. Do not deploy this file, or a server
with TRAINING_MODE enabled, anywhere other than your own local machine.

For the explanation of each scenario and its secure fix, see the
developer-only doc: docs/developer-remediation-guide.md (read AFTER you've
done your own manual testing).
"""

import jwt
from flask import Blueprint, request, jsonify, g

from config import config
from database.db import db
from models.user import User
from models.order import Order
from utils.auth import decode_token
from routes.training.scenario_manager import is_scenario_active

training_bp = Blueprint("training", __name__, url_prefix="/api/training")


def _lenient_current_user():
    """Used only by the WEAK_JWT_VALIDATION scenario. When that scenario is
    inactive, this behaves the same as the secure decode_token()."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()

    if is_scenario_active("WEAK_JWT_VALIDATION"):
        # VULNERABLE: signature verification disabled. Never do this outside
        # a controlled local lab - it is only present to let you practice
        # noticing / exploiting broken JWT validation.
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
        except jwt.InvalidTokenError:
            return None
    else:
        try:
            payload = decode_token(token)
        except jwt.InvalidTokenError:
            return None

    return User.query.get(payload.get("sub"))


@training_bp.route("/orders/<order_id>", methods=["GET"])
def training_get_order(order_id):
    """Mirrors GET /api/orders/<id>. May or may not enforce ownership,
    depending on whether IDOR_ORDER is active this run."""
    user = _lenient_current_user()
    if not user:
        return jsonify({"status": 401, "message": "Authentication token is missing or invalid.", "data": None}), 401

    try:
        oid = int(order_id)
    except ValueError:
        return jsonify({"status": 400, "message": "Invalid order id.", "data": None}), 400

    order = Order.query.get(oid)
    if not order:
        return jsonify({"status": 404, "message": "Order not found.", "data": None}), 404

    if is_scenario_active("IDOR_ORDER"):
        # VULNERABLE: no ownership check - any authenticated user can read
        # any order by guessing/incrementing the id.
        return jsonify({"status": 200, "message": "Order retrieved.", "data": order.to_dict()}), 200

    if order.user_id != user.id:
        return jsonify({"status": 404, "message": "Order not found.", "data": None}), 404
    return jsonify({"status": 200, "message": "Order retrieved.", "data": order.to_dict()}), 200


@training_bp.route("/admin/users", methods=["GET"])
def training_admin_users():
    """Mirrors GET /api/admin/users. May or may not enforce the admin role,
    depending on whether MISSING_ADMIN_CHECK is active this run."""
    user = _lenient_current_user()
    if not user:
        return jsonify({"status": 401, "message": "Authentication token is missing or invalid.", "data": None}), 401

    if not is_scenario_active("MISSING_ADMIN_CHECK"):
        if user.role != "admin":
            return jsonify({"status": 403, "message": "Administrator privileges are required.", "data": None}), 403

    users = User.query.all()
    if is_scenario_active("EXCESSIVE_DATA_EXPOSURE"):
        data = [u.to_admin_dict() for u in users]
    else:
        data = [u.to_public_dict() for u in users]
    return jsonify({"status": 200, "message": "Users retrieved.", "data": data}), 200


@training_bp.route("/profile", methods=["GET"])
def training_profile():
    """Mirrors GET /api/profile. May leak extra fields depending on
    whether EXCESSIVE_DATA_EXPOSURE is active this run."""
    user = _lenient_current_user()
    if not user:
        return jsonify({"status": 401, "message": "Authentication token is missing or invalid.", "data": None}), 401

    if is_scenario_active("EXCESSIVE_DATA_EXPOSURE"):
        # VULNERABLE: returns internal fields (phone/address/password_hash
        # metadata) that a profile endpoint has no reason to expose.
        data = user.to_admin_dict()
        data["password_hash"] = user.password_hash
    else:
        data = user.to_public_dict()

    return jsonify({"status": 200, "message": "Profile retrieved.", "data": data}), 200


@training_bp.route("/login", methods=["POST"])
def training_login():
    """Mirrors POST /api/login. May skip rate limiting depending on
    whether NO_LOGIN_RATE_LIMIT is active this run."""
    from utils.security import is_rate_limited, rate_limit_response

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not is_scenario_active("NO_LOGIN_RATE_LIMIT"):
        key = f"training_login:{request.remote_addr}:{email}"
        if is_rate_limited(key):
            return rate_limit_response()

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        if is_scenario_active("VERBOSE_ERROR_MESSAGES"):
            # VULNERABLE: distinct message reveals whether the email exists.
            if not user:
                return jsonify({"status": 401, "message": "No account exists with that email.", "data": None}), 401
            return jsonify({"status": 401, "message": "Incorrect password for that account.", "data": None}), 401
        return jsonify({"status": 401, "message": "Invalid email or password.", "data": None}), 401

    from utils.auth import generate_token
    token = generate_token(user)
    return jsonify({"status": 200, "message": "Login successful.", "data": {"token": token}}), 200


@training_bp.route("/products", methods=["GET", "POST", "PUT", "DELETE"])
def training_products():
    """Mirrors GET /api/products. May accept unsafe HTTP methods without
    authorization depending on whether INSECURE_HTTP_METHODS is active."""
    from models.product import Product

    if request.method == "GET":
        return jsonify({
            "status": 200,
            "message": "Products retrieved.",
            "data": [p.to_dict() for p in Product.query.all()],
        }), 200

    if is_scenario_active("INSECURE_HTTP_METHODS"):
        # VULNERABLE: state-changing verbs accepted here with no auth check
        # at all, on a route that looks read-only from the outside.
        if request.method == "DELETE":
            Product.query.delete()
            db.session.commit()
            return jsonify({"status": 200, "message": "All products deleted.", "data": None}), 200
        return jsonify({"status": 200, "message": f"{request.method} accepted (no-op in this lab).", "data": None}), 200

    return jsonify({"status": 405, "message": "Method not allowed.", "data": None}), 405


@training_bp.route("/products/<product_id>", methods=["GET"])
def training_product_detail(product_id):
    """Mirrors GET /api/products/<id>. May return raw internal error detail
    depending on whether VERBOSE_ERROR_MESSAGES / WEAK_INPUT_VALIDATION
    are active this run."""
    from models.product import Product

    if is_scenario_active("WEAK_INPUT_VALIDATION"):
        # VULNERABLE: no type/length checking before hitting the database.
        try:
            product = Product.query.get(product_id)
        except Exception as exc:  # noqa: BLE001 - intentionally broad, for the lab only
            if is_scenario_active("VERBOSE_ERROR_MESSAGES"):
                return jsonify({"status": 500, "message": f"Internal error: {exc}", "data": None}), 500
            return jsonify({"status": 400, "message": "Invalid request.", "data": None}), 400
    else:
        try:
            pid = int(product_id)
        except ValueError:
            return jsonify({"status": 400, "message": "Invalid product id.", "data": None}), 400
        product = Product.query.get(pid)

    if not product:
        return jsonify({"status": 404, "message": "Product not found.", "data": None}), 404

    data = product.to_dict()
    if is_scenario_active("PREDICTABLE_IDS"):
        # VULNERABLE (illustrative only): highlights that this app's ids are
        # sequential integers - fine for a learning exercise, worth flagging
        # in a real system that has any confidentiality requirement on ids.
        data["_note"] = "Object ids in this API are sequential integers."

    return jsonify({"status": 200, "message": "Product retrieved.", "data": data}), 200
