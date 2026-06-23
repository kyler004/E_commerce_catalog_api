# API Router Documentation

Frontend integration guide for the E-commerce Catalog API. All routes are JSON over HTTP. Unless noted, send `Content-Type: application/json` on requests with a body.

**Development base URL:** `http://127.0.0.1:8000`

| Area | Base path |
| :--- | :-------- |
| Catalog | `/api/` |
| Auth | `/api/auth/` |
| Cart | `/api/cart/` |
| Orders | `/api/orders/` |
| Promotions (staff) | `/api/promotions/` |
| Wishlist | `/api/wishlist/` |

---

## Quick start for frontend

### 1. Authenticate

Most shopper flows require a **verified** JWT. Obtain tokens after signup OTP verification:

```http
POST /api/auth/login/
{ "email": "user@example.com", "password": "SecurePass123!" }
```

Store `access` and `refresh`. Attach the access token to protected requests:

```http
Authorization: Bearer <access_token>
```

Refresh before expiry:

```http
POST /api/auth/token/refresh/
{ "refresh": "<refresh_token>" }
```

### 2. Browse catalog (public)

No auth required for `GET` on categories, products, variants, inventories, and product reviews.

### 3. Shopper flows (verified JWT)

| Flow | Key endpoints |
| :--- | :------------ |
| Add to cart | `POST /api/cart/items/` |
| Apply promo | `POST /api/cart/apply-promo/` |
| Checkout | `POST /api/orders/checkout/` |
| Pay (stub) | `POST /api/orders/{id}/confirm-payment/` |
| Wishlist | `POST /api/wishlist/items/` |
| Review | `POST /api/products/{id}/reviews/` (requires paid order) |

### 4. Admin / staff flows

Catalog writes and promotion CRUD require a JWT from a user with `is_staff=True`.

---

## Authentication levels

| Level | Header | Can access |
| :---- | :----- | :--------- |
| **Public** | None | Catalog reads, product review lists |
| **Authenticated** | `Bearer <access>` | `/api/auth/me/` only |
| **Verified user** | `Bearer <access>` (email verified) | Cart, orders, wishlist, reviews (write), catalog writes |
| **Staff** | `Bearer <access>` (`is_staff`) | Promotion CRUD at `/api/promotions/` |

Unverified users receive **403** on cart, order, wishlist, and catalog write endpoints.

Login before email verification returns **401** with a generic credentials message.

---

## Complete endpoint index

### Auth — `/api/auth/`

| Method | Path | Auth | Description |
| :----- | :--- | :--- | :---------- |
| `POST` | `/register/` | Public | Register; sends signup OTP |
| `POST` | `/verify-email/` | Public | Activate account with OTP |
| `POST` | `/resend-otp/` | Public | Resend OTP (`signup` or `password_reset`) |
| `POST` | `/login/` | Public | Login; returns JWT pair |
| `POST` | `/token/refresh/` | Public | Refresh access token |
| `POST` | `/forgot-password/` | Public | Request password reset OTP |
| `POST` | `/reset-password/` | Public | Reset password with OTP |
| `GET` | `/me/` | Authenticated | Current user profile |

### Catalog — `/api/`

| Method | Path | Auth | Description |
| :----- | :--- | :--- | :---------- |
| `GET` | `/categories/` | Public | List categories |
| `POST` | `/categories/` | Verified | Create category |
| `GET` | `/categories/{id}/` | Public | Category detail |
| `PUT` | `/categories/{id}/` | Verified | Replace category |
| `PATCH` | `/categories/{id}/` | Verified | Partial update |
| `DELETE` | `/categories/{id}/` | Verified | Delete category |
| `GET` | `/products/` | Public | List products |
| `POST` | `/products/` | Verified | Create product |
| `GET` | `/products/{id}/` | Public | Product detail |
| `PUT` | `/products/{id}/` | Verified | Replace product |
| `PATCH` | `/products/{id}/` | Verified | Partial update |
| `DELETE` | `/products/{id}/` | Verified | Delete product |
| `GET` | `/products/{id}/reviews/` | Public | List product reviews |
| `POST` | `/products/{id}/reviews/` | Verified | Create review |
| `GET` | `/variants/` | Public | List variants |
| `POST` | `/variants/` | Verified | Create variant |
| `GET` | `/variants/{id}/` | Public | Variant detail |
| `PUT` | `/variants/{id}/` | Verified | Replace variant |
| `PATCH` | `/variants/{id}/` | Verified | Partial update |
| `DELETE` | `/variants/{id}/` | Verified | Delete variant |
| `GET` | `/inventories/` | Public | List inventory records |
| `POST` | `/inventories/` | Verified | Create inventory |
| `GET` | `/inventories/{id}/` | Public | Inventory detail |
| `PUT` | `/inventories/{id}/` | Verified | Replace inventory |
| `PATCH` | `/inventories/{id}/` | Verified | Partial update |
| `DELETE` | `/inventories/{id}/` | Verified | Delete inventory |
| `PATCH` | `/reviews/{id}/` | Verified (owner) | Update own review |
| `DELETE` | `/reviews/{id}/` | Verified (owner) | Delete own review |

