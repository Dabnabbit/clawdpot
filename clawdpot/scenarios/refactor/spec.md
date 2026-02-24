# Task: Refactor Inventory System

The file `inventory.py` in the current directory is a working inventory management system. It's functional but poorly structured — global mutable state, no proper types, duplicated validation, hardcoded configuration, and silent failures.

Refactor it into clean, well-structured Python code.

## Goals

1. **Eliminate global state.** The current code uses module-level mutable dicts and lists. After refactoring, it must be possible to create multiple independent instances with no shared state between them.

2. **Split into multiple modules.** The code should be organized across at least 3 Python files. Keep `inventory.py` as the public entry point.

3. **Use proper data types.** Products and orders should be proper objects (dataclasses or similar), not plain dicts. Products need: `id`, `name`, `price`, `stock`, `category`. Orders need: `id`, `items`, `subtotal`, `tax`, `total`, `status`.

4. **Fix error handling.** The current code silently returns `None` on errors. Refactored code should raise `ValueError` for validation problems (bad input) and `KeyError` for missing items (product/order not found). Keep returning `bool` from cancel/complete operations.

5. **Make tax configurable.** The 8% tax rate is hardcoded. It should be configurable per instance while keeping 0.08 as the default.

6. **Preserve all business logic.** Stock deduction on orders, stock restoration on cancellation, case-insensitive search, category filtering, low stock threshold (5 units), alphabetical sorting in list/search — all must work exactly as before.

## Public API

Create an `InventorySystem` class in `inventory.py`:

```python
from inventory import InventorySystem
inv = InventorySystem()            # default tax
inv = InventorySystem(tax_rate=0.1)  # custom tax
```

It must expose methods matching the original functions: `add_product`, `update_product`, `get_product`, `list_products`, `search_products`, `low_stock_report`, `create_order`, `cancel_order`, `complete_order`, `get_order`, `list_orders`, `sales_summary`.

Methods that returned dicts should now return proper Product/Order objects. Methods that returned None on bad input should now raise appropriate exceptions.

## Constraints

- Python 3.10+, stdlib only (dataclasses OK)
- `inventory.py` must remain — refactor, don't delete
- Order creation must be atomic: if any item validation fails, no stock is modified
