# SecureShop API (Local API Security Assessment Lab)
<img width="2752" height="722" alt="Gemini_Generated_Image_tzegnktzegnktzeg" src="https://github.com/user-attachments/assets/92c676f1-c279-4291-ab02-1cdcfd495a30" />


![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-REST%20API-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Postman](https://img.shields.io/badge/Tested%20with-Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white)
![Burp Suite](https://img.shields.io/badge/Tested%20with-Burp%20Suite-FF6633?style=for-the-badge&logo=burpsuite&logoColor=white)
![Local Only](https://img.shields.io/badge/Deployment-Local%20Only-critical?style=for-the-badge)
![License](https://img.shields.io/badge/License-Educational-blue?style=for-the-badge)

A lightweight, fully local REST API built for hands-on **API security testing practice** using Burp Suite and Postman. Everything — the application, the database, and the data — runs entirely on your own machine. Nothing connects to the internet, a cloud service, or any real organization.

This is a **fictional e-commerce company ("SecureShop")** implemented twice, in parallel:
1. A **secure API** with production-style defensive controls, so you have a correct reference implementation to compare against.
2. An optional, clearly separated **Training Mode** with intentionally weakened versions of the same endpoints, so you can practice discovering real vulnerability patterns safely.

>  anotherimg


---

## ⚠️ Ethical Use Notice

- This is an **authorized local training lab only**. Do not deploy it anywhere other than your own machine.
- Never point it at real user data, real credentials, or any external system.
- Training Mode intentionally contains weakened security controls for learning purposes — never enable it outside local practice, and never expose this server to a shared network or the internet.
- You are responsible for using this project in line with your own organization's policies and applicable law.

---

## What's Included

| Area | Details |
|---|---|
| **Application** | Flask REST API — user registration/login, profiles, product catalog, order creation/history, admin dashboard/user management/product management |
| **Database** | SQLite (file-based, zero setup) via Flask-SQLAlchemy |
| **Auth** | JWT (JSON Web Tokens), salted password hashing (Werkzeug PBKDF2) |
| **Roles** | `user` and `admin`, enforced server-side on every request |
| **Fake sample data** | 1 admin, 2 normal users, 6 products, 3 sample orders — all fictional |
| **Security controls** | Authentication, RBAC, object-level authorization (anti-IDOR), input validation, rate limiting, SQL-injection prevention (parameterized ORM queries), secure error handling, security headers, audit logging |
| **Training Mode** | A parallel `/api/training/*` route set with randomized, config-selectable intentionally-vulnerable scenarios — off by default, cannot be enabled by accident |
| **Documentation** | Full API reference, a secure-controls explainer, a manual testing checklist (no answers), and a developer remediation guide (read *after* testing) |
| **Postman collection** | Pre-built requests + environment with auto-chaining variables (login auto-saves your JWT) |
| **Tests** | Basic pytest suite covering health check, registration, login, and authorization behavior |

No Docker, no virtual machines, no cloud services — just Python and Flask, light enough to run comfortably on an 8 GB RAM laptop.

---

## Project Structure

```text
secure-shop-api/
├── app.py                     # App factory & entry point
├── config.py                  # Env-driven config + training-mode safety interlock
├── requirements.txt
├── .env.example
├── database/                  # SQLAlchemy instance + fake seed data
├── models/                    # User, Product, Order
├── routes/                    # Secure blueprints: auth, user, product, order, admin, health
│   └── training/              # Training Mode blueprint (only loaded if enabled)
├── utils/                     # auth (JWT), validators, security (headers/rate-limit/logging)
├── docs/                      # api-endpoints, secure-controls, testing-checklist, remediation guide
├── postman/                   # Collection + environment
├── scripts/                   # init_database.py, reset_database.py
├── tests/                     # pytest suite
└── reports/                   # audit.log gets written here at runtime
```

---

## Requirements

- Windows 10/11 (instructions below use PowerShell; the app itself is cross-platform)
- Python 3.10+ installed and available on PATH
- ~200 MB free disk space
- Postman and Burp Suite (Community Edition is fine) for manual testing

---

## Setup & Installation

Run these from inside the project folder.

### 1. Create a virtual environment

```powershell
python -m venv venv
```

### 2. Activate it

```powershell
venv\Scripts\activate
```

Your prompt should now start with `(venv)`. **Every time you open a new terminal to work on this project, activate the venv again first** — it doesn't stay active across terminal sessions.

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

This installs Flask, Flask-SQLAlchemy, PyJWT, Werkzeug, python-dotenv, and pytest.

### 4. Create your environment file

```powershell
copy .env.example .env
```

Open `.env` in a text editor and set `JWT_SECRET_KEY` to any random string — this keeps your login tokens valid across app restarts. Leave `TRAINING_MODE=false` for now.

### 5. Initialize the database

```powershell
python scripts\init_database.py
```

This creates `database/secureshop.db` and loads the fake seed data. Sample credentials print to the console (also listed below).

### 6. Start the API

```powershell
python app.py
```

The API is now live at `http://127.0.0.1:5000`.

### 7. Confirm it's running

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

Use `Invoke-RestMethod` rather than PowerShell's `curl` alias — `curl` on Windows maps to `Invoke-WebRequest`, which tries to parse responses as HTML and throws an unnecessary security prompt for a JSON API.

---

## Sample Local Credentials

| Role | Email | Password |
|---|---|---|
| Admin | admin@secureshop.local | AdminPass123 |
| User | jordan.rivera@secureshop.local | UserPass123 |
| User | casey.morgan@secureshop.local | UserPass456 |

All fictional, local-only accounts.

---

## API Endpoint Reference

Full request/response examples live in `docs/api-endpoints.md`. Summary:

| Method | Path | Auth Required |
|---|---|---|
| GET | `/api/health` | none |
| POST | `/api/register` | none |
| POST | `/api/login` | none |
| GET | `/api/products` | none |
| GET | `/api/products/<id>` | none |
| GET | `/api/profile` | user |
| POST | `/api/orders` | user |
| GET | `/api/orders` | user |
| GET | `/api/orders/<id>` | user |
| GET | `/api/admin/dashboard` | admin |
| GET | `/api/admin/users` | admin |
| POST | `/api/admin/products` | admin |

Every response follows the same JSON envelope:
```json
{ "status": 200, "message": "...", "data": { } }
```

---

## How to Use This for API Testing

### With Postman

1. Open Postman → **Import** → select `postman/SecureShop-API.postman_collection.json` and `postman/SecureShop-Local.postman_environment.json`.
2. Select **SecureShop Local** from the environment dropdown (top right).
3. Run **Login** first — a test script automatically saves the returned JWT into the `jwt_token` variable, so every other request in the collection is pre-authenticated.
4. Work through the requests: Register → Login → Profile → Products → Create Order → Order History → Admin routes.
5. For each request, try both the "happy path" and deliberately bad input — wrong types, missing fields, someone else's resource ID, etc.

> 📌 <img width="1502" height="895" alt="image" src="https://github.com/user-attachments/assets/bf56ea7d-8593-4866-90e6-5e8f0fd2f958" />

### With Burp Suite

1. Start the Flask app (`python app.py`).
2. Route Postman (or a browser) through Burp's proxy — default `127.0.0.1:8080`.
3. Send a few requests through Postman so they show up in **Proxy → HTTP history**.
4. Right-click any request → **Send to Repeater** to manually tamper with headers, JSON bodies, IDs, and JWTs, then resend.
5. Use **Intruder** to test rate limiting on `/api/login` (you should see the API push back after a few failed attempts).

> 📌 *Screenshot idea: capture a Repeater tab showing a tampered order ID request and the API's response.*

### A Suggested Testing Order

Work through `docs/testing-checklist.md` — it has a section and space for your own notes on each of the following, without giving you the answers:

1. **Auth basics** — no token, garbage token, expired token on a protected route.
2. **Authorization** — a normal user calling any `/api/admin/*` route.
3. **Object-level authorization (IDOR)** — log in as User A, try fetching an order that belongs to User B by ID.
4. **Input validation** — non-numeric IDs, negative quantities, oversized strings, SQL-injection-style payloads.
5. **Rate limiting** — several rapid failed logins from the same client.
6. **Error handling** — confirm no response ever leaks a stack trace, file path, or raw SQL.
7. **HTTP methods** — try `DELETE`/`PUT` against read-only routes.
8. **Headers** — confirm security headers (`X-Content-Type-Options`, `X-Frame-Options`, CSP, etc.) are present on every response.

### Training Mode (optional, for deliberate vulnerability practice)

Once you're comfortable with the secure API's expected behavior, you can enable a parallel set of intentionally weakened endpoints to practice finding real flaws:

```powershell
# In .env:
TRAINING_MODE=true
```
```powershell
python scripts\init_database.py   # rolls a random set of active scenarios
python app.py                     # restart — a console warning confirms it's on
```

- Every response includes an `X-Training-Mode: enabled` header as a constant reminder.
- Which specific scenarios are active is randomized per build (or pinned via `TRAINING_SCENARIOS` in `.env` for a reproducible run) — not documented anywhere in this README on purpose.
- Test the `/api/training/*` routes the same way, using the same checklist.
- Only after finishing your own assessment, open `docs/developer-remediation-guide.md` — it explains every scenario, its impact, how to reproduce it, and the secure fix.
- Run `python scripts\reset_database.py` any time to wipe the database and get a fresh random scenario set.
- Set `TRAINING_MODE=false` and restart to fully disable it — the training routes aren't even registered when it's off, so there's no way to reach them.

---

## Running the Automated Tests

```powershell
pytest
```

Covers the health check, registration, weak-password rejection, login, the auth-required check on `/api/profile`, and the admin-role check on `/api/admin/dashboard`. These confirm the app's plumbing works — they are not a substitute for your own manual security testing.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `'python' is not recognized...` | Reinstall Python from python.org, check "Add Python to PATH" |
| `ModuleNotFoundError` | Activate the venv (`venv\Scripts\activate`) before running anything |
| Port already in use | Change `PORT` in `.env` and restart |
| Database errors after model changes | Run `python scripts\reset_database.py` |
| Tokens stop working after restart | You didn't set a fixed `JWT_SECRET_KEY` in `.env` — a new one generates each restart. Log in again for a fresh token |
| `curl` throws a script-execution warning | Use `Invoke-RestMethod` instead of the `curl`/`Invoke-WebRequest` alias |

---

## License / Attribution

Educational project. Fictional company, fictional data, local use only.

Built by **Aditya Bhosale**.