### Cart — `/api/cart/`

| Method | Path | Auth | Description |
| :----- | :--- | :--- | :---------- |
| `GET` | `/` | Verified | Get cart with promo preview |
| `DELETE` | `/` | Verified | Clear all items and applied promo |
| `POST` | `/items/` | Verified | Add or merge variant line |
| `PATCH` | `/items/{id}/` | Verified | Update line quantity |
| `DELETE` | `/items/{id}/` | Verified | Remove line |
| `POST` | `/apply-promo/` | Verified | Apply promotion code |
| `DELETE` | `/promo/` | Verified | Remove applied promotion |

### Orders — `/api/orders/`

| Method | Path | Auth | Description |
| :----- | :--- | :--- | :---------- |
| `POST` | `/checkout/` | Verified | Create order from cart |
| `GET` | `/` | Verified | List user's orders |
| `GET` | `/{id}/` | Verified | Order detail |
| `POST` | `/{id}/confirm-payment/` | Verified | Stub payment; decrements stock |
| `POST` | `/{id}/cancel/` | Verified | Cancel pending order |

### Promotions — `/api/promotions/` (staff only)

| Method | Path | Auth | Description |
| :----- | :--- | :--- | :---------- |
| `GET` | `/` | Staff | List promotions |
| `POST` | `/` | Staff | Create promotion |
| `GET` | `/{id}/` | Staff | Promotion detail |
| `PUT` | `/{id}/` | Staff | Replace promotion |
| `PATCH` | `/{id}/` | Staff | Partial update |
| `DELETE` | `/{id}/` | Staff | Delete promotion |

### Wishlist — `/api/wishlist/`

| Method | Path | Auth | Description |
| :----- | :--- | :--- | :---------- |
| `GET` | `/` | Verified | Get wishlist |
| `POST` | `/items/` | Verified | Add product |
| `DELETE` | `/items/{id}/` | Verified | Remove item |
| `POST` | `/items/{id}/move-to-cart/` | Verified | Move item to cart |

---

## Conventions

### Request format

- **Content-Type:** `application/json` for all POST/PATCH/PUT bodies.
- **Decimals:** Returned as strings (e.g. `"79.99"`). Send numbers or strings on write.
- **Dates:** ISO 8601 UTC (e.g. `"2026-06-22T10:00:00Z"`).
- **IDs:** Integer primary keys in URL paths and request bodies.

### Error responses

Validation and business-rule failures typically return:

```json
{ "detail": "Human-readable message." }
```

Field-level validation (auth forms, serializers):

```json
{
  "email": ["A user with this email already exists."],
  "password": ["This password is too short."]
}
```

OTP endpoints are rate-limited; excess requests return **429** with `{ "detail": "..." }`.

### Pagination

Paginated list endpoints (`categories`, `products`, `variants`, `inventories`, `orders`, `promotions`, `product reviews`) accept:

| Parameter | Default | Max | Description |
| :-------- | :------ | :-- | :---------- |
| `page` | `1` | — | Page number |
| `page_size` | `10` | `100` | Items per page |

**Response shape:**

```json
{
  "count": 42,
  "next": "http://127.0.0.1:8000/api/products/?page=3",
  "previous": "http://127.0.0.1:8000/api/products/?page=1",
  "results": []
}
```

Non-paginated endpoints (cart, wishlist, single order detail) return the resource directly.

---

## Authentication

### Register

```http
POST /api/auth/register/
Content-Type: application/json

{ "email": "user@example.com", "password": "SecurePass123!" }
```

