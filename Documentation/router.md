# API Router Documentation

This document describes all HTTP routes exposed by the E-commerce Catalog API. Routes are registered via Django REST Framework's `DefaultRouter` in [`api/urls.py`](../api/urls.py) and mounted at `/api/` from the project root URL config.

**Base URL (development):** `http://127.0.0.1:8000/api/`

**Auth base URL:** `http://127.0.0.1:8000/api/auth/`

**Cart base URL:** `http://127.0.0.1:8000/api/cart/`

---

## Authentication

Catalog list/retrieve endpoints are public. Create, update, and delete operations require a JWT from a verified user:

```http
Authorization: Bearer <access_token>
```

### Auth endpoints

| Method | Path | Description |
| :----- | :--- | :---------- |
| `POST` | `/api/auth/register/` | Register with email and password; sends signup OTP |
| `POST` | `/api/auth/verify-email/` | Verify signup OTP and activate account |
| `POST` | `/api/auth/resend-otp/` | Resend OTP for `signup` or `password_reset` |
| `POST` | `/api/auth/login/` | Login with email and password; returns JWT pair |
| `POST` | `/api/auth/token/refresh/` | Refresh access token |
| `POST` | `/api/auth/forgot-password/` | Send password reset OTP |
| `POST` | `/api/auth/reset-password/` | Reset password with OTP |
| `GET` | `/api/auth/me/` | Current user profile |

### Register

```http
POST /api/auth/register/
Content-Type: application/json

{ "email": "user@example.com", "password": "SecurePass123!" }
```

**Response (201):**

```json
{ "detail": "Verification code sent to your email." }
```

### Verify email

```http
POST /api/auth/verify-email/
Content-Type: application/json

{ "email": "user@example.com", "otp": "123456" }
```

### Login

```http
POST /api/auth/login/
Content-Type: application/json

{ "email": "user@example.com", "password": "SecurePass123!" }
```

**Response (200):**

```json
{
  "access": "<jwt>",
  "refresh": "<jwt>"
}
```

### Forgot / reset password

```http
POST /api/auth/forgot-password/
{ "email": "user@example.com" }

POST /api/auth/reset-password/
{ "email": "user@example.com", "otp": "123456", "new_password": "NewSecurePass456!" }
```

### SMTP configuration

OTP emails require SMTP settings in `.env`:

| Variable | Description |
| :------- | :---------- |
| `EMAIL_HOST` | SMTP server hostname |
| `EMAIL_PORT` | SMTP port (default `587`) |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password |
| `EMAIL_USE_TLS` | `True` or `False` |
| `DEFAULT_FROM_EMAIL` | Sender address |

---

## Shopping Cart

All cart endpoints require a JWT from a **verified** user. Carts are server-side (one per user). Line items reference catalog **variants**. Prices are snapshotted from `Product.price` on add/update. Stock is checked against `Inventory.quantity` but inventory is **not** decremented by cart operations.

### Cart endpoints

| Method | Path | Description |
| :----- | :--- | :---------- |
| `GET` | `/api/cart/` | Current user's cart (auto-created if empty) |
| `DELETE` | `/api/cart/` | Remove all items from cart |
| `POST` | `/api/cart/items/` | Add variant or increment existing line |
| `PATCH` | `/api/cart/items/{id}/` | Update line quantity |
| `DELETE` | `/api/cart/items/{id}/` | Remove line item |

### Add item

```http
POST /api/cart/items/
Authorization: Bearer <access_token>
Content-Type: application/json

{ "variant": 1, "quantity": 2 }
```

**Response (201):**

```json
{
  "id": 10,
  "variant": {
    "id": 1,
    "sku": "WH-L-RED",
    "size": "L",
    "color": "Red",
    "product_name": "Wireless Headphones",
    "available_quantity": 50
  },
  "quantity": 2,
  "unit_price": "79.99",
  "line_total": "159.98",
  "cart": {
    "id": 1,
    "items": [],
    "item_count": 2,
    "subtotal": "159.98",
    "updated_at": "2026-06-22T10:00:00Z"
  }
}
```

Adding the same variant again **merges** into one row (quantities are summed).

### Get cart

```http
GET /api/cart/
Authorization: Bearer <access_token>
```

**Response (200):**

```json
{
  "id": 1,
  "items": [
    {
      "id": 10,
      "variant": {
        "id": 1,
        "sku": "WH-L-RED",
        "size": "L",
        "color": "Red",
        "product_name": "Wireless Headphones",
        "available_quantity": 48
      },
      "quantity": 2,
      "unit_price": "79.99",
      "line_total": "159.98"
    }
  ],
  "item_count": 2,
  "subtotal": "159.98",
  "updated_at": "2026-06-22T10:00:00Z"
}
```

### Business rules

| Rule | Behavior |
| :--- | :------- |
| Duplicate variant | One row per variant; POST increments quantity |
| Stock limit | `quantity` must not exceed `Inventory.quantity` |
| Price | `unit_price` refreshed from catalog on add/update |
| Ownership | Users can only access their own cart items (404 for others) |
| Inventory | Cart does not reserve or decrement stock |

