# SecureShop - Secure Controls Reference

For each control: the threat it addresses, where it lives in the code, how
to verify it manually, the expected secure behavior, and how it could be
improved further in a production system.

---

## 1. Authentication

- **Threat**: Unauthenticated access to user/account data.
- **Where**: `utils/auth.py` (`token_required`), `routes/auth_routes.py`.
- **Verify**: Call `/api/profile` with no `Authorization` header -> expect `401`.
- **Expected behavior**: Every non-public route requires a valid `Bearer` JWT.
- **Improve**: Add refresh tokens, token revocation/blacklisting, MFA.

## 2. Object-Level Authorization (Anti-IDOR/BOLA)

- **Threat**: One user reading/modifying another user's resources by
  changing an id in the URL/body.
- **Where**: `routes/order_routes.py` - every query is filtered by
  `user_id == g.current_user.id`.
- **Verify**: As User A, request an order id known to belong to User B via
  `GET /api/orders/<id>` -> expect `404`, not the order data.
- **Expected behavior**: Ownership is checked server-side on every request,
  never inferred from client input.
- **Improve**: Use non-sequential (UUID) identifiers as defense in depth.

## 3. Role-Based Access Control (RBAC)

- **Threat**: A normal user reaching admin-only functionality.
- **Where**: `utils/auth.py` (`admin_required`), applied to every route in
  `routes/admin_routes.py`.
- **Verify**: Log in as a normal user, call `GET /api/admin/dashboard` ->
  expect `403`.
- **Expected behavior**: Role is re-checked against the database on every
  request, not just trusted from the JWT claim.
- **Improve**: Move to a permissions/claims model if more than two roles
  are ever needed.

## 4. JWT Validation

- **Threat**: Forged, tampered, expired, or `alg=none` tokens being accepted.
- **Where**: `utils/auth.py` (`decode_token`) - signature and expiry are
  always verified; the algorithm is pinned to `HS256`.
- **Verify**: Tamper with the token's payload/signature in Burp and resend
  -> expect `401`.
- **Expected behavior**: Any modification invalidates the token.
- **Improve**: Rotate signing keys periodically; consider short-lived
  access tokens + refresh tokens; move to RS256 with key rotation for
  multi-service deployments.

## 5. Input Validation

- **Threat**: Malformed, oversized, or unexpected input causing errors or
  logic bypass.
- **Where**: `utils/validators.py`, used by every route that accepts a body.
- **Verify**: Submit an empty password, an oversized name, or a
  non-numeric `product_id` -> expect a clean `400`, never a `500`.
- **Expected behavior**: All input is validated before touching the
  database.
- **Improve**: Adopt a schema library (e.g., `pydantic` or `marshmallow`)
  for larger APIs.

## 6. Rate Limiting

- **Threat**: Brute-force / credential-stuffing attacks on login.
- **Where**: `utils/security.py` (`is_rate_limited`), applied in
  `routes/auth_routes.py`'s `/api/login`.
- **Verify**: Send 6+ rapid login attempts with a wrong password from the
  same IP -> expect `429` after the configured threshold.
- **Expected behavior**: Excess attempts are blocked for the configured
  window, per IP+email combination.
- **Improve**: Use a shared store (Redis) for multi-process deployments;
  add CAPTCHA or exponential backoff.

## 7. SQL Injection Prevention

- **Threat**: Malicious input altering database queries.
- **Where**: Every database access uses the SQLAlchemy ORM with bound
  parameters (`Model.query.filter_by(...)`, `Model.query.get(...)`) -
  there is no raw/string-concatenated SQL anywhere in the secure routes.
- **Verify**: Submit `' OR '1'='1` style payloads in the email/search
  fields -> expect normal validation errors, not a bypass.
- **Expected behavior**: Input is always treated as data, never as SQL.
- **Improve**: Add static analysis (e.g., `bandit`) to CI to catch any
  future raw-SQL regressions.

## 8. Sensitive-Data Protection

- **Threat**: Leaking passwords, tokens, or PII in responses or logs.
- **Where**: `models/user.py` (`to_public_dict` vs `to_admin_dict`);
  `utils/security.py` (`audit_log` never logs passwords/tokens).
- **Verify**: Inspect every response body for `password_hash` - it should
  never appear outside admin-only, fully-authorized responses.
- **Expected behavior**: Only the minimum necessary fields are returned
  per endpoint/role.
- **Improve**: Field-level encryption for PII at rest; log redaction
  middleware.

## 9. Secure Error Handling

- **Threat**: Stack traces / internal details helping an attacker map the
  system.
- **Where**: `app.py` error handlers (`404`, `405`, `500`) and
  `utils/security.py` (`error_response`) - always return a fixed, generic
  message.
- **Verify**: Trigger a `500` (if possible) and confirm no traceback,
  file path, or SQL appears in the response.
- **Expected behavior**: Errors are logged server-side, not exposed
  client-side.
- **Improve**: Central structured logging (e.g., to a SIEM) with alerting
  on repeated 5xx errors.

## 10. Security Headers

- **Threat**: Clickjacking, MIME-sniffing, and related browser-side attacks.
- **Where**: `utils/security.py` (`apply_security_headers`), applied to
  every response via `app.after_request` in `app.py`.
- **Verify**: Inspect response headers in Burp/Postman for
  `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`,
  etc.
- **Expected behavior**: Present on every response, including error
  responses.
- **Improve**: Tune CSP per-route if templates/HTML are added later.

## 11. Audit Logging

- **Threat**: No record of security-relevant events for detection/response.
- **Where**: `utils/security.py` (`audit_log`), called from registration,
  login (success/failure/rate-limited), order creation, and admin product
  creation. Written to `reports/audit.log`.
- **Verify**: Perform a login, then check `reports/audit.log` for a
  corresponding JSON entry (no password/token present).
- **Expected behavior**: Every authentication and privileged action is
  logged with a timestamp, event type, and actor - never with secrets.
- **Improve**: Ship logs to a centralized, tamper-evident store.

## 12. Secure Password Hashing

- **Threat**: Password database compromise leading to direct credential
  exposure.
- **Where**: `models/user.py` (`set_password`/`check_password`) uses
  Werkzeug's salted PBKDF2-SHA256 hashing.
- **Verify**: Inspect the SQLite database directly - `password_hash`
  should be a long salted hash, never plaintext.
- **Expected behavior**: Passwords are never stored or logged in plaintext.
- **Improve**: Migrate to `argon2` for new deployments.

## 13. Proper HTTP Method Handling

- **Threat**: Unexpected verbs (e.g., `DELETE`, `PUT`) being silently
  accepted on routes that shouldn't support them.
- **Where**: Flask's route `methods=[...]` declarations restrict each
  secure endpoint to only the verbs it needs; unlisted verbs return `405`
  automatically (handled by the `405` error handler in `app.py`).
- **Verify**: Send `DELETE /api/products` -> expect `405`.
- **Expected behavior**: Only explicitly allowed methods succeed.
- **Improve**: Add automated method-fuzzing to the CI test suite.
