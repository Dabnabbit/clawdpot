"""Judge tests for the refactor scenario.

20 tests: 12 behavioral (including tricky edge cases) + 8 structural.

The edge cases here are designed to catch models that mechanically translate
the original code without thinking about correctness:
- Atomicity of order creation (no partial stock deduction on failure)
- State transitions (can't complete a cancelled order or cancel a completed one)
- Boundary conditions (zero price, exact stock depletion)
- Category normalization consistency across operations
"""

import sys
from pathlib import Path

import pytest

# Add workdir to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

WORKDIR = Path(__file__).parent.parent


def make_inv(**kwargs):
    from inventory import InventorySystem
    return InventorySystem(**kwargs)


# ===========================================================================
# Behavioral tests (12) — functionality + edge cases
# ===========================================================================

def test_add_and_retrieve_product():
    """Add a product, retrieve by ID, verify all fields."""
    inv = make_inv()
    p = inv.add_product("Widget", 9.99, 100, "electronics")
    fetched = inv.get_product(p.id)
    assert fetched.name == "Widget"
    assert fetched.price == 9.99
    assert fetched.stock == 100
    assert fetched.category == "electronics"


def test_update_preserves_unchanged_fields():
    """Updating one field must not clobber others."""
    inv = make_inv()
    p = inv.add_product("Widget", 9.99, 100, "electronics")
    updated = inv.update_product(p.id, price=12.50)
    assert updated.price == 12.50
    assert updated.name == "Widget"
    assert updated.stock == 100
    assert updated.category == "electronics"


def test_category_normalization():
    """Categories are normalized: ' Hardware ' stored as 'hardware',
    and filtering by 'HARDWARE' finds them."""
    inv = make_inv()
    inv.add_product("Bolt", 0.50, 100, " Hardware ")
    inv.add_product("Nut", 0.25, 200, "hardware")
    inv.add_product("Paint", 15.0, 50, "SUPPLIES")

    hw = inv.list_products(category="HARDWARE")
    assert len(hw) == 2
    assert all(p.category == "hardware" for p in hw)


def test_search_sorted_and_case_insensitive():
    """Search returns case-insensitive matches sorted by name."""
    inv = make_inv()
    inv.add_product("Red widget", 14.99, 5)
    inv.add_product("Blue Widget", 9.99, 10)
    inv.add_product("Bolt", 0.50, 100)

    results = inv.search_products("WIDGET")
    assert len(results) == 2
    # Alphabetical: Blue before Red
    assert results[0].name == "Blue Widget"
    assert results[1].name == "Red widget"


def test_low_stock_report():
    """Low stock report returns products with stock < 5."""
    inv = make_inv()
    inv.add_product("Abundant", 1.0, 100)
    inv.add_product("Scarce", 2.0, 3)
    inv.add_product("Borderline", 3.0, 5)  # exactly 5 = NOT low stock
    inv.add_product("Empty", 4.0, 0)

    low = inv.low_stock_report()
    names = {p.name for p in low}
    assert "Scarce" in names
    assert "Empty" in names
    assert "Abundant" not in names
    assert "Borderline" not in names  # 5 is NOT < 5


def test_order_with_tax():
    """Order calculates subtotal, tax (8% default), and total correctly."""
    inv = make_inv()
    p1 = inv.add_product("A", 50.0, 10)
    p2 = inv.add_product("B", 30.0, 10)
    order = inv.create_order([(p1.id, 2), (p2.id, 1)])

    assert order.subtotal == 130.0       # 50*2 + 30*1
    assert order.tax == 10.4             # 130 * 0.08
    assert order.total == 140.4          # 130 + 10.4
    assert order.status == "pending"


def test_cancel_restores_stock():
    """Cancelling an order restores all product stock."""
    inv = make_inv()
    p = inv.add_product("Widget", 10.0, 20)
    order = inv.create_order([(p.id, 7)])
    assert inv.get_product(p.id).stock == 13

    inv.cancel_order(order.id)
    assert inv.get_product(p.id).stock == 20


def test_sales_summary_completed_only():
    """Sales summary only counts completed orders."""
    inv = make_inv()
    p = inv.add_product("Widget", 10.0, 100)

    o1 = inv.create_order([(p.id, 2)])  # will complete
    o2 = inv.create_order([(p.id, 3)])  # stays pending
    o3 = inv.create_order([(p.id, 1)])  # will cancel
    inv.complete_order(o1.id)
    inv.cancel_order(o3.id)

    summary = inv.sales_summary()
    assert summary["total_orders"] == 1
    assert summary["total_items"] == 2
    # 2 * 10.0 = 20.0 + 8% tax = 21.60
    assert summary["total_revenue"] == 21.6


# --- Tricky edge cases ---

def test_order_exact_stock_depletion():
    """Ordering exactly all remaining stock should succeed (stock → 0)."""
    inv = make_inv()
    p = inv.add_product("LastOne", 5.0, 3)
    order = inv.create_order([(p.id, 3)])

    assert order is not None
    assert inv.get_product(p.id).stock == 0


