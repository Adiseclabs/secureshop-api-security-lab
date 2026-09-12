# SecureShop API - Local Security Assessment Lab

A lightweight, fully local REST API built for hands-on API security
practice with Burp Suite and Postman. Everything - app, database, and
data - runs on your own machine. Nothing here talks to the internet, a
cloud service, or any real organization.

## ⚠️ Ethical-Use Notice

This project is an **authorized local training lab only**.

- Do not deploy this application anywhere other than your own local
  machine.
- Do not point it at real user data, real credentials, or any external
  system.
- Training Mode (see below) intentionally contains weakened security
  controls for learning purposes - never enable it outside local practice.
- You are responsible for using this project in accordance with your own
  organization's policies and applicable law. Only test systems you own
  or are explicitly authorized to test.

## Project Overview

SecureShop is a fictional e-commerce API with users, products, and
orders. It ships two things in one codebase:

1. A **secure API** implementing standard controls (auth, RBAC, object-
   level authorization, rate limiting, input validation, secure headers,
   audit logging, etc.) - see `docs/secure-controls.md`.
2. An optional, clearly separated **Training Mode** that exposes a parallel
   set of intentionally weakened endpoints under `/api/training/*`, for
   practicing vulnerability discovery. Off by default.

## Learning Objectives

- Practice recognizing common API vulnerability classes (OWASP API
  Security Top 10 style: BOLA, broken auth, excessive data exposure,
  missing rate limiting, weak input validation, etc.).
- Compare a secure implementation against a deliberately weakened one of
  the same feature, side by side.
- Practice a structured manual testing workflow with Burp Suite and
  Postman against a safe, disposable target.
- Practice writing up findings and remediation.

## Features

- User registration & login with JWT authentication
- User profiles
- Product catalog (list + detail)
- Order creation & order history
- Admin dashboard, user management, and product management
- Fake seed data: 1 admin, 2 normal users, 6 products, 3 sample orders
- Optional Training Mode with randomized/config-selectable vulnerable
  scenarios, a reset script, and a separate remediation guide

## Technology Stack

- Python 3
- Flask
- SQLite (file-based, no external DB server)
- Flask-SQLAlchemy
- PyJWT
- Werkzeug password hashing
- Postman collection for manual testing
- No Docker, no VMs, no cloud services - runs directly on Windows

## System Requirements

- Windows 10/11
- Python 3.10+ installed and on PATH
- ~200 MB free disk space
- Comfortably runs on 8 GB RAM (this is a single lightweight Flask
  process with a file-based SQLite database - no heavy dependencies)

## Windows Installation Instructions

Open **PowerShell** or **Command Prompt** in the project folder.

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` appear at the start of your prompt.

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Set up environment variables

```powershell
copy .env.example .env
```

Open `.env` in a text editor and set your own local `JWT_SECRET_KEY`
(any random string is fine for local use). Leave `TRAINING_MODE=false`
for now.

### 4. Initialize the database

```powershell
python scripts\init_database.py
```

This creates `database/secureshop.db` and loads the fake sample data.
Sample credentials are printed to the console - also listed below.

### 5. Start the API

```powershell
python app.py
```

The API will be available at `http://127.0.0.1:5000`.

## Sample Local Credentials

| Role  | Email                            | Password      |
|-------|-----------------------------------|---------------|
| Admin | admin@secureshop.local            | AdminPass123  |
| User  | jordan.rivera@secureshop.local    | UserPass123   |
| User  | casey.morgan@secureshop.local     | UserPass456   |

All fake, local-only accounts - not real people.

## API Endpoint Table

See `docs/api-endpoints.md` for the full reference with example requests
and responses. Quick summary:

| Method | Path | Auth |
|---|---|---|
| GET | /api/health | none |
| POST | /api/register | none |
| POST | /api/login | none |
| GET | /api/products | none |
| GET | /api/products/<id> | none |
| GET | /api/profile | user |
| POST | /api/orders | user |
| GET | /api/orders | user |
| GET | /api/orders/<id> | user |
| GET | /api/admin/dashboard | admin |
| GET | /api/admin/users | admin |
| POST | /api/admin/products | admin |

## Importing the Postman Collection

1. Open Postman.
2. Click **Import** -> select `postman/SecureShop-API.postman_collection.json`.
3. Also import `postman/SecureShop-Local.postman_environment.json`.
4. Select the **SecureShop Local** environment in the top-right dropdown.
5. Run **Login** first - it automatically stores the JWT into the
   `jwt_token` environment variable for the rest of the requests.