| Field | Required | Notes |
| :---- | :------- | :---- |
| `email` | Yes | Lowercased on save; must be unique |
| `password` | Yes | Min 8 chars; Django password validators apply |

**Response (201):** `{ "detail": "Verification code sent to your email." }`

Account is created **inactive** until OTP verification.

### Verify email

```http
POST /api/auth/verify-email/
{ "email": "user@example.com", "otp": "123456" }
```

**Response (200):** `{ "detail": "Email verified successfully." }`

**Errors (400):** `{ "otp": ["Invalid or expired code."] }`

### Resend OTP

```http
POST /api/auth/resend-otp/
{ "email": "user@example.com", "purpose": "signup" }
```

| Field | Required | Values |
| :---- | :------- | :----- |
| `purpose` | Yes | `"signup"` or `"password_reset"` |

**Response (200):** `{ "detail": "Verification code sent to your email." }`

### Login

```http
POST /api/auth/login/
{ "email": "user@example.com", "password": "SecurePass123!" }
```

**Response (200):**

```json
{
  "access": "<jwt>",
  "refresh": "<jwt>"
}
```

**Errors (401):** Unverified or invalid credentials — `{ "detail": "No active account found with the given credentials." }`

### Refresh token

```http
POST /api/auth/token/refresh/
{ "refresh": "<refresh_token>" }
```

**Response (200):** `{ "access": "<new_access_token>" }`

### Forgot password

```http
POST /api/auth/forgot-password/
{ "email": "user@example.com" }
```

**Response (200):** `{ "detail": "If an account exists for this email, a verification code has been sent." }`

Always returns 200 (no email enumeration).

### Reset password

```http
POST /api/auth/reset-password/
{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "NewSecurePass456!"
}
```

**Response (200):** `{ "detail": "Password reset successfully." }`

### Current user

```http
GET /api/auth/me/
Authorization: Bearer <access_token>
```

**Response (200):**

```json
{
  "id": 1,
  "email": "user@example.com",
  "email_verified_at": "2026-06-22T10:00:00Z"
}
```

Use `email_verified_at !== null` to gate shopper UI before login, or rely on login succeeding only after verification.

---

## Catalog

Catalog **reads** are public. **Writes** require `Authorization: Bearer <access_token>` from a verified user.

### Categories — `/api/categories/`

**Query parameters:**

| Parameter | Type | Description |
| :-------- | :--- | :---------- |
| `name` | string | Exact name match |
| `parent` | integer | Filter by parent category ID |
| `search` | string | Search `name`, `description` |
| `ordering` | string | `name`, `created_at` (prefix `-` for desc) |

**Response fields:**

| Field | Type | Notes |
| :---- | :--- | :---- |
| `id` | integer | Primary key |
| `name` | string | Category name |
| `description` | string | Optional |
| `parent` | integer \| null | Parent category ID |
| `products` | array | Nested products (read-only) |

**Create / update body:**

```json
{
  "name": "Electronics",
  "description": "Electronic devices and accessories",
  "parent": null
}
```

### Products — `/api/products/`

**Query parameters:**

| Parameter | Type | Description |
| :-------- | :--- | :---------- |
| `min_price` | number | Minimum price (inclusive) |
| `max_price` | number | Maximum price (inclusive) |
| `color` | string | Variant color (case-insensitive) |
| `size` | string | Variant size (case-insensitive) |
| `category` | integer | Category ID |
| `search` | string | Search `name`, `description` |
| `ordering` | string | `price`, `created_at` |

**Response fields:**

| Field | Type | Notes |
| :---- | :--- | :---- |
| `id` | integer | Primary key |
| `name` | string | Product name |
| `description` | string | Product description |
| `price` | decimal string | Unit price |
| `category` | integer | Category ID |
| `created_at` | datetime | ISO 8601 |
| `average_rating` | number \| null | Mean review rating (2 decimal places) |
| `review_count` | integer | Total reviews |
| `variants` | array | Nested variants with inventory (read-only) |

**Create / update body:**

```json
{
  "name": "Wireless Headphones",
  "description": "Noise-cancelling over-ear headphones",
  "price": "79.99",
  "category": 1
}
```

> Variants are **not** created via the product endpoint. Use `/api/variants/`.

**Example product detail:**

