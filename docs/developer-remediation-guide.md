# SecureShop - Developer Remediation Guide

> **READ AFTER MANUAL TESTING.**
> This document explains every intentionally vulnerable Training Mode
> scenario, why it's vulnerable, its impact, how to reproduce it locally,
> and the secure replacement code. Reading it before you finish your own
> testing will spoil the exercise.

All scenarios live in `routes/training/training_routes.py` and are gated
by `routes/training/scenario_manager.py`. Which ones are "live" in your
current build is randomized (or pinned via `TRAINING_SCENARIOS` in `.env`).
Check `config/.training_state.json` (gitignored) if you want to see your
current build's active list directly instead of inferring it from testing.

---

### IDOR_ORDER - Broken Object-Level Authorization on orders
- **Vulnerable route**: `GET /api/training/orders/<id>`
- **Why vulnerable**: The handler fetches the order by id and returns it
  without checking `order.user_id == current_user.id`.
- **Impact**: Any authenticated user can read any other user's order
  (amounts, product, status) by enumerating ids.
- **Reproduce**: Log in as User A, note an order id belonging to User B,
  call the training endpoint with User A's token.
- **Secure code**: see `routes/order_routes.py::get_order` - the same
  route pattern, but with `if not order or order.user_id != g.current_user.id: return 404`.
- **Recommended controls**: object-level authorization on every read/write,
  return `404` (not `403`) for resources that exist but aren't owned by the
  caller, to avoid confirming existence.
- **Retest**: repeat the reproduction steps and confirm a `404`.

### MISSING_ADMIN_CHECK - Missing role validation on an admin endpoint
- **Vulnerable route**: `GET /api/training/admin/users`
- **Why vulnerable**: The role check (`if user.role != "admin"`) is
  skipped when this scenario is active.
- **Impact**: Any authenticated normal user can list all users.
- **Reproduce**: Log in as a normal user, call the training endpoint.
- **Secure code**: see `routes/admin_routes.py::list_users`, protected by
  the `@admin_required` decorator in `utils/auth.py`, which re-checks the
  role against the database on every request.
- **Recommended controls**: centralize RBAC in a decorator/middleware
  applied consistently; never gate admin routes with a client-controlled
  flag or an easily-forgotten inline check.
- **Retest**: confirm `403` for non-admins.

### EXCESSIVE_DATA_EXPOSURE - Over-sharing in profile/user responses
- **Vulnerable routes**: `GET /api/training/profile`,
  `GET /api/training/admin/users` (when combined with this scenario)
- **Why vulnerable**: Returns `to_admin_dict()` (and even the raw
  `password_hash`) from a route a normal user can call about themselves.
- **Impact**: Leaks phone/address/hash data that has no business being in
  a basic profile response.
- **Reproduce**: Call the training profile endpoint and diff the JSON
  against `GET /api/profile`.
- **Secure code**: see `models/user.py::to_public_dict` - a minimal,
  purpose-built serializer used by the secure `/api/profile` route.
