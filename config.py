"""
config.py
---------
Central configuration for the SecureShop training lab.

Design goals:
  * Everything sensitive comes from environment variables (never hardcoded).
  * TRAINING_MODE requires an EXPLICIT, exact "true" string. Any typo,
    unset variable, or non-development context defaults to OFF.
  * A hard safety interlock prevents training mode from turning on if the
    app looks like it might be running in a production-like context.
"""

import os
import secrets
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core Flask config ---
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    PORT = int(os.getenv("PORT", "5000"))

    # --- Database ---
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database/secureshop.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, DATABASE_PATH)}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- JWT ---
    # If no secret is provided, generate an ephemeral one so the app never
    # silently runs with a known/default secret. This means tokens will not
    # survive a restart unless you set JWT_SECRET_KEY yourself - that's
    # intentional for a security lab (forces you to set it explicitly).
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_hex(32)
    JWT_ALGORITHM = "HS256"
    JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))

    # --- Rate limiting ---
    RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv("RATE_LIMIT_MAX_ATTEMPTS", "5"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # ------------------------------------------------------------------
    # TRAINING MODE SAFETY INTERLOCK
    #
    # Rules (all must hold, or training mode is forced OFF):
    #   1. TRAINING_MODE env var must be the exact string "true".
    #   2. FLASK_ENV must not be "production".
    #   3. DEBUG must be enabled (production deployments normally disable
    #      debug, so this acts as a second independent check).
    #
    # This means someone would have to deliberately misconfigure THREE
    # separate settings to turn training mode on outside local development.
    # ------------------------------------------------------------------
    _requested_training_mode = os.getenv("TRAINING_MODE", "false").strip().lower() == "true"
    _env_allows_training = FLASK_ENV != "production"
    _debug_allows_training = DEBUG

    TRAINING_MODE = _requested_training_mode and _env_allows_training and _debug_allows_training

    # Optional pinned scenario list (comma-separated codes), else random.
    TRAINING_SCENARIOS_RAW = os.getenv("TRAINING_SCENARIOS", "").strip()

    # Where the (gitignored) record of which scenarios are active is kept.
    TRAINING_STATE_FILE = os.path.join(BASE_DIR, "config", ".training_state.json")

    # --- Audit logging ---
    AUDIT_LOG_PATH = os.path.join(BASE_DIR, "reports", "audit.log")


config = Config()