```json
{
  "id": 1,
  "name": "Wireless Headphones",
  "description": "Noise-cancelling over-ear headphones",
  "price": "79.99",
  "category": 1,
  "created_at": "2026-06-21T10:00:00Z",
  "average_rating": 4.5,
  "review_count": 12,
  "variants": [
    {
      "id": 1,
      "product": 1,
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

### Variants — `/api/variants/`

**Query parameters:** `product`, `size`, `color`, `search` (SKU)

**Response fields:**

| Field | Type | Notes |
| :---- | :--- | :---- |
| `id` | integer | Primary key |
| `product` | integer | Product ID |
| `size` | string | Optional |
| `color` | string | Optional |
| `sku` | string | Unique SKU |
| `inventory` | object \| null | Nested `{ quantity, last_updated }` |

**Create / update body:**

```json
{ "product": 1, "size": "L", "color": "Red", "sku": "WH-L-RED" }
```

> Creating a variant does **not** create inventory. Add stock via `/api/inventories/`.

### Inventory — `/api/inventories/`

**Query parameters:** `variant`, `quantity`

**Response fields:**

| Field | Type | Notes |
| :---- | :--- | :---- |
| `quantity` | integer | Stock count |
| `last_updated` | datetime | Auto-updated on save |

**Create / update body:**

```json
{ "variant": 3, "quantity": 50 }
```

One inventory record per variant.

---

## Shopping cart

All endpoints require a verified user JWT. One server-side cart per user. Line items reference **variants**. Prices snapshot from `Product.price`. Stock is validated but **not** reserved or decremented until payment.

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
  "promotion": {
    "code": "SAVE10",
    "discount_amount": "16.00",
    "total": "143.98"
  },
  "updated_at": "2026-06-22T10:00:00Z"
}
```

`promotion` is `null` when no code is applied or the applied code is no longer valid for the current subtotal.

### Add item

```http
POST /api/cart/items/
{ "variant": 1, "quantity": 2 }
```

| Field | Required | Notes |
| :---- | :------- | :---- |
| `variant` | Yes | Variant ID |
| `quantity` | No | Default `1`; min `1` |

**Response (201):** Cart line object plus nested `cart` summary (same shape as GET cart).

Adding the same variant **merges** quantities into one row.

### Update item

```http
PATCH /api/cart/items/{id}/
{ "quantity": 3 }
```

**Response (200):** Updated line + nested `cart`.

### Remove item / clear cart

```http
DELETE /api/cart/items/{id}/     → 204 No Content
DELETE /api/cart/                → 204 No Content (also clears applied promo)
```

### Apply promotion

```http
POST /api/cart/apply-promo/
{ "code": "SAVE10" }
```

**Response (200):** Full cart object with updated `promotion` preview.

**Errors (400):** `{ "detail": "Promotion has expired." }` (or similar validation message)

### Remove promotion

```http
DELETE /api/cart/promo/
```

**Response (200):** Full cart object with `promotion: null`.

### Cart business rules

| Rule | Behavior |
| :--- | :------- |
| Duplicate variant | One row per variant; POST increments quantity |
| Stock limit | `quantity` ≤ `available_quantity` on variant |
| Price | `unit_price` refreshed from catalog on add/update |
| Ownership | Other users' item IDs return **404** |
| Inventory | Cart does not reserve or decrement stock |

---

## Orders / checkout

All endpoints require a verified user JWT. Checkout creates a **pending** order, snapshots line items and shipping, applies any cart promotion, then **clears the cart**. Inventory decrements only on payment confirmation.

### Checkout

```http
POST /api/orders/checkout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "shipping": {
    "full_name": "Jane Doe",
    "address_line1": "123 Main St",
    "address_line2": "Apt 4",
    "city": "Paris",
    "postal_code": "75001",
    "country": "FR",
    "phone": "+33600000000"
  }
}
```

| Shipping field | Required | Notes |
| :------------- | :------- | :---- |
| `full_name` | Yes | |
| `address_line1` | Yes | |
| `address_line2` | No | |
| `city` | Yes | |
| `postal_code` | Yes | |
| `country` | Yes | |
| `phone` | No | |

**Response (201):**

