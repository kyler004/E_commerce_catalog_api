# E-commerce Catalog API

Backend API for an e-commerce storefront built with Django and Django REST Framework. It supports catalog browsing, verified-user shopping flows, promotions, checkout, order receipts, wishlist management, verified-purchase reviews, and account spending analytics.

## Feature Overview

- **Catalog:** Categories, products, variants, inventory, product images, filtering, search, ordering, pagination, and rating aggregates.
- **Authentication:** Email/password registration, OTP email verification, JWT login/refresh, current-user profile, and OTP password reset.
- **Cart:** Server-side cart per verified user, variant line items, stock validation, price snapshots, cart totals, and promotion preview.
- **Checkout and Orders:** Cart-to-order checkout with shipping address, pending/paid/cancelled lifecycle, inventory decrement on payment confirmation, order history filters, and HTML receipts.
- **Promotions:** Staff-managed percentage or fixed discount codes with active windows, minimum order amount, max-use limits, and usage tracking.
- **Wishlist:** Product-level saved items with move-to-cart support.
- **Reviews:** Verified-purchase product reviews, one review per user per product, and product rating aggregates.
- **Account Analytics:** Dedicated spending summary endpoint for lifetime spend, monthly totals, category totals, savings, average order value, and recent paid orders.

## Tech Stack

- **Language:** Python 3.12+
- **Framework:** Django 6.x
- **API Toolkit:** Django REST Framework
- **Authentication:** `djangorestframework-simplejwt`
- **Filtering:** `django-filter`
- **Database:** PostgreSQL for development/runtime, in-memory SQLite for tests
- **Configuration:** `python-dotenv`
- **CORS:** `django-cors-headers`

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 14+ or Docker Compose

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd E_commerce_catalog_api
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your PostgreSQL and SMTP settings. SMTP is used for OTP emails.

5. Start PostgreSQL with Docker:

   ```bash
   docker-compose up -d db
   ```

   If you use a local PostgreSQL instance instead, create the database manually:

   ```bash
   createdb -U postgres ecommerce_catalog
   ```

6. Apply migrations:

   ```bash
   python manage.py migrate
   ```

   Run this after pulling schema changes. If API responses mention a missing column, your database likely has pending migrations.

7. Run the development server:

   ```bash
   python manage.py runserver
   ```

The API will be available at `http://127.0.0.1:8000/`.

### Seed Catalog Data

The project includes a management command that populates realistic shoe catalog data:

```bash
python manage.py populate_shoes
```

### Run Tests

Tests use an in-memory SQLite database, so PostgreSQL does not need to be running:

```bash
python manage.py test accounts api cart orders promotions wishlists reviews
```

## Authentication and Authorization

