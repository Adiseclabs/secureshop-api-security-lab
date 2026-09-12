"""
utils/security.py
--------------------
Cross-cutting security controls that aren't specific to one route file:
  * Security response headers
  * In-memory rate limiting (fine for a single-process local lab)
  * Audit logging
  * Safe error responses (never leak stack traces/internal details)
"""

import json
import time
import logging
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock

from flask import request, jsonify

from config import config

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

def apply_security_headers(response):
    """Attach standard hardening headers to every response.

    Threats addressed: clickjacking, MIME-sniffing, referrer leakage,
    and (for the local demo) a conservative Content-Security-Policy.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # Not meaningful over plain local HTTP, but included so the header is
    # present when you later test this over HTTPS/behind a reverse proxy.
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    # Avoid caching sensitive API responses in intermediary caches/browsers.
    response.headers["Cache-Control"] = "no-store"
    return response


# ---------------------------------------------------------------------------
# Rate limiting (simple fixed-window, in-memory - fine for a local single
# worker process; would need a shared store like Redis for multi-worker use)
# ---------------------------------------------------------------------------

_attempts = defaultdict(list)
_lock = Lock()


def is_rate_limited(key: str) -> bool:
    """Threat addressed: credential stuffing / brute-force login attempts."""
    now = time.time()
    window = config.RATE_LIMIT_WINDOW_SECONDS
    max_attempts = config.RATE_LIMIT_MAX_ATTEMPTS

    with _lock:
        recent = [t for t in _attempts[key] if now - t < window]
        _attempts[key] = recent
        if len(recent) >= max_attempts:
            return True
        _attempts[key].append(now)
        return False


def rate_limit_response():
    return jsonify({
        "status": 429,
        "message": "Too many attempts. Please wait before trying again.",
        "data": None,
    }), 429


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

_logger = logging.getLogger("secureshop.audit")
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    handler = logging.FileHandler(config.AUDIT_LOG_PATH)
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)


def audit_log(event: str, **details):
    """Structured, append-only audit trail for security-relevant events
    (logins, failed logins, admin actions, registration). Never logs
    passwords or raw tokens - only identifiers and outcomes."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "ip": request.remote_addr if request else None,
        **details,
    }
    _logger.info(json.dumps(entry))


# ---------------------------------------------------------------------------
# Safe error responses
# ---------------------------------------------------------------------------

def error_response(status_code: int, message: str):
    """Generic error envelope. Never includes exception text, stack traces,
    SQL, or file paths - only a safe, fixed message."""
    return jsonify({"status": status_code, "message": message, "data": None}), status_code
