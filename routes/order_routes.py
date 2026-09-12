"""
routes/order_routes.py
------------------------
Order creation and order history.

This is the canonical place to test for IDOR/BOLA: every query here is
scoped to g.current_user.id, both for reads and writes, so one user can
never see or act on another user's orders through the SECURE routes.
(The training-mode blueprint may expose a deliberately broken variant -
see routes/training/.)
"""

from flask import Blueprint, request, jsonify, g

from database.db import db
from models.order import Order
from models.product import Product
from utils.auth import token_required
from utils.validators import is_positive_int
from utils.security import audit_log, error_response

order_bp = Blueprint("order", __name__)


@order_bp.route("/api/orders", methods=["POST"])
@token_required
def create_order():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not is_positive_int(product_id):
        return error_response(400, "A valid product_id is required.")
    if not is_positive_int(quantity):
        return error_response(400, "Quantity must be a positive integer.")

    product = Product.query.get(int(product_id))
    if not product:
        return error_response(404, "Product not found.")

    quantity = int(quantity)
    if quantity > product.stock:
        return error_response(400, "Insufficient stock for the requested quantity.")

    order = Order(
        user_id=g.current_user.id,   # always the authenticated user - never trust a client-supplied user_id
        product_id=product.id,
        quantity=quantity,
        total_price=round(product.price * quantity, 2),
        status="placed",
    )
    product.stock -= quantity
    db.session.add(order)
    db.session.commit()

    audit_log("order_created", user_id=g.current_user.id, order_id=order.id, product_id=product.id)

    return jsonify({
        "status": 201,
        "message": "Order created successfully.",
        "data": order.to_dict(),
    }), 201


@order_bp.route("/api/orders", methods=["GET"])
@token_required
def order_history():
    orders = Order.query.filter_by(user_id=g.current_user.id).order_by(Order.created_at.desc()).all()
    return jsonify({
        "status": 200,
        "message": "Order history retrieved successfully.",
        "data": [o.to_dict() for o in orders],
    }), 200


@order_bp.route("/api/orders/<order_id>", methods=["GET"])
@token_required
def get_order(order_id):
    if not is_positive_int(order_id):
        return error_response(400, "Invalid order id.")

    order = Order.query.get(int(order_id))

    # Object-level authorization check: the order must exist AND belong to
    # the caller. Returning 404 (not 403) for someone else's order avoids
    # confirming that a given order id even exists.
    if not order or order.user_id != g.current_user.id:
        return error_response(404, "Order not found.")

    return jsonify({
        "status": 200,
        "message": "Order retrieved successfully.",
        "data": order.to_dict(),
    }), 200