```json
{
  "id": 1,
  "status": "pending",
  "subtotal": "159.98",
  "discount_amount": "16.00",
  "promotion_code": "SAVE10",
  "total": "143.98",
  "items": [
    {
      "id": 1,
      "variant": 1,
      "product_name": "Wireless Headphones",
      "sku": "WH-L-RED",
      "size": "L",
      "color": "Red",
      "quantity": 2,
      "unit_price": "79.99",
      "line_total": "159.98"
    }
  ],
  "shipping": {
    "full_name": "Jane Doe",
    "address_line1": "123 Main St",
    "address_line2": "Apt 4",
    "city": "Paris",
    "postal_code": "75001",
    "country": "FR",
    "phone": "+33600000000"
  },
  "created_at": "2026-06-23T10:00:00Z",
  "updated_at": "2026-06-23T10:00:00Z",
  "paid_at": null
}
```

`discount_amount` is `"0.00"` and `promotion_code` is `""` when no promo was applied.

**Errors (400):** Empty cart, insufficient stock, invalid shipping — `{ "detail": "..." }`

### List orders

```http
GET /api/orders/?page=1&page_size=10
```

**Result item fields:** `id`, `status`, `total`, `item_count`, `created_at`, `paid_at`

`status` values: `"pending"`, `"paid"`, `"cancelled"`

### Order detail

```http
GET /api/orders/{id}/
```

Returns full order shape (same as checkout response).

### Confirm payment (stub)

```http
POST /api/orders/{id}/confirm-payment/
```

**Response (200):** Order with `"status": "paid"` and `paid_at` set.

**Errors:**
- **404** — Order not found or not owned by user
- **400** — Not pending, or insufficient stock at payment time

Increments promotion `used_count` when order had a `promotion_code`.

### Cancel order

```http
POST /api/orders/{id}/cancel/
```

**Response (200):** Order with `"status": "cancelled"`

Only **pending** orders can be cancelled. No inventory change (stock was never decremented).

### Recommended checkout UI flow

```
Cart (with promo) → POST checkout → pending order → confirm-payment → paid
                                              ↘ cancel → cancelled
```

---

## Promotions (staff)

Staff JWT required for CRUD. Shoppers interact with promotions only via cart apply/remove and checkout.

### List / create

```http
GET /api/promotions/
POST /api/promotions/
```

**Create body:**

```json
{
  "code": "SAVE10",
  "description": "10% off orders over $50",
  "discount_type": "percentage",
  "discount_value": "10.00",
  "min_order_amount": "50.00",
  "max_uses": 100,
  "valid_from": "2026-06-01T00:00:00Z",
  "valid_until": "2026-12-31T23:59:59Z",
  "is_active": true
}
```

| Field | Required | Notes |
| :---- | :------- | :---- |
| `code` | Yes | Stored uppercase |
| `discount_type` | Yes | `"percentage"` or `"fixed"` |
| `discount_value` | Yes | Percent (e.g. `10.00`) or fixed amount |
| `min_order_amount` | No | Minimum cart subtotal |
| `max_uses` | No | Global usage cap |
| `valid_from` / `valid_until` | No | ISO datetimes |
| `is_active` | No | Default `true` |

**Response fields:** `id`, `code`, `description`, `discount_type`, `discount_value`, `min_order_amount`, `max_uses`, `used_count`, `valid_from`, `valid_until`, `is_active`, `created_at`, `updated_at`

`used_count` is read-only; incremented on order payment confirmation.

### Update / delete

```http
GET    /api/promotions/{id}/
PUT    /api/promotions/{id}/
PATCH  /api/promotions/{id}/
DELETE /api/promotions/{id}/
```

---

## Wishlist

All endpoints require a verified user JWT. Items are saved at the **product** level (one row per product, not per variant).

### Get wishlist

```http
GET /api/wishlist/
```

**Response (200):**

```json
{
  "id": 1,
  "items": [
    {
      "id": 5,
      "product": {
        "id": 1,
        "name": "Wireless Headphones",
        "price": "79.99"
      },
      "added_at": "2026-06-22T10:00:00Z"
    }
  ],
  "item_count": 1,
  "updated_at": "2026-06-22T10:00:00Z"
}
```

### Add product

```http
POST /api/wishlist/items/
{ "product": 1 }
```

**Response (201):** Single wishlist item object.

**Errors (400):** Duplicate product — `{ "detail": "Product is already in your wishlist." }`

### Remove item

```http
DELETE /api/wishlist/items/{id}/
```

**Response:** **204** No Content

### Move to cart

```http
POST /api/wishlist/items/{id}/move-to-cart/
{ "variant": 1, "quantity": 1 }
```