- **Recommended controls**: define per-endpoint response schemas
  (allow-list fields, don't just omit sensitive ones ad hoc); never
  serialize the raw ORM object or include hash/secret fields in any
  API response.
- **Retest**: confirm only `id/name/email/role` are returned.

### WEAK_JWT_VALIDATION - Signature verification disabled
- **Vulnerable route**: any `/api/training/*` route (uses `_lenient_current_user`)
- **Why vulnerable**: Calls `jwt.decode(token, options={"verify_signature": False})`,
  so a token with ANY signature (or none) is accepted as long as it's
  well-formed base64 JSON.
- **Impact**: An attacker can forge a token claiming any `sub`/user id
  without knowing the server's secret.
- **Reproduce**: Craft a JWT with `alg: none` or a bogus signature, set
  `sub` to another user's id, and call a training route with it.
- **Secure code**: see `utils/auth.py::decode_token` - signature and
  expiration are always verified, and the algorithm is pinned
  (`algorithms=[config.JWT_ALGORITHM]`) so an attacker cannot force `alg: none`.
- **Recommended controls**: always verify signature and expiry; pin the
  expected algorithm explicitly; never trust an unverified claim.
- **Retest**: confirm forged tokens are rejected with `401`.

### NO_LOGIN_RATE_LIMIT - Missing throttling on login
- **Vulnerable route**: `POST /api/training/login`
- **Why vulnerable**: Skips the `is_rate_limited` check entirely.
- **Impact**: Enables unthrottled password-guessing/credential-stuffing.
- **Reproduce**: Send many rapid failed login attempts; note no `429` ever
  appears.
- **Secure code**: see `routes/auth_routes.py::login`, which calls
  `utils/security.py::is_rate_limited` keyed by IP+email before checking
  credentials.
- **Recommended controls**: rate limit by IP and by account; add
  exponential backoff or CAPTCHA after repeated failures; alert on spikes
  via the audit log.
- **Retest**: confirm `429` appears after the configured attempt threshold.

### WEAK_INPUT_VALIDATION - Missing type/length checks
- **Vulnerable route**: `GET /api/training/products/<product_id>`
- **Why vulnerable**: Passes `product_id` straight to `Product.query.get()`
  without validating it's a positive integer first.
- **Impact**: Unexpected types can trigger internal errors (and, combined
  with `VERBOSE_ERROR_MESSAGES`, leak internal detail).
- **Reproduce**: Request `/api/training/products/abc` or an extremely long
  string.
- **Secure code**: see `routes/product_routes.py::get_product`, which uses
  `utils/validators.py::is_positive_int` before querying.
- **Recommended controls**: validate and coerce all path/query/body input
  before it reaches the database or business logic.
- **Retest**: confirm a clean `400` for invalid ids.

### INSECURE_HTTP_METHODS - Unsafe verbs accepted without authorization
- **Vulnerable route**: `/api/training/products` (`POST`/`PUT`/`DELETE`)
- **Why vulnerable**: The route accepts state-changing verbs with no
  authentication or role check at all - `DELETE` even wipes the product
  table.
- **Impact**: Any unauthenticated caller can delete or "modify" data.
- **Reproduce**: `DELETE /api/training/products` with no auth header.
- **Secure code**: see `routes/product_routes.py` (GET-only, public) and
  `routes/admin_routes.py::create_product` (POST, `@admin_required`) -
  the secure API never combines an unauthenticated route with a
  state-changing verb.
- **Recommended controls**: explicitly declare allowed methods per route;
  require authentication + authorization for anything that mutates state;
  rely on Flask's automatic `405` for undeclared methods.
- **Retest**: confirm mutating verbs require admin auth (or are rejected).

### VERBOSE_ERROR_MESSAGES - Information disclosure via error messages
- **Vulnerable routes**: `POST /api/training/login` (user-enumeration via
  distinct messages), `GET /api/training/products/<id>` (raw exception
  text in the `500` body)
- **Why vulnerable**: Returns different messages for "no such user" vs.
  "wrong password", and/or includes `str(exc)` directly in the response.
- **Impact**: Enables user enumeration and leaks internal implementation
  detail useful for further attacks.
- **Reproduce**: Compare login error text for a real vs. fake email;
  trigger the malformed-id error path on the training product route.
- **Secure code**: see `utils/security.py::error_response` - always a
  fixed, generic message; `routes/auth_routes.py::login` uses the same
  message for both failure cases.
- **Recommended controls**: log full detail server-side only; return
  generic client-facing messages; centralize error formatting.
- **Retest**: confirm identical error text regardless of failure reason.

### MISSING_SECURITY_HEADERS - Headers stripped
- **Where it shows up**: compare headers on `/api/training/*` responses
  vs. `/api/*` responses (the `after_request` hook in `app.py` still
  applies globally in this lab build for safety, but treat this scenario
  as a placeholder for "some deployments forget to apply hardening
  headers on every blueprint" - a very common real-world finding).
- **Impact**: Increases exposure to clickjacking, MIME-sniffing, and
  related client-side attacks.
- **Secure code**: see `utils/security.py::apply_security_headers` and its
  registration in `app.py`'s `after_request`.
- **Recommended controls**: apply hardening headers globally via a single
  middleware/hook, not per-blueprint, so new routes can't accidentally
  skip them.
- **Retest**: confirm headers are present on every route, old and new.

### PREDICTABLE_IDS - Sequential/guessable identifiers
- **Where it shows up**: `GET /api/training/products/<id>` includes a note
  when this scenario is active; more generally, all ids in this lab
  (including the secure routes) are sequential integers for simplicity.
- **Impact**: Sequential ids make enumeration attacks (like IDOR above)
  trivial to carry out at scale.
- **Reproduce**: Note that valid product/order/user ids increase by 1.
- **Recommended controls**: use UUIDs (or another non-sequential
  identifier) for anything referenced externally, especially combined
  with strong object-level authorization as the primary control.
- **Retest**: N/A for this lab (would require a schema migration) - treat
  this as a design-improvement note rather than a fix you apply here.

---

## General Recommendations Recap

1. Authorization checks belong on every single request, never inferred
   from a token claim alone or "the UI wouldn't let you do that."
2. Validate input at the boundary, before it reaches business logic.
3. Never let error handling leak more than a fixed, generic message.
4. Rate-limit anything that can be brute-forced.
5. Keep response payload shapes minimal and purpose-built per endpoint.
6. Apply cross-cutting controls (headers, logging) globally, not per-route.
