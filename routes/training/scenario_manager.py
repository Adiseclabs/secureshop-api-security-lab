"""
routes/training/scenario_manager.py
--------------------------------------
Decides WHICH intentionally-vulnerable scenarios are active for this run,
and persists that choice so it survives a server restart (but not a
`scripts/reset_database.py` run, which starts fresh).

This file is the ONLY place that knows the full scenario list. It is never
imported by, or exposed through, any normal-mode route. The active list is
written to a gitignored JSON file, not the README, and is not reachable
through any API endpoint.

See docs/developer-remediation-guide.md (read AFTER testing) for what each
code means and how to fix it.
"""

import json
import os
import random

from config import config

ALL_SCENARIOS = [
    "IDOR_ORDER",           # BOLA on GET /api/training/orders/<id>
    "MISSING_ADMIN_CHECK",  # admin route reachable without role check
    "EXCESSIVE_DATA_EXPOSURE",  # profile endpoint leaks extra fields
    "WEAK_JWT_VALIDATION",  # accepts alg=none / unverified tokens
    "NO_LOGIN_RATE_LIMIT",  # login endpoint has no throttling
    "WEAK_INPUT_VALIDATION",  # accepts malformed/oversized input
    "INSECURE_HTTP_METHODS",  # unsafe verb accepted where it shouldn't be
    "VERBOSE_ERROR_MESSAGES",  # stack trace / internal detail leakage
    "MISSING_SECURITY_HEADERS",  # headers stripped on this blueprint
    "PREDICTABLE_IDS",      # sequential/guessable identifiers exposed
]


def _load_state():
    if os.path.exists(config.TRAINING_STATE_FILE):
        try:
            with open(config.TRAINING_STATE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _save_state(active):
    os.makedirs(os.path.dirname(config.TRAINING_STATE_FILE), exist_ok=True)
    with open(config.TRAINING_STATE_FILE, "w") as f:
        json.dump({"active": active}, f)


def get_active_scenarios(force_reroll: bool = False) -> list:
    """Return the list of active scenario codes for this run.

    Order of precedence:
      1. If TRAINING_SCENARIOS env var is set, use exactly that list (a
         reproducible/pinned build for repeat practice).
      2. Else, reuse a previously-persisted random selection, unless
         force_reroll is True (used by init_database.py on a fresh build).
      3. Else, choose a random subset (40-70% of the catalog) and persist it.
    """
    if config.TRAINING_SCENARIOS_RAW:
        pinned = [s.strip() for s in config.TRAINING_SCENARIOS_RAW.split(",") if s.strip()]
        pinned = [s for s in pinned if s in ALL_SCENARIOS]
        _save_state(pinned)
        return pinned

    if not force_reroll:
        state = _load_state()
        if state and isinstance(state.get("active"), list):
            return state["active"]

    k = random.randint(max(1, int(len(ALL_SCENARIOS) * 0.4)), int(len(ALL_SCENARIOS) * 0.7))
    active = random.sample(ALL_SCENARIOS, k)
    _save_state(active)
    return active


def is_scenario_active(code: str) -> bool:
    if not config.TRAINING_MODE:
        return False
    return code in get_active_scenarios()
