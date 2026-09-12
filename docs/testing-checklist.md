# SecureShop - Manual Testing Checklist

Use this checklist with Burp Suite / Postman against your local instance.
This document intentionally contains **no findings or answers** - fill in
your own observations as you go. See the README for how to enable
Training Mode before you start, if you want extra practice targets.

For each test: note what you actually observed, assign a severity if you
find an issue (Critical/High/Medium/Low/Info), and jot a remediation idea
before checking the developer guide.

---

## 1. Registration Testing
- [ ] Register with valid data - confirm success and response shape.
- [ ] Register with a duplicate email - confirm generic error, not "email exists".
- [ ] Register with a weak/short password - confirm rejection.
- [ ] Register with an invalid email format - confirm rejection.
- [ ] Try to pass `"role": "admin"` in the registration body.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 2. Login Testing
- [ ] Login with correct credentials - confirm a JWT is returned.
- [ ] Login with wrong password - confirm generic error message.
- [ ] Login with non-existent email - confirm the SAME generic error message.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 3. Authentication Testing
- [ ] Call a protected route with no `Authorization` header.
- [ ] Call a protected route with a malformed/garbage token.
- [ ] Call a protected route with an expired token (wait past the expiry,
      or shorten `JWT_EXP_MINUTES` for a fast test).
  - Observations: ______________________
  - Severity / remediation: ______________________

## 4. Authorization Testing
- [ ] As a normal user, call each `/api/admin/*` route.
- [ ] As an admin, confirm normal user routes still work as expected.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 5. IDOR / BOLA Testing
- [ ] Create orders as two different users. Try to fetch User B's order id
      while authenticated as User A via `GET /api/orders/<id>`.
- [ ] Repeat the same test against `/api/training/orders/<id>` (training
      mode) and compare behavior.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 6. Privilege Escalation Testing
- [ ] As a normal user, attempt every admin action (dashboard, list users,
      create product).
- [ ] Try modifying the JWT payload's `role` claim (re-sign or tamper) and
      resending.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 7. JWT Testing
- [ ] Decode your JWT (e.g., jwt.io) and review its claims.
- [ ] Try an `alg: none` token.
- [ ] Try a token signed with a guessed/empty secret.
- [ ] Compare behavior between `/api/profile` and `/api/training/profile`.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 8. Input Validation Testing
- [ ] Submit oversized strings, negative numbers, and wrong types
      (e.g., `quantity: "abc"`) to each endpoint that accepts a body.
- [ ] Submit SQL-injection-style payloads (`' OR 1=1 --`) in text fields.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 9. Excessive Data Exposure Testing
- [ ] Compare the fields returned by `/api/profile` vs. `/api/admin/users`.
- [ ] Compare `/api/profile` vs `/api/training/profile`.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 10. Rate-Limit Testing
- [ ] Send 10+ rapid failed logins to `/api/login` from the same client.
- [ ] Repeat against `/api/training/login`.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 11. Error-Handling Testing
- [ ] Send malformed JSON, missing Content-Type, and invalid ids to each
      endpoint. Check whether any response reveals a stack trace, file
      path, or SQL fragment.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 12. HTTP-Method Testing
- [ ] Try `PUT`/`DELETE`/`PATCH` against every documented endpoint.
- [ ] Include `/api/training/products` in this pass.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 13. Security-Header Testing
- [ ] Inspect response headers on both secure and training-mode routes.
      Note any headers present on one but missing on the other.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 14. Sensitive-Data Exposure Testing
- [ ] Check the raw SQLite file for plaintext passwords (there should be none).
- [ ] Check `reports/audit.log` for anything sensitive being logged.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 15. Business-Logic Testing
- [ ] Order a quantity greater than available stock.
- [ ] Order a negative or zero quantity.
- [ ] Order a non-existent `product_id`.
  - Observations: ______________________
  - Severity / remediation: ______________________

## 16. Logging and Monitoring Testing
- [ ] Perform a mix of successful/failed logins and admin actions, then
      review `reports/audit.log` for completeness and accuracy.
  - Observations: ______________________
  - Severity / remediation: ______________________

---

**Next step**: once you've completed your own testing and written up your
findings, open `docs/developer-remediation-guide.md` to compare notes and
review the secure replacement code for every training scenario.