Auth endpoints are mounted at `/api/auth/`.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/auth/register/` | `POST` | Register with email and password; sends signup OTP |
| `/api/auth/verify-email/` | `POST` | Verify signup OTP and activate account |
| `/api/auth/resend-otp/` | `POST` | Resend OTP for `signup` or `password_reset` |
| `/api/auth/login/` | `POST` | Login and receive JWT access/refresh tokens |
| `/api/auth/token/refresh/` | `POST` | Refresh access token |
| `/api/auth/forgot-password/` | `POST` | Request password reset OTP |
| `/api/auth/reset-password/` | `POST` | Reset password with OTP |
| `/api/auth/me/` | `GET` | Return current authenticated user profile |

Signup flow:

1. `POST /api/auth/register/` with `{ "email", "password" }`.
2. `POST /api/auth/verify-email/` with `{ "email", "otp" }`.
3. `POST /api/auth/login/` with `{ "email", "password" }`.

Use JWT access tokens on protected requests:

```http
Authorization: Bearer <access_token>
```

Catalog reads and review lists are public. Cart, checkout, orders, wishlist, review writes, receipts, spending summaries, and catalog writes require a verified user JWT. Promotion CRUD requires staff access.

## Catalog API

Catalog routes are mounted under `/api/`.

| Resource | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| Categories | `/api/categories/` | Public read, verified write | Hierarchical category CRUD |
| Products | `/api/products/` | Public read, verified write | Product CRUD with rating aggregates |
| Variants | `/api/variants/` | Public read, verified write | Size/color/SKU variants |
| Inventory | `/api/inventories/` | Public read, verified write | Variant stock records |
| Product reviews | `/api/products/{id}/reviews/` | Public `GET`, verified `POST` | Product review list/create |
| Review detail | `/api/reviews/{id}/` | Owner | Update/delete own review |

Product filters include:

| Param | Purpose |
| :--- | :--- |
| `min_price`, `max_price` | Price range |
| `color`, `size` | Variant attributes |
| `category` | Category ID |
| `search` | Name/description search |
| `ordering` | Supported ordering fields |
| `page`, `page_size` | Pagination |

Example:

```http
GET /api/products/?min_price=20&max_price=100&color=Red&page_size=12
```

Product responses include `average_rating` and `review_count`.

## Shopping Cart

Cart endpoints are mounted at `/api/cart/`. All cart operations require a verified user JWT.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/cart/` | `GET` | View cart items and totals |
| `/api/cart/` | `DELETE` | Clear the cart |
| `/api/cart/items/` | `POST` | Add or increment `{ "variant", "quantity" }` |
| `/api/cart/items/{id}/` | `PATCH` | Update item quantity |
| `/api/cart/items/{id}/` | `DELETE` | Remove item |
| `/api/cart/apply-promo/` | `POST` | Apply promotion code `{ "code" }` |
| `/api/cart/promo/` | `DELETE` | Remove applied promotion |

Stock is validated when adding/updating cart items. Inventory is not decremented until payment confirmation.

## Orders, Checkout, and Receipts

Order endpoints are mounted at `/api/orders/`. All order endpoints require a verified user JWT and are scoped to the authenticated user.

### Checkout Flow

1. Add variants to the cart.
2. `POST /api/orders/checkout/` with a shipping address.
3. Backend creates a `pending` order, snapshots line-item details, and clears the cart.
4. `POST /api/orders/{id}/confirm-payment/` marks the order `paid`, decrements inventory, and records `paid_at`.
5. `POST /api/orders/{id}/cancel/` cancels a pending order.

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

### Order Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/orders/checkout/` | `POST` | Create pending order from cart |
| `/api/orders/` | `GET` | Paginated order list |
| `/api/orders/{id}/` | `GET` | Full order detail |
| `/api/orders/{id}/confirm-payment/` | `POST` | Stub payment confirmation |
| `/api/orders/{id}/cancel/` | `POST` | Cancel pending order |
| `/api/orders/{id}/receipt/` | `GET` | HTML receipt for paid order |

### Order List Filters

`GET /api/orders/` supports:

| Param | Allowed values | Purpose |
| :--- | :--- | :--- |
| `status` | `paid`, `pending`, `cancelled` | Filter by order status |
| `ordering` | `-paid_at`, `-created_at`, `-total` | Sort paid date, created date, or total descending |
| `paid_after`, `paid_before` | `YYYY-MM-DD` or ISO datetime | Paid-date range |
| `created_after`, `created_before` | `YYYY-MM-DD` or ISO datetime | Created-date range |
| `page`, `page_size` | Pagination controls | Paginated browsing |

Examples:

```http
GET /api/orders/?status=paid&ordering=-paid_at&page=1&page_size=20
```

```http
GET /api/orders/?status=paid&paid_after=2026-01-01&paid_before=2026-12-31
```

Use the order list for tables and receipt archives. Use the spending summary endpoint for charts and lifetime totals.

### Receipts

Receipts are HTML responses for paid orders:

```http
GET /api/orders/{id}/receipt/
```

Pending or cancelled orders return `400 Bad Request`. Orders belonging to another user return `404 Not Found`.

For a receipt archive page:

```http
GET /api/orders/?status=paid&ordering=-paid_at&page=1&page_size=20
```

## Account Spending Summary

The account analytics endpoint is mounted at `/api/account/spending-summary/` and requires a verified user JWT.

