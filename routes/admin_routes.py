"""
routes/admin_routes.py
------------------------
Administrative endpoints. Every route here uses @admin_required, which
independently re-verifies the JWT AND checks the role against the
database (not just the token claim) on every single request.
"""

from flask import Blueprint, request, jsonify

from database.db import db
from models.user import User
from models.product import Product
from models.order import Order
from utils.auth import admin_required
from utils.validators import is_valid_name, sanitize_string
from utils.security import audit_log, error_response

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/api/admin/dashboard", methods=["GET"])
@admin_required
def dashboard():
    return jsonify({
        "status": 200,
        "message": "Admin dashboard retrieved successfully.",
        "data": {
            "total_users": User.query.count(),
            "total_products": Product.query.count(),
            "total_orders": Order.query.count(),
        },
    }), 200


@admin_bp.route("/api/admin/users", methods=["GET"])
@admin_required
def list_users():
    users = User.query.all()
    return jsonify({
        "status": 200,
        "message": "Users retrieved successfully.",
        "data": [u.to_admin_dict() for u in users],
    }), 200


@admin_bp.route("/api/admin/products", methods=["POST"])
@admin_required
def create_product():
    data = request.get_json(silent=True) or {}
    name = sanitize_string(data.get("name"), 150)
    description = sanitize_string(data.get("description"), 500)
    sku = sanitize_string(data.get("sku"), 50)

    try:
        price = float(data.get("price"))
        stock = int(data.get("stock", 0))
    except (TypeError, ValueError):
        return error_response(400, "Price and stock must be valid numbers.")

    if not is_valid_name(name):
        return error_response(400, "A valid product name is required.")
    if price <= 0:
        return error_response(400, "Price must be greater than zero.")
    if stock < 0:
        return error_response(400, "Stock cannot be negative.")
    if not sku:
        return error_response(400, "SKU is required.")
    if Product.query.filter_by(sku=sku).first():
        return error_response(400, "A product with this SKU already exists.")

    product = Product(name=name, description=description, price=price, stock=stock, sku=sku)
    db.session.add(product)
    db.session.commit()

    audit_log("product_created", sku=sku, name=name)

    return jsonify({
        "status": 201,
        "message": "Product created successfully.",
        "data": product.to_dict(),
    }), 201
