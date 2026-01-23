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

## proper Tech Stack

- **Language:** Python 3.12+
- **Framework:** Django 5.x
- **API Toolkit:** Django REST Framework
- **Filtering:** django-filter

## Getting Started

### Prerequisites

- Python 3.8 or higher installed.

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

4.  **Apply database migrations**

    ```bash
    python manage.py migrate
    ```

5.  **Run the development server**
    ```bash
    python manage.py runserver
    ```

The API will be available at `http://127.0.0.1:8000/api/`.

## API Endpoints

| Resource       | Endpoint                | Description                          |
| :------------- | :---------------------- | :----------------------------------- |
| **Products**   | `GET /api/products/`    | List all products. Supports filters. |
|                | `POST /api/products/`   | Create a new product.                |
| **Categories** | `GET /api/categories/`  | List all categories.                 |
| **Variants**   | `GET /api/variants/`    | List product variants.               |
| **Inventory**  | `GET /api/inventories/` | Check stock levels.                  |

### Example Filtering

**Filter by Price and Color:**

```http
GET /api/products/?min_price=20&max_price=100&color=Red
```