```http
GET /api/account/spending-summary/?period=12m
```

| Param | Default | Purpose |
| :--- | :--- | :--- |
| `period` | `12m` | Chart window. Use `6m`, `12m`, `24m`, or `all`. |

Response:

```json
{
  "currency": "USD",
  "lifetime_spend": "1249.50",
  "paid_order_count": 12,
  "pending_order_count": 1,
  "cancelled_order_count": 2,
  "total_savings": "89.00",
  "average_order_value": "104.13",
  "spending_by_month": [
    { "period": "2025-07", "total": "320.00", "order_count": 3 }
  ],
  "spending_by_category": [
    { "category_id": 2, "category_name": "Apparel", "total": "450.00", "order_count": 4 }
  ],
  "recent_paid_orders": [
    { "id": 42, "total": "143.98", "paid_at": "2026-06-23T10:00:00Z", "item_count": 2 }
  ]
}
```

Rules:

- Only `paid` orders count toward spend metrics.
- Pending and cancelled orders are counted separately.
- Time-series data uses `paid_at`, with `created_at` as a fallback.
- `discount_amount` is aggregated into `total_savings`.
- Results are strictly scoped to the authenticated user.
- Category analytics use category snapshots stored on each order line at checkout.

## Category Snapshots

Order items snapshot product and category data at checkout:

- `product_name`
- `sku`
- `size`
- `color`
- `category_id`
- `category_name`
- `unit_price`
- `line_total`

This keeps order history, receipts, and category spending charts stable even if catalog products are later renamed, moved, or deleted.

After pulling the snapshot migration, run:

```bash
python manage.py migrate orders
```

## Promotions

Staff manage promotion codes at `/api/promotions/`. Customers apply codes to their cart before checkout.

| Endpoint | Method | Access | Description |
| :--- | :--- | :--- | :--- |
| `/api/promotions/` | `GET`, `POST` | Staff | List/create promotions |
| `/api/promotions/{id}/` | `GET`, `PATCH`, `DELETE` | Staff | Retrieve/update/delete promotion |
| `/api/cart/apply-promo/` | `POST` | Verified user | Apply promotion to cart |
| `/api/cart/promo/` | `DELETE` | Verified user | Remove cart promotion |

Promotion discounts are previewed in cart totals, copied to the order at checkout, and counted as used when payment is confirmed.

## Wishlist

Wishlist endpoints are mounted at `/api/wishlist/` and require a verified user JWT.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/wishlist/` | `GET` | View wishlist |
| `/api/wishlist/items/` | `POST` | Add `{ "product" }` |
| `/api/wishlist/items/{id}/` | `DELETE` | Remove item |
| `/api/wishlist/items/{id}/move-to-cart/` | `POST` | Move to cart with `{ "variant", "quantity" }` |

Wishlist items are stored at the product level. Moving to cart requires selecting a variant.

## Reviews

Reviews are mounted under product and review routes.

| Endpoint | Method | Access | Description |
| :--- | :--- | :--- | :--- |
| `/api/products/{id}/reviews/` | `GET` | Public | List product reviews |
| `/api/products/{id}/reviews/` | `POST` | Verified user | Create review after paid purchase |
| `/api/reviews/{id}/` | `PATCH`, `DELETE` | Owner | Update/delete own review |

Review rules:

- The user must have a paid order containing the product.
- One review is allowed per user per product.
- Ratings are 1 to 5.

## Documentation

Additional integration docs live in `Documentation/`:

- `Documentation/router.md` — full frontend route/API integration guide.
- `Documentation/receipt_integration_guide.md` — receipt HTML integration and print guidance.
- `Documentation/spending_summary_integration_guide.md` — order analytics and spending summary integration.

## Development Notes

- The payment flow is currently a stub endpoint. It marks orders as paid and decrements inventory, but it does not integrate with a real payment provider.
- Runtime data uses PostgreSQL. Tests use SQLite in memory.
- Local development CORS is configured for `http://localhost:5173`.
- Keep migrations applied when switching branches or pulling backend schema changes.
