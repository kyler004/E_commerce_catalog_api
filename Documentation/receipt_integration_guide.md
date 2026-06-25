# Order Receipt Frontend Integration Guide

This guide describes how to integrate the backend order receipt feature (`GET /api/orders/{id}/receipt/`) into your frontend application (e.g., React, Next.js, Vite).

---

## 1. Authentication Integration

Since the receipt endpoint is protected by the `OrderPermissionMixin` (requiring `IsAuthenticated` and `IsEmailVerified`), any client request must include the JWT authentication header:

```http
Authorization: Bearer <your_access_token>
```

Depending on your frontend setup, you have two primary options to fetch and display the receipt.

### Option A: Render via Iframe (Recommended)
This approach keeps the receipt isolated from your main application styles and uses browser-native printing commands cleanly.

1. Fetch the HTML receipt from the backend as text, passing the auth token.
2. Create a temporary blob URL or insert the content into a sandboxed iframe.

```javascript
import React, { useState, useEffect } from 'react';

const ReceiptViewer = ({ orderId, token }) => {
  const [htmlContent, setHtmlContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`/api/orders/${orderId}/receipt/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load receipt');
        return res.text();
      })
      .then((html) => {
        setHtmlContent(html);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [orderId, token]);

  if (loading) return <div>Loading receipt...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <iframe
      title={`Receipt for Order #${orderId}`}
      srcDoc={htmlContent}
      style={{
        width: '100%',
        height: '800px',
        border: '1px solid #ccc',
        borderRadius: '8px',
      }}
    />
  );
};

export default ReceiptViewer;
```

### Option B: Open in a New Window/Tab
If you want to open the receipt in a new tab where the user can print it directly, you can write the fetched HTML into a new window:

```javascript
const openReceiptInNewTab = async (orderId, token) => {
  try {
    const response = await fetch(`/api/orders/${orderId}/receipt/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      alert('Failed to load receipt. Make sure the order is paid.');
      return;
    }

    const html = await response.text();
    const newWindow = window.open('', '_blank');
    if (newWindow) {
      newWindow.document.write(html);
      newWindow.document.close();
    }
  } catch (error) {
    console.error('Error fetching receipt:', error);
  }
};
```

---

## 2. Receipt Styling Description

The receipt is built with a premium, high-contrast visual style utilizing the Google Font **Outfit** and CSS custom properties (variables) for theme consistency.

### HSL Color Palette (CSS Variables)

| Variable | Value | Description |
|---|---|---|
| `--primary` | `hsl(220, 85%, 57%)` | Electric blue used for the primary print button and headers |
| `--primary-hover` | `hsl(220, 85%, 47%)` | Darker blue shade for button hover states |
| `--text-main` | `hsl(224, 71%, 4%)` | Primary typography color (very dark blue/gray for legibility) |
| `--text-muted` | `hsl(220, 9%, 46%)` | Secondary/subtle text color |
| `--bg-main` | `hsl(210, 20%, 98%)` | Pale gray background used for screen display mode |
| `--bg-card` | `hsl(0, 0%, 100%)` | Pure white background for the receipt card |
| `--border-color` | `#e8ff00` | Bright neon yellow border accents |
| `--border-hover` | `hsl(220, 13%, 80%)` | Subtle borders for table grid lines |
| `--success` | `hsl(142, 72%, 29%)` | Forest green status text for the "Paid" badge |
| `--success-bg` | `hsl(143, 76%, 95%)` | Soft green background for the "Paid" badge |

### Structure & Layout Styles

- **Decorative Header Accent**: The container has a top decorative gradient bar moving from `--primary` (blue) to purple `hsl(262, 80%, 50%)` to give a premium brand feel.
- **Card Styling**: On screens, the receipt displays as a floating card with a subtle drop shadow (`box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05)`) and rounded corners (`border-radius: 16px`).
- **Typography hierarchy**:
  - Store logo/brand: `font-size: 1.8rem`, `font-weight: 700`.
  - Details grid: Clean two-column CSS grid displaying customer info next to shipping address.
  - Items Table: Structured with a table-collapse layout, clean headers, and alignment helpers (`item-qty` is centered, pricing is right-aligned).

---

## 3. Printing Experience (`@media print`)

The receipt template includes a dedicated `@media print` style block to guarantee the physical or PDF output remains pristine, professional, and free of clutter.

When a print operation is triggered (via `window.print()` or the built-in action button):

1. **Hidden Navigation/Controls**: The `.actions-bar` (which contains the "Close Window" and "Print Receipt" controls) is completely hidden (`display: none`).
2. **Hidden Accent Elements**: The neon top border gradient and the card boundary borders are hidden to save printer ink.
3. **Background/Contrast Adjustments**: The outer background wrapper is changed to white (`background-color: white`) and typography colors default to full black to ensure high-contrast readability on physical paper.
4. **Layout Reset**: Shadows and margins are stripped from `.receipt-container` so the receipt fills the print page boundaries perfectly without clipping.
