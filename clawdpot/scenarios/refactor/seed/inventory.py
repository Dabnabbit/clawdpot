"""Inventory management system.

Works correctly but is poorly structured:
- All logic in one file
- Global mutable state (module-level dicts/lists)
- Duplicated validation
- Dict-based data (no proper types)
- Hardcoded tax rate
- Returns None on errors instead of raising
"""

# --- Global state ---
_products = {}  # id -> {name, price, stock, category}
_orders = []    # list of order dicts
_next_product_id = [1]   # mutable list so closures can modify
_next_order_id = [1]

TAX_RATE = 0.08
LOW_STOCK_THRESHOLD = 5
MAX_ORDER_ITEMS = 50


def add_product(name, price, stock, category="general"):
    """Add a product to inventory. Returns product dict or None on bad input."""
    if not name or not name.strip():
        return None
    if price < 0:
        return None
    if stock < 0:
        return None

    pid = _next_product_id[0]
    _next_product_id[0] += 1
    _products[pid] = {
        "id": pid,
        "name": name.strip(),
        "price": float(price),
        "stock": int(stock),
        "category": category.lower().strip(),
    }
    return _products[pid].copy()


def update_product(pid, name=None, price=None, stock=None):
    """Update product fields. Returns updated product dict or None."""
    if pid not in _products:
        return None

    p = _products[pid]
    if name is not None:
        # Duplicated validation from add_product
        if not name or not name.strip():
            return None
        p["name"] = name.strip()
    if price is not None:
        if price < 0:
            return None
        p["price"] = float(price)
    if stock is not None:
        if stock < 0:
            return None
        p["stock"] = int(stock)
    return p.copy()


def get_product(pid):
    """Get product by ID. Returns dict or None."""
    if pid in _products:
        return _products[pid].copy()
    return None


def list_products(category=None, in_stock_only=False):
    """List products with optional filters."""
    results = []
    for p in _products.values():
        if category and p["category"] != category.lower().strip():
            continue
        if in_stock_only and p["stock"] <= 0:
            continue
        results.append(p.copy())
    results.sort(key=lambda x: x["name"].lower())
    return results


def search_products(query):
    """Search products by name (case-insensitive)."""
    query = query.lower().strip()
    if not query:
        return []
    results = []
    for p in _products.values():
        if query in p["name"].lower():
            results.append(p.copy())
    results.sort(key=lambda x: x["name"].lower())
    return results


def low_stock_report():
    """Return products with stock below threshold."""
    return [
        p.copy() for p in _products.values()
        if p["stock"] < LOW_STOCK_THRESHOLD
    ]


def create_order(items):
    """Create an order from a list of (product_id, quantity) tuples.

    Returns order dict or None on failure.
    """
    if not items or len(items) > MAX_ORDER_ITEMS:
        return None

    order_items = []
    total = 0.0

    for pid, qty in items:
        if pid not in _products:
            return None
        if qty <= 0:
            return None
        p = _products[pid]
        if p["stock"] < qty:
            return None
        order_items.append({
            "product_id": pid,
            "product_name": p["name"],
            "quantity": qty,
            "unit_price": p["price"],
            "subtotal": p["price"] * qty,
        })
        total += p["price"] * qty

    # Deduct stock
    for pid, qty in items:
        _products[pid]["stock"] -= qty

    tax = total * TAX_RATE

    oid = _next_order_id[0]
    _next_order_id[0] += 1
    order = {
        "id": oid,
        "items": order_items,
        "subtotal": round(total, 2),
        "tax": round(tax, 2),
        "total": round(total + tax, 2),
        "status": "pending",
    }
    _orders.append(order)
    return order.copy()


def cancel_order(oid):
    """Cancel an order and restore stock. Returns True/False."""
    for order in _orders:
        if order["id"] == oid:
            if order["status"] == "cancelled":
                return False
            for item in order["items"]:
                if item["product_id"] in _products:
                    _products[item["product_id"]]["stock"] += item["quantity"]
            order["status"] = "cancelled"
            return True
    return False


def complete_order(oid):
    """Mark an order as completed. Returns True/False."""
    for order in _orders:
        if order["id"] == oid:
            if order["status"] != "pending":
                return False
            order["status"] = "completed"
            return True
    return False


def get_order(oid):
    """Get order by ID. Returns dict or None."""
    for order in _orders:
        if order["id"] == oid:
            return order.copy()
    return None


def list_orders(status=None):
    """List orders, optionally filtered by status."""
    results = []
    for order in _orders:
        if status and order["status"] != status:
            continue
        results.append(order.copy())
    return results


def sales_summary():
    """Calculate total sales from completed orders."""
    total_revenue = 0.0
    total_orders = 0
    total_items = 0

    for order in _orders:
        if order["status"] == "completed":
            total_revenue += order["total"]
            total_orders += 1
            for item in order["items"]:
                total_items += item["quantity"]

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "total_items": total_items,
    }


def reset():
    """Reset all state — used for testing."""
    _products.clear()
    _orders.clear()
    _next_product_id[0] = 1
    _next_order_id[0] = 1