## Using Burp Suite with the Local API

1. Start the Flask app (`python app.py`).
2. Configure Postman (or your browser) to route traffic through Burp's
   proxy (default `127.0.0.1:8080`), or use Burp's built-in browser.
3. Install Burp's CA certificate if you want to inspect HTTPS - not
   required here since the local app runs over plain HTTP on `127.0.0.1`.
4. Send a request through Postman/browser once so it appears in Burp's
   **Proxy > HTTP history**.
5. Right-click any request -> **Send to Repeater** to manually modify and
   resend requests (tampering with JWTs, ids, body fields, headers, etc.).
6. Use **Intruder** for rate-limit and brute-force testing against
   `/api/login` (respect the lab's own rate limiting - that's part of
   what you're testing!).

## Training Mode

Training Mode adds a parallel, clearly separated set of intentionally
weakened endpoints under `/api/training/*` so you can practice finding
real vulnerability patterns safely.

### Enabling it

Edit `.env`:
```
TRAINING_MODE=true
```

Then re-initialize so a scenario set is selected for this build:
```powershell
python scripts\init_database.py
```
Restart the app. You'll see a console warning banner, and every response
will include an `X-Training-Mode: enabled` header as a constant reminder.

### Disabling it

Set `TRAINING_MODE=false` in `.env` and restart the app. The
`/api/training/*` routes are not even registered when this is off - there
is no way to reach them.

### Important notes

- Training Mode requires **three** independent conditions to all be true
  (the `TRAINING_MODE` flag, a non-production `FLASK_ENV`, and `DEBUG`
  enabled) - see `config.py` for the exact interlock. This makes it very
  hard to enable by accident.
- Which specific vulnerable scenarios are active is randomized each time
  you run `scripts\init_database.py` (or pinned via `TRAINING_SCENARIOS`
  in `.env` if you want a reproducible build) - not every scenario is
  guaranteed to be present in a given run. Find them yourself using
  `docs/testing-checklist.md`.
- The specific vulnerabilities are **not** listed in this README. See
  `docs/developer-remediation-guide.md` (clearly marked **read after
  testing**) once you've done your own assessment.
- Run `python scripts\reset_database.py` at any time to wipe the database
  and training-mode state and start completely fresh.

## Troubleshooting

- **`'python' is not recognized...`** - Reinstall Python from
  python.org and check "Add Python to PATH" during setup.
- **`ModuleNotFoundError`** - Make sure your virtual environment is
  activated (`venv\Scripts\activate`) before running `pip install` or
  `python app.py`.
- **Port already in use** - Change `PORT` in `.env` and restart.
- **Database errors after changing models** - Run
  `python scripts\reset_database.py` to rebuild from scratch.
- **JWT errors after restarting the app** - If you didn't set a fixed
  `JWT_SECRET_KEY` in `.env`, a new random one is generated on every
  restart, invalidating old tokens. Log in again to get a fresh token.

## Project Structure

```text
secure-shop-api/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── database/
│   ├── db.py
│   └── seed.py
├── models/
│   ├── user.py
│   ├── product.py
│   └── order.py
├── routes/
│   ├── auth_routes.py
│   ├── user_routes.py
│   ├── product_routes.py
│   ├── order_routes.py
│   ├── admin_routes.py
│   ├── health_routes.py
│   └── training/
│       ├── scenario_manager.py
│       └── training_routes.py
├── utils/
│   ├── auth.py
│   ├── validators.py
│   └── security.py
├── docs/
│   ├── api-endpoints.md
│   ├── testing-checklist.md
│   ├── secure-controls.md
│   └── developer-remediation-guide.md
├── postman/
│   ├── SecureShop-API.postman_collection.json
│   └── SecureShop-Local.postman_environment.json
├── scripts/
│   ├── init_database.py
│   └── reset_database.py
├── tests/
│   └── test_api.py
└── reports/
    └── .gitkeep
```

## Running the Basic Tests

```powershell
pytest
```

Covers the health check, registration, login, weak-password rejection,
authentication requirement, and admin-role enforcement. These confirm the
app's plumbing works - they are not the security assessment itself.

## License / Attribution

Educational project. Fictional company, fictional data, local use only.