---

## Route Overview

| Resource     | Base path           | ViewSet            |
| :----------- | :------------------ | :----------------- |
| Categories   | `/api/categories/`  | `CategoryViewSet`  |
| Products     | `/api/products/`    | `ProductViewSet`   |
| Variants     | `/api/variants/`    | `VariantViewSet`   |
| Inventory    | `/api/inventories/` | `InventoryViewSet` |

Each resource supports standard REST actions. **Write operations** (`POST`, `PUT`, `PATCH`, `DELETE`) require a JWT from a verified user. **Read operations** (`GET`) are public.

| Method   | URL pattern              | Action   | Description              |
| :------- | :----------------------- | :------- | :----------------------- |
| `GET`    | `/api/{resource}/`       | `list`   | List all records         |
| `POST`   | `/api/{resource}/`       | `create` | Create a new record      |
| `GET`    | `/api/{resource}/{id}/`  | `retrieve` | Get a single record  |
| `PUT`    | `/api/{resource}/{id}/`  | `update` | Replace a record       |
| `PATCH`  | `/api/{resource}/{id}/`  | `partial_update` | Update fields  |
| `DELETE` | `/api/{resource}/{id}/`  | `destroy` | Delete a record       |

---

## Pagination

All list endpoints use `StandardPagination`:

| Parameter   | Default | Max  | Description                    |
| :---------- | :------ | :--- | :----------------------------- |
| `page`      | `1`     | —    | Page number                    |
| `page_size` | `10`    | `100`| Number of items per page       |

**Example:**

```http
GET /api/products/?page=2&page_size=20
```

**List response shape:**

```json
{
  "count": 42,
  "next": "http://127.0.0.1:8000/api/products/?page=3",
  "previous": "http://127.0.0.1:8000/api/products/?page=1",
  "results": []
}
```

---

## Categories

**Endpoint:** `/api/categories/`

### Query parameters

| Parameter  | Type    | Description                                      |
| :--------- | :------ | :----------------------------------------------- |
| `name`     | string  | Exact match on category name                     |
| `parent`   | integer | Filter by parent category ID                     |
| `search`   | string  | Search in `name` and `description`               |
| `ordering` | string  | Sort by `name` or `created_at` (prefix `-` for desc) |

**Examples:**

```http
GET /api/categories/?search=electronics
GET /api/categories/?parent=1
GET /api/categories/?ordering=-created_at
```

### Response fields

| Field         | Type    | Notes                                      |
| :------------ | :------ | :----------------------------------------- |
| `id`          | integer | Primary key                                |
| `name`        | string  | Category name                              |
| `description` | string  | Optional description                       |
| `parent`      | integer | Parent category ID, or `null` for root     |
| `products`    | array   | Nested products (read-only on list/detail) |

### Create / update request body

```json
{
  "name": "Electronics",
  "description": "Electronic devices and accessories",
  "parent": null
}
```

| Field         | Required | Notes                          |
| :------------ | :------- | :----------------------------- |
| `name`        | Yes      | Max 255 characters             |
| `description` | No       | Can be empty                   |
| `parent`      | No       | ID of parent category, or null |

---

## Products

**Endpoint:** `/api/products/`

### Query parameters

| Parameter   | Type    | Description                                      |
| :---------- | :------ | :----------------------------------------------- |
| `min_price` | number  | Minimum price (inclusive)                        |
| `max_price` | number  | Maximum price (inclusive)                        |
| `color`     | string  | Filter by variant color (case-insensitive)       |
| `size`      | string  | Filter by variant size (case-insensitive)        |
| `category`  | integer | Filter by category ID                            |
| `search`    | string  | Search in `name` and `description`               |
| `ordering`  | string  | Sort by `price` or `created_at`                  |

**Examples:**

```http
GET /api/products/?min_price=20&max_price=100&color=Red
GET /api/products/?category=1&size=S
GET /api/products/?search=laptop&ordering=price
```

### Response fields

| Field         | Type    | Notes                                      |
| :------------ | :------ | :----------------------------------------- |
| `id`          | integer | Primary key                                |
| `name`        | string  | Product name                               |
| `description` | string  | Product description                        |
| `price`       | decimal | Price with up to 2 decimal places          |
| `category`    | integer | Category ID                                |
| `created_at`  | datetime| ISO 8601 timestamp                         |
| `variants`    | array   | Nested variants with inventory (read-only) |

### Create / update request body

```json
{
  "name": "Wireless Headphones",
  "description": "Noise-cancelling over-ear headphones",
  "price": "79.99",
  "category": 1
}
```

| Field         | Required | Notes                          |
| :------------ | :------- | :----------------------------- |
| `name`        | Yes      | Max 255 characters             |
| `description` | Yes      | Product description            |
| `price`       | Yes      | Decimal, max 10 digits         |
| `category`    | Yes      | Valid category ID              |

> **Note:** Variants cannot be created through the product endpoint. Create variants separately via `/api/variants/`.

---

## Variants

**Endpoint:** `/api/variants/`

### Query parameters

