# Spending Summary and Order Analytics Integration Guide

This guide documents the backend endpoints that support account dashboards, spending charts, order archives, and receipt pages.

**Development base URL:** `http://127.0.0.1:8000`

All endpoints in this guide require a verified user JWT:

```http
Authorization: Bearer <access_token>
```

Unverified users receive `403 Forbidden`. Unauthenticated requests receive `401 Unauthorized`.

---

## Order List Filters

Use the existing order list endpoint when the frontend needs paginated order rows:

```http
GET /api/orders/
```

The endpoint is scoped to the authenticated user and supports the following query parameters:

| Param | Allowed values | Purpose |
| :--- | :--- | :--- |
| `status` | `paid`, `pending`, `cancelled` | Filter order archive by status |
| `ordering` | `-paid_at`, `-created_at`, `-total` | Sort newest paid, newest created, or highest total first |
| `paid_after` | `YYYY-MM-DD` or ISO datetime | Include orders paid on/after this timestamp |
| `paid_before` | `YYYY-MM-DD` or ISO datetime | Include orders paid on/before this timestamp |
| `created_after` | `YYYY-MM-DD` or ISO datetime | Include orders created on/after this timestamp |
| `created_before` | `YYYY-MM-DD` or ISO datetime | Include orders created on/before this timestamp |
| `page_size` | `1` to `100` | Control page size |

Examples:

```http
GET /api/orders/?status=paid&ordering=-paid_at&page_size=100
```

```http
GET /api/orders/?status=paid&paid_after=2026-01-01&paid_before=2026-12-31
```

Date-only values are treated as full-day boundaries. For example, `paid_before=2026-12-31` includes orders through the end of that day.

Invalid `status`, `ordering`, or date values return `400 Bad Request`.

### Response

The endpoint uses the standard paginated DRF shape:

```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 42,
      "status": "paid",
      "total": "143.98",
      "item_count": 2,
      "created_at": "2026-06-23T09:55:00Z",
      "paid_at": "2026-06-23T10:00:00Z"
    }
  ]
}
```

Use this endpoint for order tables, receipt archive rows, and paginated history. Do not use it to compute lifetime totals or chart aggregates on the frontend.

---

## Spending Summary Endpoint

Use the dedicated summary endpoint for dashboard totals and charts:

```http
GET /api/account/spending-summary/?period=12m
```

### Query Parameters

| Param | Default | Purpose |
| :--- | :--- | :--- |
| `period` | `12m` | Limits chart-style aggregates. Use month periods like `6m`, `12m`, `24m`, or `all`. |

### Backend Rules

- Only `status=paid` orders count toward spend metrics.
- Pending and cancelled orders are counted separately, but never included in spend totals.
- Time-series data uses `paid_at`; if a paid order has no `paid_at`, it falls back to `created_at`.
- `discount_amount` is aggregated into `total_savings`.
- Results are strictly scoped to the authenticated user.
- Category charts use category snapshots stored on each order line at checkout time.

### Response Shape

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
    {
      "period": "2025-07",
      "total": "320.00",
      "order_count": 3
    }
  ],
  "spending_by_category": [
    {
      "category_id": 2,
      "category_name": "Apparel",
      "total": "450.00",
      "order_count": 4
    }
  ],
  "recent_paid_orders": [
    {
      "id": 42,
      "total": "143.98",
      "paid_at": "2026-06-23T10:00:00Z",
      "item_count": 2
    }
  ]
}
```

### Frontend Usage

Use this endpoint for:

- Account dashboard KPI cards.
- Monthly spending bar or line charts.
- Category spending charts.
- Recent paid order widgets.

Recommended React flow:

```ts
async function fetchSpendingSummary(accessToken: string, period = "12m") {
  const response = await fetch(`/api/account/spending-summary/?period=${period}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to load spending summary");
  }

  return response.json();
}
```

Amounts are serialized as strings to preserve decimal precision. Convert them to numbers only at chart-render time.

---

## Category Snapshot Behavior

Order line items now store:

```json
{
  "category_id": 2,
  "category_name": "Apparel"
}
```

These fields are captured at checkout. This keeps historical spending charts stable even if products are moved to another category later.

Existing order items are backfilled during migration from the current variant → product → category relation when possible. If an old order item no longer has a variant, it will not appear in category breakdowns.

---

## Receipt Integration

Receipt support remains available through the existing endpoints:

| Endpoint | Purpose |
| :--- | :--- |
| `GET /api/orders/{id}/receipt/` | Paid-order HTML receipt |
| `GET /api/orders/{id}/` | Full order JSON |
| `GET /api/orders/?status=paid&ordering=-paid_at` | Paginated receipt archive list |

The HTML receipt endpoint only works for paid orders. Pending or cancelled orders return `400 Bad Request`.

For a receipt archive page, use:

```http
GET /api/orders/?status=paid&ordering=-paid_at&page=1&page_size=20
```

Each result contains enough data for a slim archive row: `id`, `total`, `paid_at`, and `item_count`. The frontend can treat `receipt_available` as `true` for paid order rows.

---

## Recommended Integration Pattern

Use both endpoints together:

1. Load `/api/account/spending-summary/?period=12m` once for dashboard totals and charts.
2. Load `/api/orders/?status=paid&ordering=-paid_at&page_size=20` for receipt/order archive rows.
3. Fetch `/api/orders/{id}/receipt/` only when the user opens or prints a receipt.

This keeps dashboard charts fast for heavy shoppers and keeps paginated order browsing independent from aggregate reporting.
