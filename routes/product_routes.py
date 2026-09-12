"""
routes/product_routes.py
--------------------------
Public product catalog. Read-only for normal users; creation is admin-only
and lives in admin_routes.py.
"""

from flask import Blueprint, jsonify

from models.product import Product
from utils.validators import is_positive_int
from utils.security import error_response

product_bp = Blueprint("product", __name__)


@product_bp.route("/api/products", methods=["GET"])
def list_products():
    products = Product.query.all()
    return jsonify({
        "status": 200,
        "message": "Products retrieved successfully.",
        "data": [p.to_dict() for p in products],
    }), 200


@product_bp.route("/api/products/<product_id>", methods=["GET"])
def get_product(product_id):
    if not is_positive_int(product_id):
        return error_response(400, "Invalid product id.")

    product = Product.query.get(int(product_id))
    if not product:
        return error_response(404, "Product not found.")

    return jsonify({
        "status": 200,
        "message": "Product retrieved successfully.",
        "data": product.to_dict(),
    }), 200