| Parameter | Type    | Description                          |
| :-------- | :------ | :----------------------------------- |
| `product` | integer | Filter by product ID                 |
| `size`    | string  | Exact match on size                  |
| `color`   | string  | Exact match on color                 |
| `search`  | string  | Search by SKU                        |

**Examples:**

```http
GET /api/variants/?product=1&color=Red
GET /api/variants/?search=P1-L-RED
```

### Response fields

| Field       | Type    | Notes                                      |
| :---------- | :------ | :----------------------------------------- |
| `id`        | integer | Primary key                                |
| `size`      | string  | Variant size (optional)                    |
| `color`     | string  | Variant color (optional)                   |
| `sku`       | string  | Unique stock-keeping unit                  |
| `inventory` | object  | Nested inventory record (read-only), or `null` |

### Create / update request body

```json
{
  "product": 1,
  "size": "L",
  "color": "Red",
  "sku": "WH-L-RED"
}
```

| Field     | Required | Notes                          |
| :-------- | :------- | :----------------------------- |
| `product` | Yes      | Valid product ID               |
| `size`    | No       | Max 50 characters              |
| `color`   | No       | Max 50 characters              |
| `sku`     | Yes      | Must be unique across variants |

> **Note:** Creating a variant does not automatically create an inventory record. Add stock via `/api/inventories/`.

---

## Inventory

**Endpoint:** `/api/inventories/`

### Query parameters

| Parameter  | Type    | Description              |
| :--------- | :------ | :----------------------- |
| `variant`  | integer | Filter by variant ID     |
| `quantity` | integer | Exact match on quantity  |

**Example:**

```http
GET /api/inventories/?variant=3
```

### Response fields

| Field          | Type     | Notes                          |
| :------------- | :------- | :----------------------------- |
| `quantity`     | integer  | Stock count (default: 0)       |
| `last_updated` | datetime | ISO 8601, auto-updated on save |

### Create / update request body

```json
{
  "variant": 3,
  "quantity": 50
}
```

| Field      | Required | Notes                                    |
| :--------- | :------- | :--------------------------------------- |
| `variant`  | Yes      | Valid variant ID (one inventory per variant) |
| `quantity` | No       | Non-negative integer, defaults to 0      |

---

## Nested response example

A product detail response includes nested variants and inventory:

```json
{
  "id": 1,
  "name": "Wireless Headphones",
  "description": "Noise-cancelling over-ear headphones",
  "price": "79.99",
  "category": 1,
  "created_at": "2026-06-21T10:00:00Z",
  "variants": [
    {
      "id": 1,
      "size": "L",
      "color": "Red",
      "sku": "WH-L-RED",
      "inventory": {
        "quantity": 50,
        "last_updated": "2026-06-21T12:30:00Z"
      }
    }
  ]
}
```

A category detail response nests the full product tree:

```json
{
  "id": 1,
  "name": "Electronics",
  "description": "Electronic devices",
  "parent": null,
  "products": [
    {
      "id": 1,
      "name": "Wireless Headphones",
      "description": "Noise-cancelling over-ear headphones",
      "price": "79.99",
      "category": 1,
      "created_at": "2026-06-21T10:00:00Z",
      "variants": []
    }
  ]
}
```

---

## HTTP status codes

| Code | Meaning                                      |
| :--- | :------------------------------------------- |
| 200  | Success (GET, PUT, PATCH)                    |
| 201  | Created (POST)                               |
| 204  | No content (DELETE)                          |
| 400  | Bad request (validation error)               |
| 401  | Unauthorized (missing or invalid token)      |
| 403  | Forbidden (e.g. unverified email)            |
| 404  | Resource not found                           |
| 429  | Too many requests (OTP rate limit)           |

---

## Related files

| File | Purpose |
| :--- | :------ |
| [`accounts/urls.py`](../accounts/urls.py) | Auth route registration |
| [`accounts/views.py`](../accounts/views.py) | Auth API views |
| [`accounts/serializers.py`](../accounts/serializers.py) | Auth request/response schemas |
| [`accounts/models.py`](../accounts/models.py) | User and EmailOTP models |
| [`accounts/services/otp.py`](../accounts/services/otp.py) | OTP generation and validation |
| [`cart/urls.py`](../cart/urls.py) | Cart route registration |
| [`cart/views.py`](../cart/views.py) | Cart API views |
| [`cart/serializers.py`](../cart/serializers.py) | Cart request/response schemas |
| [`cart/models.py`](../cart/models.py) | Cart and CartItem models |
| [`cart/services.py`](../cart/services.py) | Cart business logic |
| [`api/urls.py`](../api/urls.py) | Catalog router registration |
| [`api/views.py`](../api/views.py) | ViewSets, pagination, filter backends |
| [`api/serializers.py`](../api/serializers.py) | Request/response schemas |
| [`api/filters.py`](../api/filters.py) | Product filter definitions |
| [`api/models.py`](../api/models.py) | Database models |
| [`E_commerce_catalog_api/urls.py`](../E_commerce_catalog_api/urls.py) | Root URL mounting at `/api/` |
