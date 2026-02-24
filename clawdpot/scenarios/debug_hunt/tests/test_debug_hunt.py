"""Judge tests for the debug_hunt scenario.

10 tests — 2 per bug. Each pair of tests exposes one specific bug.
Tests are the source of truth: the code must be fixed to pass these.
"""

import sys
from pathlib import Path

import pytest

# Add workdir to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))


# --- Bug 1: slugify doesn't strip leading/trailing hyphens ---

def test_slugify_basic():
    from utils import slugify
    assert slugify("Hello World") == "hello-world"


def test_slugify_strips_hyphens():
    from utils import slugify
    assert slugify("  --Hello World--  ") == "hello-world"


# --- Bug 2: truncate off-by-one (result too long by 1 char) ---

def test_truncate_short():
    from utils import truncate
    assert truncate("Hello", 10) == "Hello"


def test_truncate_exact_length():
    from utils import truncate
    # "Hello World" is 11 chars. With max_len=8, result should be "Hello..."
    result = truncate("Hello World", 8)
    assert result == "Hello..."
    assert len(result) == 8


# --- Bug 3: parse_csv_line drops last field ---

def test_csv_simple():
    from utils import parse_csv_line
    assert parse_csv_line("a,b,c") == ["a", "b", "c"]


def test_csv_quoted():
    from utils import parse_csv_line
    assert parse_csv_line('a,"b,c",d') == ["a", "b,c", "d"]


# --- Bug 4: get_pending sorts ascending instead of descending ---

def test_pending_sort_order():
    from app import TaskManager
    tm = TaskManager()
    tm.add_task("low", priority=1)
    tm.add_task("high", priority=10)
    tm.add_task("mid", priority=5)
    pending = tm.get_pending()
    priorities = [t["priority"] for t in pending]
    assert priorities == [10, 5, 1], f"Expected descending order, got {priorities}"


def test_pending_excludes_completed():
    from app import TaskManager
    tm = TaskManager()
    t1 = tm.add_task("one")
    t2 = tm.add_task("two")
    tm.complete_task(t1["id"])
    pending = tm.get_pending()
    assert len(pending) == 1
    assert pending[0]["title"] == "two"


# --- Bug 5: search is case-sensitive ---

def test_search_case_insensitive():
    from app import TaskManager
    tm = TaskManager()
    tm.add_task("Buy Groceries")
    tm.add_task("buy stamps")
    results = tm.search("buy")
    assert len(results) == 2, f"Expected 2 results for 'buy', got {len(results)}"


def test_search_no_match():
    from app import TaskManager
    tm = TaskManager()
    tm.add_task("Buy Groceries")
    results = tm.search("xyz")
    assert len(results) == 0
