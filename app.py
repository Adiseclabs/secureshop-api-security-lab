"""
app.py
-------
SecureShop API - application factory and entry point.

Run with:  python app.py
"""

import os
from flask import Flask, jsonify

from config import config
from database.db import db

from routes.health_routes import health_bp
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.product_routes import product_bp
from routes.order_routes import order_bp
from routes.admin_routes import admin_bp

from utils.security import apply_security_headers, error_response


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)

    # --- Register the SECURE, always-on blueprints ---
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp)

    # --- Conditionally register the TRAINING (intentionally vulnerable)
    #     blueprint. See config.py for the full safety interlock. ---
    if config.TRAINING_MODE:
        from routes.training.training_routes import training_bp
        app.register_blueprint(training_bp)

        print("=" * 78)
        print(" WARNING: TRAINING_MODE IS ENABLED")
        print(" This build exposes intentionally vulnerable routes under /api/training/*")
        print(" Use for local, authorized security practice ONLY.")
        print(" Never expose this server to the internet or any shared network.")
        print("=" * 78)

    @app.after_request
    def _security_headers(response):
        response = apply_security_headers(response)
        if config.TRAINING_MODE:
            # Makes it unmistakable, in every single response, that this is
            # not a production-safe build - visible in Burp/Postman too.
            response.headers["X-Training-Mode"] = "enabled"
        return response

    # --- Generic, safe error handlers (never leak stack traces) ---
    @app.errorhandler(404)
    def not_found(_e):
        return error_response(404, "The requested resource was not found.")

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return error_response(405, "This HTTP method is not allowed for this endpoint.")

    @app.errorhandler(500)
    def internal_error(_e):
        db.session.rollback()
        return error_response(500, "An internal error occurred. Please try again later.")

    return app


app = create_app()

if __name__ == "__main__":
    # debug=config.DEBUG is intentional: it is one of the three independent
    # conditions the training-mode interlock checks in config.py.
    app.run(host="127.0.0.1", port=config.PORT, debug=config.DEBUG)