| Field | Required | Notes |
| :---- | :------- | :---- |
| `variant` | Yes | Must belong to the wishlisted product |
| `quantity` | No | Default `1` |

**Response (201):** Cart line object (same as add-to-cart) with nested `cart` summary. Wishlist item is **removed** after a successful move.

---

## Reviews

### List product reviews (public)

```http
GET /api/products/{product_id}/reviews/?page=1
```

**Result item fields:**

| Field | Type | Notes |
| :---- | :--- | :---- |
| `id` | integer | Review ID |
| `user_email` | string | Reviewer email (read-only) |
| `rating` | integer | 1–5 |
| `title` | string | Optional |
| `body` | string | Review text |
| `created_at` | datetime | |
| `updated_at` | datetime | |

Product list/detail also expose `average_rating` and `review_count` for summary display.

### Create review (verified purchase required)

```http
POST /api/products/{product_id}/reviews/
Authorization: Bearer <access_token>

{ "rating": 5, "title": "Great product", "body": "Would buy again." }
```

| Field | Required | Notes |
| :---- | :------- | :---- |
| `rating` | Yes | Integer 1–5 |
| `title` | No | Max 255 chars |
| `body` | Yes | Review text |

**Response (201):** Review object.

**Errors (400):**
- `{ "detail": "You can only review products you have purchased." }`
- `{ "detail": "You have already reviewed this product." }`

Purchase verification: user must have a **paid** order containing a variant of the product.

### Update / delete own review

```http
PATCH  /api/reviews/{id}/
DELETE /api/reviews/{id}/
```

Only the review **owner** can modify or delete. Other users receive **404**.

**PATCH body:** Any subset of `{ "rating", "title", "body" }`

---

## HTTP status codes

| Code | When |
| :--- | :--- |
| **200** | Success (GET, PATCH, PUT, promo remove) |
| **201** | Created (POST register, cart item, checkout, review, etc.) |
| **204** | No content (DELETE cart, cart item, wishlist item) |
| **400** | Validation or business rule failure |
| **401** | Missing/invalid token, or login before verification |
| **403** | Authenticated but not verified (or non-staff on staff routes) |
| **404** | Resource not found or not owned by user |
| **429** | OTP rate limit exceeded |

---

## Frontend integration patterns

### Token storage

Store `refresh` securely (httpOnly cookie or secure storage). Keep `access` in memory or short-lived storage. Refresh proactively or on **401**.

### Gating UI by auth state

| State | Suggested UI |
| :---- | :----------- |
| Logged out | Browse catalog; prompt login for cart/checkout |
| Logged in, unverified | Show OTP verification screen; block cart |
| Verified | Full shopper features |
| Staff | Admin promotion management |

### Stock display

Use `variant.inventory.quantity` from product detail, or `variant.available_quantity` on cart lines (same value, cart-specific field name).

### Price display

- **Catalog:** `product.price` (same for all variants of a product)
- **Cart/order:** `unit_price` and `line_total` on line items (snapshotted at add/checkout)

### Error handling checklist

- Parse `detail` string for toast messages
- Parse field keys for form inline errors
- On cart **400**, show stock or promo message from `detail`
- On checkout **400**, re-fetch cart (may have been partially consumed)

---

## Related source files

| File | Purpose |
| :--- | :------ |
| [`E_commerce_catalog_api/urls.py`](../E_commerce_catalog_api/urls.py) | Root URL mounting |
| [`accounts/urls.py`](../accounts/urls.py) | Auth routes |
| [`accounts/serializers.py`](../accounts/serializers.py) | Auth schemas |
| [`api/urls.py`](../api/urls.py) | Catalog + review routes |
| [`api/serializers.py`](../api/serializers.py) | Catalog schemas |
| [`cart/urls.py`](../cart/urls.py) | Cart routes |
| [`cart/serializers.py`](../cart/serializers.py) | Cart schemas |
| [`orders/urls.py`](../orders/urls.py) | Order routes |
| [`orders/serializers.py`](../orders/serializers.py) | Order schemas |
| [`promotions/urls.py`](../promotions/urls.py) | Promotion routes |
| [`promotions/serializers.py`](../promotions/serializers.py) | Promotion schemas |
| [`wishlists/urls.py`](../wishlists/urls.py) | Wishlist routes |
| [`reviews/views.py`](../reviews/views.py) | Review views |
