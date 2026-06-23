# E-commerce Catalog API

## Overview

This is a robust backend API for an e-commerce platform, built using **Django** and **Django REST Framework (DRF)**. It provides comprehensive management for product catalogs, including hierarchal categories, product variants (sizes/colors), and real-time inventory tracking.

## Key Features

- **Product Catalog:** logical organization of products into categories and subcategories.
- **Variant Management:** Support for multiple variations of a single product (e.g., Size M / Red, Size L / Blue) with unique SKUs.
- **Inventory Tracking:** Dedicated inventory model linked to specific variants to track stock levels.
- **Advanced Filtering:** Powerful filtering capabilities allowing clients to query products by:
  - **Price Range** (`min_price`, `max_price`)
  - **Attributes** (`color`, `size`)
  - **Category**
- **Authentication:** Email/password registration with OTP email verification, JWT login, and OTP-based password reset.
- **Shopping Cart:** Server-side cart per verified user with variant line items, stock validation, and price snapshotting.
- **Orders / Checkout:** Convert cart to order with shipping address; stub payment flow decrements inventory on confirmation.
- **Promotions:** Percentage or fixed discount codes; staff CRUD; apply to cart with checkout preview; usage tracked on payment confirmation.
- **Wishlists:** Product-level saved items per user; move items directly into the cart.
- **Reviews:** Verified-purchase reviews (paid order required); one review per user per product; product rating aggregates on catalog.

## proper Tech Stack

- **Language:** Python 3.12+
- **Framework:** Django 5.x
- **API Toolkit:** Django REST Framework
- **Authentication:** djangorestframework-simplejwt (JWT)
- **Filtering:** django-filter
- **Database:** PostgreSQL

## Getting Started

### Prerequisites

- Python 3.8 or higher installed.
- PostgreSQL 14+ (local install or Docker via `docker compose`).

### Installation

1.  **Clone the repository**

    ```bash
    git clone <repository-url>
    cd E_commerce_catalog_api
    ```

2.  **Create and activate a virtual environment**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables**

    ```bash
    cp .env.example .env
    ```

    Edit `.env` with your PostgreSQL credentials and SMTP settings (required for OTP emails).

5.  **Start PostgreSQL (Docker)**

    ```bash
    docker-compose up -d db
    ```

    Wait until the database is healthy, then continue.

    If you already have PostgreSQL running on port 5432, create the database manually instead:

    ```bash
    createdb -U postgres ecommerce_catalog
    ```

6.  **Apply database migrations**

    ```bash
    python manage.py migrate
    ```

    If you see an `InconsistentMigrationHistory` error after pulling model changes, your local DB was migrated before the custom user model existed. Reset an empty dev database with `dropdb`/`createdb` (or `docker compose down -v`) and run `migrate` again.

7.  **Run the development server**

    ```bash
    python manage.py runserver
    ```

The API will be available at `http://127.0.0.1:8000/api/`.

### Running tests

Tests use an in-memory SQLite database so PostgreSQL does not need to be running:

```bash
python manage.py test accounts api cart orders promotions wishlists reviews
```

## Authentication

Auth endpoints are mounted at `/api/auth/`. Catalog **read** endpoints are public; **write** endpoints require a verified user JWT.

### Signup flow

1. `POST /api/auth/register/` with `{ "email", "password" }` — creates an inactive account and sends a 6-digit OTP by email.
2. `POST /api/auth/verify-email/` with `{ "email", "otp" }` — verifies the account.
3. `POST /api/auth/login/` with `{ "email", "password" }` — returns `{ "access", "refresh" }` JWT tokens.

### Password reset flow

1. `POST /api/auth/forgot-password/` with `{ "email" }` — sends a reset OTP if the account exists.
2. `POST /api/auth/reset-password/` with `{ "email", "otp", "new_password" }` — sets a new password.

### Authenticated catalog writes

Include the access token on write requests:

