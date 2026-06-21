# API Router Documentation

This document describes all HTTP routes exposed by the E-commerce Catalog API. Routes are registered via Django REST Framework's `DefaultRouter` in [`api/urls.py`](../api/urls.py) and mounted at `/api/` from the project root URL config.

**Base URL (development):** `http://127.0.0.1:8000/api/`

---

## Route Overview

| Resource     | Base path           | ViewSet            |
| :----------- | :------------------ | :----------------- |
| Categories   | `/api/categories/`  | `CategoryViewSet`  |
| Products     | `/api/products/`    | `ProductViewSet`   |
| Variants     | `/api/variants/`    | `VariantViewSet`   |
| Inventory    | `/api/inventories/` | `InventoryViewSet` |

Each resource supports standard REST actions:

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
| 404  | Resource not found                           |

---

## Related files

| File | Purpose |
| :--- | :------ |
| [`api/urls.py`](../api/urls.py) | Router registration |
| [`api/views.py`](../api/views.py) | ViewSets, pagination, filter backends |
| [`api/serializers.py`](../api/serializers.py) | Request/response schemas |
| [`api/filters.py`](../api/filters.py) | Product filter definitions |
| [`api/models.py`](../api/models.py) | Database models |
| [`E_commerce_catalog_api/urls.py`](../E_commerce_catalog_api/urls.py) | Root URL mounting at `/api/` |
