# SecureShop API - Endpoint Reference

Base URL (local): `http://127.0.0.1:5000`

All responses use this envelope:

```json
{
  "status": 200,
  "message": "Human-readable message",
  "data": { }
}
```

## Public

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Liveness check. Shows whether training mode is on. |
| POST | `/api/register` | Create a new user account (role is always "user"). |
| POST | `/api/login` | Authenticate and receive a JWT. |
| GET | `/api/products` | List all products. |
| GET | `/api/products/<id>` | Get a single product by id. |

## Authenticated (user)

Send `Authorization: Bearer <token>` on every request below.

| Method | Path | Description |
|---|---|---|
| GET | `/api/profile` | Get the current user's own profile. |
| POST | `/api/orders` | Create an order (`product_id`, `quantity`). |
| GET | `/api/orders` | List the current user's own orders. |
| GET | `/api/orders/<id>` | Get one of the current user's own orders. |

## Authenticated (admin only)

| Method | Path | Description |
|---|---|---|
| GET | `/api/admin/dashboard` | Aggregate counts. |
| GET | `/api/admin/users` | List all users (full admin view). |
| POST | `/api/admin/products` | Create a new product. |

## Example: register

Request:
```json
POST /api/register
{
  "name": "Jamie Example",
  "email": "jamie.example@secureshop.local",
  "password": "SamplePass123"
}
```

Response (201):
```json
{
  "status": 201,
  "message": "Registration successful.",
  "data": { "id": 4, "name": "Jamie Example", "email": "jamie.example@secureshop.local", "role": "user" }
}
```

## Example: login

Request:
```json
POST /api/login
{ "email": "jamie.example@secureshop.local", "password": "SamplePass123" }
```

Response (200):
```json
{
  "status": 200,
  "message": "Login successful.",
  "data": { "token": "<jwt>", "user": { "id": 4, "name": "Jamie Example", "email": "jamie.example@secureshop.local", "role": "user" } }
}
```

## Example: create order

Request (with `Authorization: Bearer <token>`):
```json
POST /api/orders
{ "product_id": 1, "quantity": 2 }
```

Response (201):
```json
{
  "status": 201,
  "message": "Order created successfully.",
  "data": { "id": 4, "user_id": 2, "product_id": 1, "product_name": "Wireless Mouse", "quantity": 2, "total_price": 39.98, "status": "placed", "created_at": "2026-01-01T12:00:00" }
}
```

> A training-mode-only endpoint group also exists at `/api/training/*` when
> `TRAINING_MODE=true`. It is intentionally undocumented here - see the
> README's "Training Mode" section for how to enable/disable it, and
> `docs/developer-remediation-guide.md` (read AFTER testing) for details.