```http
POST /api/products/
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Auth endpoints

| Endpoint | Method | Description |
| :------- | :----- | :---------- |
| `/api/auth/register/` | POST | Register with email and password |
| `/api/auth/verify-email/` | POST | Verify signup OTP |
| `/api/auth/resend-otp/` | POST | Resend OTP (`purpose`: `signup` or `password_reset`) |
| `/api/auth/login/` | POST | Login and receive JWT tokens |
| `/api/auth/token/refresh/` | POST | Refresh access token |
| `/api/auth/forgot-password/` | POST | Request password reset OTP |
| `/api/auth/reset-password/` | POST | Reset password with OTP |
| `/api/auth/me/` | GET | Current user profile (authenticated) |

## Shopping Cart

Cart endpoints are at `/api/cart/`. All cart operations require a verified user JWT. Stock is validated against inventory but not decremented until payment is confirmed.

| Endpoint | Method | Description |
| :------- | :----- | :---------- |
| `/api/cart/` | GET | View cart with items and totals |
| `/api/cart/` | DELETE | Clear all cart items |
| `/api/cart/items/` | POST | Add or increment `{ "variant", "quantity" }` |
| `/api/cart/items/{id}/` | PATCH | Update item quantity |
| `/api/cart/items/{id}/` | DELETE | Remove item |
| `/api/cart/apply-promo/` | POST | Apply promotion code `{ "code" }` |
| `/api/cart/promo/` | DELETE | Remove applied promotion |

```http
POST /api/cart/items/
Authorization: Bearer <access_token>
Content-Type: application/json

{ "variant": 1, "quantity": 2 }
```

## Orders / Checkout

Order endpoints are at `/api/orders/`. Checkout converts the cart into a **pending** order with a shipping address and clears the cart. Inventory is decremented only when payment is confirmed via the stub endpoint.

### Checkout flow

1. Add items to cart
2. `POST /api/orders/checkout/` with shipping address → order `pending`, cart cleared
3. `POST /api/orders/{id}/confirm-payment/` → order `paid`, inventory decremented
4. Or `POST /api/orders/{id}/cancel/` on a pending order → order `cancelled`

| Endpoint | Method | Description |
| :------- | :----- | :---------- |
| `/api/orders/checkout/` | POST | Create order from cart + shipping |
| `/api/orders/` | GET | List user's orders (paginated) |
| `/api/orders/{id}/` | GET | Order detail |
| `/api/orders/{id}/confirm-payment/` | POST | Stub payment confirmation |
| `/api/orders/{id}/cancel/` | POST | Cancel pending order |

```http
POST /api/orders/checkout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "shipping": {
    "full_name": "Jane Doe",
    "address_line1": "123 Main St",
    "city": "Paris",
    "postal_code": "75001",
    "country": "FR"
  }
}
```

## Promotions

Staff manage promotion codes at `/api/promotions/` (staff JWT required). Customers apply codes to their cart before checkout.

| Endpoint | Method | Auth | Description |
| :------- | :----- | :--- | :---------- |
| `/api/promotions/` | GET/POST | Staff | List or create promotions |
| `/api/promotions/{id}/` | GET/PATCH/DELETE | Staff | Retrieve, update, or delete |
| `/api/cart/apply-promo/` | POST | Verified user | Apply `{ "code" }` to cart |
| `/api/cart/promo/` | DELETE | Verified user | Remove applied promotion |

Discount is previewed on `GET /api/cart/` and applied at checkout. `used_count` increments when payment is confirmed.

## Wishlist

Wishlist endpoints are at `/api/wishlist/`. Items are saved at the **product** level (not variant).

| Endpoint | Method | Description |
| :------- | :----- | :---------- |
| `/api/wishlist/` | GET | View wishlist |
| `/api/wishlist/items/` | POST | Add `{ "product" }` |
| `/api/wishlist/items/{id}/` | DELETE | Remove item |
| `/api/wishlist/items/{id}/move-to-cart/` | POST | Move to cart `{ "variant", "quantity" }` |

## Reviews

Product reviews require a **verified purchase** (paid order containing the product). One review per user per product; rating 1–5.

| Endpoint | Method | Auth | Description |
| :------- | :----- | :--- | :---------- |
| `/api/products/{id}/reviews/` | GET | Public | List product reviews |
| `/api/products/{id}/reviews/` | POST | Verified user | Create review |
| `/api/reviews/{id}/` | PATCH/DELETE | Owner | Update or delete own review |

Product list/detail responses include `average_rating` and `review_count`.

## API Endpoints

| Resource       | Endpoint                | Description                          |
| :------------- | :---------------------- | :----------------------------------- |
| **Products**   | `GET /api/products/`    | List all products. Supports filters. |
|                | `POST /api/products/`   | Create a new product (auth required). |
| **Categories** | `GET /api/categories/`  | List all categories.                 |
| **Variants**   | `GET /api/variants/`    | List product variants.               |
| **Inventory**  | `GET /api/inventories/` | Check stock levels.                  |

### Example Filtering

**Filter by Price and Color:**

```http
GET /api/products/?min_price=20&max_price=100&color=Red
```