def test_order_atomic_on_failure():
    """If order creation fails (insufficient stock), NO stock is modified.

    This tests atomicity: with two items where the second lacks stock,
    the first item's stock must remain unchanged.
    """
    inv = make_inv()
    p1 = inv.add_product("Plenty", 10.0, 100)
    p2 = inv.add_product("Scarce", 20.0, 2)

    with pytest.raises((ValueError, KeyError)):
        inv.create_order([(p1.id, 5), (p2.id, 10)])  # p2 only has 2

    # p1 stock must be untouched — order was atomic
    assert inv.get_product(p1.id).stock == 100


def test_order_state_transitions():
    """Can't complete a cancelled order or cancel a completed order."""
    inv = make_inv()
    p = inv.add_product("Widget", 10.0, 50)

    o1 = inv.create_order([(p.id, 1)])
    inv.complete_order(o1.id)
    assert inv.cancel_order(o1.id) is False   # can't cancel completed

    o2 = inv.create_order([(p.id, 1)])
    inv.cancel_order(o2.id)
    assert inv.complete_order(o2.id) is False  # can't complete cancelled


# ===========================================================================
# Structural tests (8) — clean architecture
# ===========================================================================

def test_struct_multi_module():
    """At least 3 .py files exist."""
    py_files = [
        f for f in WORKDIR.glob("*.py")
        if not f.name.startswith("test_") and f.name != "__init__.py"
    ]
    assert len(py_files) >= 3, (
        f"Expected >= 3 .py files, found {len(py_files)}: "
        f"{sorted(f.name for f in py_files)}"
    )


def test_struct_product_is_object():
    """Products are proper objects with attributes, not dicts."""
    inv = make_inv()
    p = inv.add_product("Test", 5.0, 10)
    # Must have real attributes, not dict access
    assert hasattr(p, "name") and hasattr(p, "price") and hasattr(p, "stock")
    assert not isinstance(p, dict), "Product should be a proper object, not a dict"


def test_struct_order_is_object():
    """Orders are proper objects with attributes, not dicts."""
    inv = make_inv()
    p = inv.add_product("Test", 5.0, 10)
    order = inv.create_order([(p.id, 1)])
    assert hasattr(order, "total") and hasattr(order, "status")
    assert not isinstance(order, dict), "Order should be a proper object, not a dict"


def test_struct_independent_instances():
    """Two InventorySystem instances do not share state."""
    inv1 = make_inv()
    inv2 = make_inv()

    inv1.add_product("Widget", 10.0, 5)
    assert len(inv1.list_products()) == 1
    assert len(inv2.list_products()) == 0, (
        "Instances share state — global mutable data still present"
    )


def test_struct_validation_raises():
    """Bad input raises ValueError."""
    inv = make_inv()
    with pytest.raises(ValueError):
        inv.add_product("", 10.0, 5)
    with pytest.raises(ValueError):
        inv.add_product("Widget", -1.0, 5)
    with pytest.raises(ValueError):
        inv.add_product("Widget", 10.0, -1)


def test_struct_not_found_raises():
    """Missing product/order raises KeyError."""
    inv = make_inv()
    with pytest.raises(KeyError):
        inv.get_product(99999)
    with pytest.raises(KeyError):
        inv.get_order(99999)


def test_struct_tax_configurable():
    """Custom tax_rate changes order totals."""
    inv_lo = make_inv(tax_rate=0.0)
    inv_hi = make_inv(tax_rate=0.25)

    p1 = inv_lo.add_product("X", 100.0, 10)
    p2 = inv_hi.add_product("X", 100.0, 10)

    o1 = inv_lo.create_order([(p1.id, 1)])
    o2 = inv_hi.create_order([(p2.id, 1)])

    assert o1.tax == 0.0
    assert o1.total == 100.0
    assert o2.tax == 25.0
    assert o2.total == 125.0


def test_struct_zero_price_product():
    """Free products (price=0) are valid — not a validation error."""
    inv = make_inv()
    p = inv.add_product("Freebie", 0.0, 10)
    assert p.price == 0.0
    order = inv.create_order([(p.id, 1)])
    assert order.total == 0.0


def test_order_multi_item_stock_tracking():
    """Order with multiple different products tracks stock correctly for each."""
    inv = make_inv()
    p1 = inv.add_product("A", 10.0, 20)
    p2 = inv.add_product("B", 20.0, 15)
    p3 = inv.add_product("C", 30.0, 8)

    order = inv.create_order([(p1.id, 5), (p2.id, 3), (p3.id, 2)])

    assert inv.get_product(p1.id).stock == 15
    assert inv.get_product(p2.id).stock == 12
    assert inv.get_product(p3.id).stock == 6
    assert order.subtotal == 5 * 10.0 + 3 * 20.0 + 2 * 30.0  # 170.0
